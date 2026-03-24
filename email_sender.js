const nodemailer = require('nodemailer');

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
    const allowInsecure = Boolean(transport.allowInsecure);
    const useAuth = Boolean(transport.useAuth);

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

    const to = String(message.to || '').trim();
    const subject = String(message.subject || '');
    const html = message.html ? String(message.html) : undefined;
    const text = message.text ? String(message.text) : undefined;

    if (!to) {
      throw new Error('Recipient address is required');
    }

    const info = await transporter.sendMail({
      from: `SkillForge <${fromAddr}>`,
      to,
      subject,
      text,
      html,
    });

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
