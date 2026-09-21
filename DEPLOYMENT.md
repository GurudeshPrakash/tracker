# Deployment Guide: FLUX Tracker

This application is fully production-ready and containerized with Docker, FastAPI, and a pre-compiled TypeScript React frontend.

---

## 🚀 Option 1: Deploy on Render (Recommended)

1. Fork or push this repository to GitHub: [https://github.com/GurudeshPrakash/tracker](https://github.com/GurudeshPrakash/tracker)
2. Log in to [Render.com](https://render.com).
3. Click **New +** &rarr; **Blueprint** (or **Web Service**).
4. Connect your GitHub repository `GurudeshPrakash/tracker`.
5. Render will automatically detect `render.yaml` with:
   - Docker runtime
   - Port `8501`
   - Persistent Disk mounted at `/app/data` (ensuring your SQLite database persists across redeploys)
   - Health check probe on `/api/health`
6. Click **Apply / Deploy**.

---

## 🚂 Option 2: Deploy on Railway

1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** &rarr; **Deploy from GitHub repo**.
3. Select `tracker`.
4. Add a **Persistent Volume**:
   - Go to the service **Settings** &rarr; **Volumes**.
   - Add Volume mounted to `/app/data`.
5. Under **Variables**, set:
   - `PORT=8501`
6. Railway will build the Dockerfile and launch your application automatically.

---

## 🪽 Option 3: Deploy on Fly.io

1. Install Fly CLI: `winget install flyctl` (or `brew install flyctl` on macOS).
2. Authenticate: `fly auth login`.
3. Create persistent storage volume:
   ```bash
   fly volumes create tracker_data --size 1
   ```
4. Deploy using the included `fly.toml`:
   ```bash
   fly deploy
   ```

---

## 🐳 Option 4: Deploy with Docker / Docker Compose (Any VPS / Local)

1. Clone the repository on your server:
   ```bash
   git clone https://github.com/GurudeshPrakash/tracker.git
   cd tracker
   ```
2. Start container with persistent volume:
   ```bash
   docker compose up -d
   ```
3. Open `http://<your-server-ip>:8501`.
