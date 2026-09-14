const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const pool = require('./db');
const { sendOtpEmail, sendAccountCreatedEmail, sendLoginAlertEmail } = require('./mailer');

const router = express.Router();

const OTP_TTL_MINUTES = 5;
const OTP_MAX_ATTEMPTS = 5;
const JWT_SECRET = process.env.JWT_SECRET || 'dev-only-change-me';

// ---------- helpers ----------

function generateOtp() {
  return String(Math.floor(100000 + Math.random() * 900000)); // 6 digits
}

function hashOtp(code) {
  return crypto.createHash('sha256').update(code).digest('hex');
}

async function sendOtp(email, code, purpose) {
  // Prints to the terminal too, so you always have a fallback while testing.
  console.log(`\n[OTP] purpose=${purpose}  email=${email}  code=${code}  (valid ${OTP_TTL_MINUTES} min)\n`);
  try {
    await sendOtpEmail(email, code, purpose);
  } catch (err) {
    console.error('Failed to send OTP email — check your SMTP settings in .env:', err.message);
  }
}

async function logAudit(userId, eventType, description, ip) {
  await pool.query(
    `INSERT INTO audit_logs (user_id, event_type, description, ip_address) VALUES ($1, $2, $3, $4)`,
    [userId, eventType, description, ip]
  );
}

async function issueOtp(userId, email, purpose) {
  const code = generateOtp();
  await pool.query(
    `INSERT INTO otp_codes (user_id, purpose, code_hash, expires_at)
     VALUES ($1, $2, $3, now() + interval '${OTP_TTL_MINUTES} minutes')`,
    [userId, purpose, hashOtp(code)]
  );
  await sendOtp(email, code, purpose);
}

// ============================================================
// GET /api/ministries — populates the signup dropdown
// ============================================================
router.get('/ministries', async (req, res) => {
  try {
    const result = await pool.query('SELECT id, name FROM departments ORDER BY name');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not load ministries.' });
  }
});

// ============================================================
// POST /api/auth/register
// ============================================================
router.post('/auth/register', async (req, res) => {
  const { fullName, email, ministryId, designation, password, termsAccepted, aiAckAccepted } = req.body;

  if (!fullName || !email || !password || password.length < 8) {
    return res.status(400).json({ error: 'Missing or invalid required fields.' });
  }
  if (!termsAccepted || !aiAckAccepted) {
    return res.status(400).json({ error: 'You must accept the Terms and the AI-processing acknowledgement.' });
  }

  const client = await pool.connect();
  try {
    const existing = await client.query('SELECT id, is_verified FROM users WHERE LOWER(email) = LOWER($1)', [email]);

    if (existing.rows.length > 0) {
      const existingUser = existing.rows[0];
      if (existingUser.is_verified) {
        return res.status(409).json({ error: 'An account with this email already exists. Please sign in instead.' });
      }
      // Email is registered but never verified (e.g. they closed the tab before entering
      // the OTP) — just resend a fresh code instead of blocking them.
      await issueOtp(existingUser.id, email, 'signup');
      await logAudit(existingUser.id, 'signup_otp_resent', 'Re-registration attempt for unverified account, new OTP sent', req.ip);
      return res.json({ message: 'This email is already registered but not yet verified. A new code has been sent.' });
    }

    const passwordHash = await bcrypt.hash(password, 12);

    await client.query('BEGIN');

    const userResult = await client.query(
      `INSERT INTO users (full_name, email, password_hash, department_id, designation)
       VALUES ($1, $2, $3, $4, $5) RETURNING id`,
      [fullName, email, passwordHash, ministryId || null, designation]
    );
    const userId = userResult.rows[0].id;

    await client.query(
      `INSERT INTO user_consents (user_id, terms_accepted, terms_accepted_at, ai_ack_accepted, ai_ack_accepted_at)
       VALUES ($1, TRUE, now(), TRUE, now())`,
      [userId]
    );

    await client.query('COMMIT');

    await issueOtp(userId, email, 'signup');
    await logAudit(userId, 'signup', 'Account created, awaiting OTP verification', req.ip);

    res.json({ message: 'Account created. Check your email for the verification code.' });
  } catch (err) {
    await client.query('ROLLBACK');
    console.error(err);
    res.status(500).json({ error: 'Something went wrong creating your account.' });
  } finally {
    client.release();
  }
});

