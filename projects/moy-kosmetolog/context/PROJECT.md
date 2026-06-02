# Мой косметолог — Project Overview for AI Agents

AI-powered skincare platform. Users photograph their skin → get GPT-4o analysis → receive personalized routines, articles, doctor recommendations. Russian-language audience, mobile-first PWA.

---

## Architecture

```
nginx (reverse proxy)
  ├── /api/*   → FastAPI (Python)  :3000
  ├── /admin   → Admin CMS (Next.js) :3002
  └── /        → PWA (Next.js)     :3001
       ↓
  PostgreSQL 16  :5432
  Redis 7        :6379
  Yandex S3 (object storage)
```

Monorepo — `packages/` with npm workspaces.

| Package | Stack | Status |
|---|---|---|
| `packages/api-python` | Python 3.12, FastAPI, SQLAlchemy 2 async | **Active backend** |
| `packages/web` | Next.js 16 App Router, React 19, Tailwind v4 | **Active frontend** |
| `packages/api` | Node/Fastify (Kysely) | Legacy placeholder, ignore |

External repo `../moy-kosmetolog-admin` is the Admin CMS (mounted in Docker as `kosmetolog-admin`).

---

## Backend — `packages/api-python`

**Entry:** `app/main.py`  
**Run locally:** `uvicorn app.main:app --reload --port 3000`  
**API base:** `/api/v1`  
**Docs:** `/docs` (dev only)  
**Health:** `GET /health`

### Routers (all under `/api/v1`)

| Prefix | Module | Key functionality |
|---|---|---|
| `/auth` | `routers/auth.py` | OTP phone auth, JWT refresh, OAuth (Apple, Google, VK, Yandex, Telegram) |
| `/profile` | `routers/user.py` | User CRUD, skin profile (type, concerns, routine) |
| `/scan` | `routers/scan.py` | AI vision skin scan, anonymous→auth claim flow |
| `/home` | `routers/home.py` | Personalized dashboard data |
| `/articles` | `routers/articles.py` | Educational content |
| `/cosmetic_analysis` | `routers/cosmetic_analysis.py` | Scan breakdown |
| `/recommendations` | `routers/recommendations.py` | Personalized product/routine recs |
| `/diary` | `routers/diary.py` | Skin diary entries + streak stats |
| `/feed` | `routers/feed.py` | Community posts, likes, comments |
| `/chat` | `routers/chat.py` | AI FAQ chat (Claude) |
| `/doctors` | `routers/doctors.py` | Doctor catalog + reviews |
| `/upload` | `routers/upload.py` | Image upload to Yandex S3 |
| `/routine` | `routers/routine.py` | User routines + product selection |

### Database

ORM: SQLAlchemy 2.0 async, models in `app/models/`.  
Migrations: Alembic (`migrations/`), run with `alembic upgrade head`.  
Docker startup runs migrations automatically before the app starts.

**Key models:** `User`, `Scan`, `SkinDiaryEntry`, `FeedPost`, `Comment`, `Like`, `Recommendation`, `ChatSession`, `ChatMessage`, `DoctorProfile`, `DoctorReview`, `UserRoutine`, `RoutineProduct`, `Article`.

`User.auth_provider` enum: `PHONE | APPLE | GOOGLE | VK | YANDEX | TELEGRAM`

### AI integrations

- **OpenAI GPT-4o** (`OPENAI_VISION_MODEL=gpt-4o`) — skin photo analysis in `routers/scan.py`
- **Anthropic Claude** (`ANTHROPIC_CHAT_MODEL=claude-sonnet-4-5`) — FAQ chat + recommendations

Dev: `OPENAI_API_KEY` is empty, scan uses mock response. SMS OTP is mocked too — code prints to console.

### Auth flow

1. User submits phone → OTP sent via SMS.ru (mocked in dev)
2. OTP verified → JWT access (15 min) + refresh (30 days) issued
3. Anonymous scan can be claimed after registration (`/scan/{id}/claim`)

---

## Frontend — `packages/web`

**Entry:** `app/layout.tsx`  
**Run locally:** `npm run dev` (port 3001)  
**Middleware:** `middleware.ts` — validates JWT, redirects unauthed users to `/main/otp`

