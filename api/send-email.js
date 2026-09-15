import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: 465,
  secure: true,
  auth: {
    user: process.env.SMTP_USER || 'syntaxtrrors@gmail.com',
    pass: process.env.SMTP_PASS || 'szbfukaiioisvnly',
  },
});

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { type, to, code, purpose, fullName, time, ip } = req.body || {};

  if (!to) {
    return res.status(400).json({ error: 'Recipient email "to" is required.' });
  }

  try {
    if (type === 'otp') {
      const purposeText = purpose === 'signup' ? 'verify your new PAIMANA account' : 'sign in to PAIMANA';
      const info = await transporter.sendMail({
        from: '"PAIMANA Sovereign Platform" <syntaxtrrors@gmail.com>',
        to,
        subject: `Your PAIMANA verification code: ${code}`,
        text: `Your verification code is ${code}. Use it to ${purposeText}. It expires in 5 minutes.`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 440px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
              <span style="font-size: 18px; font-weight: bold; letter-spacing: 1px; color: #0f172a;">PAIMANA</span>
              <span style="font-size: 11px; background: #e0f2fe; color: #0284c7; padding: 2px 8px; border-radius: 999px; font-weight: 600;">OFFICIAL AUTH</span>
            </div>
            <h2 style="color: #0f172a; margin-top: 0;">Verification Code</h2>
            <p style="color: #475569; font-size: 14px;">Use this 6-digit code to ${purposeText}. It expires in 5 minutes.</p>
            <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; text-align: center; padding: 16px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; color: #0284c7; font-family: monospace;">
              ${code}
            </div>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 20px;">If you did not request this verification code, you can safely ignore this email.</p>
          </div>
        `
      });
      return res.status(200).json({ success: true, messageId: info.messageId });
    } else if (type === 'welcome') {
      const info = await transporter.sendMail({
        from: '"PAIMANA Sovereign Platform" <syntaxtrrors@gmail.com>',
        to,
        subject: 'Your PAIMANA account is ready',
        text: `Hi ${fullName || 'Officer'}, your PAIMANA account has been verified successfully. You can now sign in.`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 440px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #0f172a; margin-top: 0;">Welcome to PAIMANA</h2>
            <p style="color: #475569; font-size: 14px;">Hi <strong>${fullName || 'Officer'}</strong>, your account has been verified and provisioned with authorized analytical access.</p>
            <div style="margin: 20px 0; padding: 14px; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px; font-size: 13px; color: #166534;">
              ✓ Identity Verified · Institutional Early-Warning Access Activated
            </div>
            <p style="color: #94a3b8; font-size: 12px;">PAIMANA National Infrastructure Decision-Support Platform</p>
          </div>
        `
      });
      return res.status(200).json({ success: true, messageId: info.messageId });
    } else if (type === 'login_alert') {
      const timeStr = time || new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
      const info = await transporter.sendMail({
        from: '"PAIMANA Sovereign Platform" <syntaxtrrors@gmail.com>',
        to,
        subject: 'Security Notice: New sign-in to PAIMANA',
        text: `Your PAIMANA account was signed in to at ${timeStr}${ip ? ` from IP ${ip}` : ''}.`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 440px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h3 style="margin-top: 0; color: #0f172a;">New Sign-In Detected</h3>
            <p style="color: #475569; font-size: 13.5px;">Your PAIMANA account was just accessed with valid credentials.</p>
            <table style="font-size: 13px; color: #1e293b; margin: 14px 0;">
              <tr><td style="padding: 3px 14px 3px 0; color: #64748b;">Timestamp:</td><td><strong>${timeStr}</strong></td></tr>
              ${ip ? `<tr><td style="padding: 3px 14px 3px 0; color: #64748b;">Origin IP:</td><td><strong>${ip}</strong></td></tr>` : ''}
            </table>
            <p style="color: #94a3b8; font-size: 11.5px;">If this was not you, please rotate your password immediately.</p>
          </div>
        `
      });
      return res.status(200).json({ success: true, messageId: info.messageId });
    } else {
      return res.status(400).json({ error: `Unknown email type: ${type}` });
    }
  } catch (err) {
    console.error('Failed to deliver email via SMTP:', err);
    return res.status(500).json({ error: 'Failed to deliver email', details: err.message });
  }
}
