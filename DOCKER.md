# Running Mirage with Docker

This starts all three services (`ai/`, `backend/`, `frontend/`) together,
with the backend's database pre-populated with realistic demo data — a
handful of past interview sessions with real Trust DNA scores and evidence
(computed by actually running the AI engine, not fake numbers), some
clean, some flagged for manual review, plus one still "live." You should
see exactly the same thing the person who sent you this repo sees.

## Prerequisites

**Linux**

1. Install Docker Engine + the Compose plugin. On most distros:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
   (or use your distro's package manager — `docker.io`/`docker-ce` plus
   `docker-compose-plugin`).
2. Add yourself to the `docker` group so you don't need `sudo` for every
   command, then start a new shell (or log out/in):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```
3. Make sure the Docker daemon is running:
   ```bash
   sudo systemctl start docker
   ```

**Windows**

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. During setup, make sure the **WSL2 backend** is enabled (Docker Desktop
   will prompt for this — accept it; it may also ask to install/enable
   WSL2 itself if you don't have it yet).
3. Launch Docker Desktop and wait for it to say "Docker Desktop is running"
   (the whale icon in the system tray stops animating).
4. Use either PowerShell, Command Prompt, or a WSL terminal — the commands
   below are identical on all of them.

## Run it

From the repo root (same folder as `docker-compose.yml`):

```bash
docker compose up --build
```

(Windows: run the exact same command in PowerShell.)

First run takes a few minutes (downloading base images, installing
dependencies, building the frontend). Subsequent runs are much faster.

Once it settles, open **http://localhost:5173** in a browser. Log in with
anything (it's a demo gate, any input works) and you'll land on a
Dashboard already populated with 6 sessions.

To run it in the background instead of tying up your terminal:

```bash
docker compose up --build -d
```

## Stopping it

```bash
docker compose down
```

Demo data persists in a Docker volume, so the next `docker compose up`
won't re-seed or lose anything. If you want a completely fresh reset
(re-seed from scratch):

```bash
docker compose down -v
```

## Troubleshooting

- **"port is already allocated"** — something else on your machine is
  using port 8000, 8001, or 5173. Stop that other thing, or edit the port
  numbers on the left-hand side of the `ports:` entries in
  `docker-compose.yml` (e.g. `"5174:80"` instead of `"5173:80"`).
- **Windows: Docker Desktop must be running** before `docker compose`
  commands will work at all — if you get a "cannot connect to the Docker
  daemon" error, open Docker Desktop and wait for it to finish starting.
- **Linux: "permission denied ... docker.sock"** — you're not in the
  `docker` group yet, or haven't started a new shell since being added to
  it. Run `sudo usermod -aG docker $USER && newgrp docker` and try again.
- **Dashboard looks empty** — the backend only seeds once, on its very
  first start (when its data volume is empty). If you ran `docker compose
  down` without `-v` the data is still there; if something looks broken,
  `docker compose down -v` then `docker compose up --build` gives you a
  guaranteed-fresh, freshly-seeded start.
- **Checking logs** — `docker compose logs -f backend` (or `ai`,
  `frontend`) streams that service's logs if something isn't behaving.
