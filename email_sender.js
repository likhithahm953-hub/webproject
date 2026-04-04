const nodemailer = require('nodemailer');
const dns = require('dns').promises;

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

async function resolveIPv4(hostname) {
  try {
    const lookup = await dns.lookup(hostname, { family: 4 });
    return lookup && lookup.address ? String(lookup.address).trim() : '';
  } catch (_err) {
    return '';
  }
}

function uniqueConnectionPlans(primaryPort) {
  const plans = [];
  const add = (port, ipv4Only) => {
    if (!Number.isFinite(port) || port <= 0) {
      return;
    }
    if (!plans.some((p) => p.port === port && p.ipv4Only === ipv4Only)) {
      plans.push({ port, ipv4Only });
    }
  };

  const normalizedPrimary = Number(primaryPort || 587);
  add(normalizedPrimary, false);
  add(normalizedPrimary, true);

  const alternate = normalizedPrimary === 465 ? 587 : 465;
  add(alternate, false);
  add(alternate, true);

  return plans;
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

    const to = String(message.to || '').trim();
    const subject = String(message.subject || '');
    const html = message.html ? String(message.html) : undefined;
    const text = message.text ? String(message.text) : undefined;

    if (!to) {
      throw new Error('Recipient address is required');
    }

    let info = null;
    let lastError = null;
    const connectionPlans = uniqueConnectionPlans(port);

    for (const plan of connectionPlans) {
      const resolvedHost = plan.ipv4Only ? await resolveIPv4(host) : '';
      const transportHost = resolvedHost || host;

      const transporter = nodemailer.createTransport({
        host: transportHost,
        port: plan.port,
        secure: plan.port === 465,
        auth: useAuth ? { user, pass: password } : undefined,
        connectionTimeout: 10000,
        greetingTimeout: 5000,
        socketTimeout: 8000,
        tls: {
          rejectUnauthorized: !allowInsecure,
          servername: host,
        },
      });

      try {
        info = await transporter.sendMail({
          from: `SkillForge <${fromAddr}>`,
          to,
          subject,
          text,
          html,
        });
        lastError = null;
        break;
      } catch (err) {
        lastError = err;
        if (!isTransientSmtpError(err)) {
          throw err;
        }
        await delay(700);
      }
    }

    if (!info) {
      throw lastError || new Error('Connection timeout');
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
