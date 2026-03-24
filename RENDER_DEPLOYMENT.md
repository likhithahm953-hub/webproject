# Render Deployment Guide (Flask)

## 1. Push this folder to GitHub
Use the `webproject/` folder as the repository root (the folder that contains `app.py`).

## 2. Create service from Blueprint (recommended)
1. Go to Render dashboard.
2. Click `New` -> `Blueprint`.
3. Connect your GitHub repo.
4. Render detects `render.yaml` and creates the service + disk config.

Alternative: create a standard Web Service manually if you do not want Blueprint.

## 3. Build and start settings
- Build Command: `pip install -r requirements.txt`
- Build Command: `npm install --omit=dev && pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## 4. Environment variables in Render
Most are already declared in `render.yaml`. Set secret values in Render dashboard:
- `FLASK_SECRET_KEY` = strong random string
- `GEMINI_API_KEY` = (optional) your Gemini key
- `REQUIRE_EMAIL_VERIFICATION` = `true`
- `EMAIL_PROVIDER` = `nodemailer`
- `NODEMAILER_HOST` = your SMTP relay host (for example `smtp.gmail.com`)
- `NODEMAILER_PORT` = `465` (SSL) or `587` (STARTTLS)
- `NODEMAILER_USE_AUTH` = `true`
- `NODEMAILER_USER` = relay username
- `NODEMAILER_PASS` = relay password or app password
- `EMAIL_FROM` = sender email, for example `noreply@yourdomain.com`
- `SERVER_BASE_URL` = your public site URL, for example `https://your-app.onrender.com`
- `EMAIL_VERIFICATION_EXPIRY_SECONDS` = `900` (15 minutes recommended for hosted environments)

Optional Resend alternative only if you do not use NodeMailer:
- `EMAIL_PROVIDER` = `resend`
- `RESEND_API_KEY` = your Resend API key

Security option for self-signed relays:
- `NODEMAILER_ALLOW_INSECURE` = `false` (recommended; set `true` only if your relay requires insecure TLS)

Do not commit local secrets from `instance/config.py`.

## 4.1 Render Dashboard Checklist
In the Render service settings, enter these exact values:
- `EMAIL_PROVIDER=nodemailer`
- `NODEMAILER_HOST=<your mail relay host>`
- `NODEMAILER_PORT=587`
- `NODEMAILER_USE_AUTH=true`
- `NODEMAILER_USER=<your mail username>`
- `NODEMAILER_PASS=<your mail password/app password>`
- `EMAIL_FROM=<your sender, for example noreply@yourdomain.com>`
- `SERVER_BASE_URL=https://<your-render-service>.onrender.com`
- `EMAIL_VERIFICATION_EXPIRY_SECONDS=900`
- `REQUIRE_EMAIL_VERIFICATION=true`
- `FLASK_SECRET_KEY=<strong random secret>`

Leave this blank unless you explicitly want Resend alternative:
- `RESEND_API_KEY`

## 5. Persistent data note (important)
This project uses SQLite. `render.yaml` mounts a persistent disk and sets:
- `DATABASE_PATH=/var/data/database.db`
- `DATA_DIR=/var/data`

If you remove the disk, data may reset on redeploy.

## 6. Deploy
Click `Apply` in Blueprint flow (or `Create Web Service` in manual flow).
After build completes, open the Render URL.

## 7. Verify app
- Open `/signup`
- Create a user and login
- Check `/profile` upload
- Check `/certificates` download + verification link

## 8. If build fails
- Ensure repo root contains: `app.py`, `requirements.txt`, `Procfile`.
- Confirm start command is exactly: `gunicorn app:app`.
- Confirm `render.yaml` is in repo root and valid YAML.
