const nodemailer = require('nodemailer');

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseBool(value, defaultValue = false) {
  if (value === undefined || value === null) {
    return defaultValue;
  }
  if (typeof value === 'boolean') {
    return value;
  }
  return String(value).trim().toLowerCase() === 'true' || String(value).trim() === '1' || String(value).trim().toLowerCase() === 'yes' || String(value).trim().toLowerCase() === 'on';
}

function isTransientSmtpError(err) {
  if (!err) {
    return false;
  }

  const code = String(err.code || err.errno || '').toUpperCase();
  if (['ETIMEDOUT', 'ESOCKET', 'ECONNRESET', 'EPIPE', 'EHOSTUNREACH', 'ENOTFOUND', 'ECONNREFUSED'].includes(code)) {
    return true;
  }

  const message = String(err.message || '').toLowerCase();
  return message.includes('timeout') || message.includes('temporar') || message.includes('try again') || message.includes('greylist');
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', (err) => reject(err));
  });
}

async function main() {
  try {
    const raw = await readStdin();
    if (!raw || !raw.trim()) {
      throw new Error('No input payload provided to email_sender.js');
    }

    const payload = JSON.parse(raw);
    const transport = payload.transport || {};
    const message = payload.message || {};

    const host = String(transport.host || '').trim();
    const port = Number(transport.port || 587);
    const user = String(transport.user || '').trim();
    const password = String(transport.password || '');
    const fromAddr = String(transport.from || '').trim();
    const allowInsecure = parseBool(transport.allowInsecure, false);
    const useAuth = parseBool(transport.useAuth, true);

    if (!host) {
      throw new Error('NODEMAILER_HOST is required');
    }
    if (!fromAddr) {
      throw new Error('EMAIL_FROM is required');
    }
    if (useAuth && !user) {
      throw new Error('NODEMAILER_USER is required when NODEMAILER_USE_AUTH=true');
    }
    if (useAuth && !password) {
      throw new Error('NODEMAILER_PASS is required when NODEMAILER_USE_AUTH=true');
    }

    const transporter = nodemailer.createTransport({
      host,
      port,
      secure: port === 465,
      auth: useAuth ? { user, pass: password } : undefined,
      tls: {
        rejectUnauthorized: !allowInsecure,
      },
    });

    await transporter.verify();

    const to = String(message.to || '').trim();
    const subject = String(message.subject || '');
    const html = message.html ? String(message.html) : undefined;
    const text = message.text ? String(message.text) : undefined;

    if (!to) {
      throw new Error('Recipient address is required');
    }

    let info = null;
    const maxAttempts = 3;

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        info = await transporter.sendMail({
          from: `SkillForge <${fromAddr}>`,
          to,
          subject,
          text,
          html,
        });
        break;
      } catch (err) {
        if (attempt >= maxAttempts || !isTransientSmtpError(err)) {
          throw err;
        }
        await delay(1000 * attempt);
      }
    }

    process.stdout.write(JSON.stringify({
      ok: true,
      messageId: info.messageId || '',
      response: info.response || '',
    }));
  } catch (err) {
    process.stdout.write(JSON.stringify({
      ok: false,
      error: err && err.message ? err.message : String(err),
    }));
    process.exit(1);
  }
}

main();