// ============================================================
// POST /api/auth/login — password-only, no OTP. Issues a token
// and sends a login-alert email.
// ============================================================
router.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ error: 'Email and password are required.' });

  const result = await pool.query('SELECT * FROM users WHERE LOWER(email) = LOWER($1)', [email]);
  const user = result.rows[0];

  if (!user) {
    await logAudit(null, 'login_failed', `No account for ${email}`, req.ip);
    return res.status(401).json({ error: 'Invalid email or password.' });
  }
  if (user.locked_until && new Date(user.locked_until) > new Date()) {
    return res.status(423).json({ error: 'Account temporarily locked. Try again later.' });
  }
  if (!user.is_active) {
    return res.status(403).json({ error: 'This account has been suspended.' });
  }

  const passwordOk = await bcrypt.compare(password, user.password_hash);
  if (!passwordOk) {
    const failedLogins = user.failed_logins + 1;
    const lock = failedLogins >= 5;
    await pool.query(
      `UPDATE users SET failed_logins = $1, locked_until = ${lock ? "now() + interval '15 minutes'" : 'NULL'} WHERE id = $2`,
      [failedLogins, user.id]
    );
    await logAudit(user.id, 'login_failed', 'Incorrect password', req.ip);
    return res.status(401).json({ error: 'Invalid email or password.' });
  }
  if (!user.is_verified) {
    return res.status(403).json({ error: 'Please verify your account via the signup OTP first.' });
  }

  await pool.query('UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = $1', [user.id]);

  const token = jwt.sign({ userId: user.id, email: user.email }, JWT_SECRET, { expiresIn: '12h' });
  await logAudit(user.id, 'login_success', 'Password verified, token issued', req.ip);

  const loginTime = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  sendLoginAlertEmail(user.email, { time: loginTime, ip: req.ip }).catch(err =>
    console.error('Failed to send login-alert email:', err.message)
  );

  res.json({ message: 'Signed in successfully.', token });
});

// ============================================================
// POST /api/auth/resend-otp — { email } — signup verification only
// ============================================================
router.post('/auth/resend-otp', async (req, res) => {
  const { email } = req.body;
  if (!email) return res.status(400).json({ error: 'Missing email.' });

  const result = await pool.query('SELECT id, email, is_verified FROM users WHERE LOWER(email) = LOWER($1)', [email]);
  const user = result.rows[0];
  if (!user) return res.status(404).json({ error: 'No account found for that email.' });
  if (user.is_verified) return res.status(400).json({ error: 'This account is already verified.' });

  await issueOtp(user.id, user.email, 'signup');
  await logAudit(user.id, 'otp_resent', 'Resent signup OTP', req.ip);

  res.json({ message: 'A new code has been sent.' });
});

// ============================================================
// POST /api/auth/verify-otp — { email, otp } — signup verification only
// ============================================================
router.post('/auth/verify-otp', async (req, res) => {
  const { email, otp } = req.body;
  if (!email || !otp) return res.status(400).json({ error: 'Missing email or code.' });

  const userResult = await pool.query('SELECT * FROM users WHERE LOWER(email) = LOWER($1)', [email]);
  const user = userResult.rows[0];
  if (!user) return res.status(404).json({ error: 'No account found for that email.' });

  const otpResult = await pool.query(
    `SELECT * FROM otp_codes WHERE user_id = $1 AND purpose = 'signup' AND consumed = FALSE ORDER BY created_at DESC LIMIT 1`,
    [user.id]
  );
  const record = otpResult.rows[0];

  if (!record) return res.status(400).json({ error: 'No pending code. Request a new one.' });
  if (new Date(record.expires_at) < new Date()) return res.status(400).json({ error: 'Code expired. Request a new one.' });
  if (record.attempts >= OTP_MAX_ATTEMPTS) return res.status(400).json({ error: 'Too many attempts. Request a new code.' });

  if (hashOtp(otp) !== record.code_hash) {
    await pool.query('UPDATE otp_codes SET attempts = attempts + 1 WHERE id = $1', [record.id]);
    return res.status(400).json({ error: 'Incorrect code.' });
  }

  await pool.query('UPDATE otp_codes SET consumed = TRUE WHERE id = $1', [record.id]);
  await pool.query('UPDATE users SET is_verified = TRUE WHERE id = $1', [user.id]);
  await logAudit(user.id, 'signup_verified', 'Signup OTP verified, account activated', req.ip);

  sendAccountCreatedEmail(user.email, user.full_name).catch(err =>
    console.error('Failed to send account-created email:', err.message)
  );

  res.json({ message: 'Account verified. You can now sign in.' });
});

module.exports = router;
