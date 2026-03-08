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
- Start Command: `gunicorn app:app`

## 4. Environment variables in Render
Most are already declared in `render.yaml`. Set secret values in Render dashboard:
- `FLASK_SECRET_KEY` = strong random string
- `GEMINI_API_KEY` = (optional) your Gemini key
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `EMAIL_FROM`
- `SMTP_ALLOW_INSECURE` = `false` (recommended)

Do not commit local secrets from `instance/config.py`.

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