### Routing (Next.js App Router)

**Public (no auth):**
- `/main/welcome` — Landing, theme picker
- `/main/otp` — Phone input + OTP verification
- `/main/scan` — Anonymous skin scan
- `/main/scan/result` — Scan result preview
- `/callback` — OAuth callback (Apple/Google/VK)

**Protected (JWT required):**
- `/main/home` — Personalized dashboard
- `/main/chat` — AI FAQ chatbot
- `/main/diary` — Skin diary + streak tracking
- `/main/profile` — User profile + onboarding
- `/main/onboarding` — Initial skin profile setup
- `/main/scan/[id]` — Individual scan detail

Navigation is a fixed bottom tab bar (`HaloTabBar`): Home / Chat / Diary / Profile.

### Design system — Halo DS

**Location:** `packages/web/halo-ds/`  
**Full docs:** `packages/web/halo-ds/CLAUDE.md` — READ THIS before touching UI.

Quick rules:
- All colors via CSS tokens (`--halo-accent`, `--halo-ink-soft`, etc.) — no hardcoded hex/rgb
- 4 themes: `cream` (default/warm), `rose`, `sage`, `midnight` (dark)
- Typography: Inter (body), Instrument Serif (display), JetBrains Mono (code)
- Key components: `HaloGlass`, `HaloButton`, `HaloRing`, `HaloTabBar`, `HaloSheet`, `HaloHeading`
- Variants via `class-variance-authority`, utility via `cn()` (clsx + tailwind-merge)

### State management

- **Server state:** TanStack Query v5 (`@tanstack/react-query`)
- **Client state:** Zustand v5
- **HTTP:** axios (base URL from env, JWT auto-attached)

### PWA

Service worker registered in `layout.tsx`. `manifest.json` present. MediaPipe runs client-side for skin landmark detection before upload.

---

## Infrastructure

### Docker Compose (local dev + prod)

```bash
docker compose up -d          # start all
docker compose logs -f api    # stream API logs
docker compose exec api bash  # shell into API container
```

Services: `kosmetolog-db` (pg:5432), `kosmetolog-redis` (redis:6379), `kosmetolog-api` (:3000), `kosmetolog-web` (:3001), `kosmetolog-admin` (:3002).

Nginx sits in front of all services in production (`nginx/kosmetolog.conf`). In dev there is also a `nginx.conf` that Docker uses.

### Key env vars (see `packages/api-python/.env.example`)

```
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
JWT_ACCESS_SECRET / JWT_REFRESH_SECRET
SMS_MOCK=true                     # dev: OTP printed to console
OPENAI_API_KEY                    # empty in dev → mock scan
ANTHROPIC_API_KEY
S3_ENDPOINT / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY  # Yandex Cloud
TELEGRAM_BOT_TOKEN
```

**Changing `.env` does not require container recreation** — uvicorn `--reload` picks up changes automatically.

---

## Development cheat-sheet

```bash
# start infra only
docker compose up -d kosmetolog-db kosmetolog-redis

# backend
cd packages/api-python
uvicorn app.main:app --reload --port 3000

# frontend
cd packages/web
npm run dev

# migrations
cd packages/api-python
alembic upgrade head
alembic revision --autogenerate -m "description"

# seed
python -m app.seed   # (or via docker: docker compose exec api python -m app.seed)

# lint/format backend
ruff check . && ruff format .

# lint frontend
npm run lint
```

**Test credentials (after seed):**
- Doctor: `+79161111111`
- User: `+79162222222`
- OTP: any 4-digit code (mock mode)

---

## Key file locations

| What | Where |
|---|---|
| FastAPI app factory | `packages/api-python/app/main.py` |
| ORM models | `packages/api-python/app/models/` |
| Alembic config | `packages/api-python/alembic.ini` |
| Next.js root layout | `packages/web/app/layout.tsx` |
| Auth middleware | `packages/web/middleware.ts` |
| Halo DS tokens | `packages/web/halo-ds/tokens.css` |
| Halo DS docs | `packages/web/halo-ds/CLAUDE.md` |
| Docker orchestration | `docker-compose.yml` |
| Nginx (prod) | `nginx/kosmetolog.conf` |
| DB bootstrap SQL | `init.sql` |
