const nodemailer = require('nodemailer');

// Works with Gmail out of the box (see .env.example for setup notes).
// Swap the transport config below if you use a different provider.
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: Number(process.env.SMTP_PORT) || 587,
  secure: false, // true for port 465, false for 587
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

async function sendOtpEmail(toEmail, code, purpose) {
  const purposeText = purpose === 'signup' ? 'verify your new PAIMANA account' : 'sign in to PAIMANA';

  await transporter.sendMail({
    from: `"PAIMANA" <${process.env.SMTP_USER}>`,
    to: toEmail,
    subject: `Your PAIMANA verification code: ${code}`,
    text: `Your verification code is ${code}. Use it to ${purposeText}. It expires in 5 minutes. If you didn't request this, you can ignore this email.`,
    html: `
      <div style="font-family: sans-serif; max-width: 420px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="margin: 0 0 8px 0; color: #101827;">PAIMANA verification code</h2>
        <p style="color: #5c6b80; font-size: 14px;">Use this code to ${purposeText}. It expires in 5 minutes.</p>
        <div style="font-size: 32px; font-weight: 700; letter-spacing: 6px; text-align: center; padding: 16px; background: #f1f4f9; border-radius: 6px; margin: 16px 0;">
          ${code}
        </div>
        <p style="color: #8b98ac; font-size: 12px;">If you didn't request this code, you can safely ignore this email.</p>
      </div>
    `,
  });
}

async function sendAccountCreatedEmail(toEmail, fullName) {
  await transporter.sendMail({
    from: `"PAIMANA" <${process.env.SMTP_USER}>`,
    to: toEmail,
    subject: 'Your PAIMANA account is ready',
    text: `Hi ${fullName}, your PAIMANA account has been created and verified successfully. You can now sign in.`,
    html: `
      <div style="font-family: sans-serif; max-width: 420px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="margin: 0 0 8px 0; color: #101827;">Welcome to PAIMANA</h2>
        <p style="color: #5c6b80; font-size: 14px;">Hi ${fullName}, your account has been created and verified successfully. You can now sign in with your email and password.</p>
        <p style="color: #8b98ac; font-size: 12px;">If you didn't create this account, please contact your administrator.</p>
      </div>
    `,
  });
}

async function sendLoginAlertEmail(toEmail, { time, ip }) {
  await transporter.sendMail({
    from: `"PAIMANA" <${process.env.SMTP_USER}>`,
    to: toEmail,
    subject: 'New sign-in to your PAIMANA account',
    text: `Your PAIMANA account was just signed in to at ${time}${ip ? ` from IP ${ip}` : ''}. If this wasn't you, contact your administrator immediately.`,
    html: `
      <div style="font-family: sans-serif; max-width: 420px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="margin: 0 0 8px 0; color: #101827;">New sign-in detected</h2>
        <p style="color: #5c6b80; font-size: 14px;">Your PAIMANA account was just signed in to.</p>
        <table style="font-size: 13px; color: #101827; margin: 12px 0;">
          <tr><td style="padding: 2px 12px 2px 0; color: #8b98ac;">Time</td><td>${time}</td></tr>
          ${ip ? `<tr><td style="padding: 2px 12px 2px 0; color: #8b98ac;">IP address</td><td>${ip}</td></tr>` : ''}
        </table>
        <p style="color: #8b98ac; font-size: 12px;">If this wasn't you, contact your administrator immediately and change your password.</p>
      </div>
    `,
  });
}

module.exports = { sendOtpEmail, sendAccountCreatedEmail, sendLoginAlertEmail };
