# Frontend web dev agent — operating rules

You are a frontend dev agent for the **PWA** (Next.js 16 App Router) inside a sandbox.

## Repo structure (moy-kosmetolog monorepo, pnpm workspaces)

- `packages/web/` — **your playground** (Next.js PWA)
- `packages/api-python/` — Python FastAPI backend (not your area)
- `packages/api/` — legacy Node service (ignore)

Work only inside `packages/web/`.

## Tech stack rules (packages/web/)

- **Next.js 16** App Router, **React 19**, TypeScript strict mode
- **Tailwind CSS v4** + **Halo DS** (custom design system, see below)
- State: TanStack Query v5 for server state, Zustand v5 for client state
- Forms: react-hook-form + zod
- HTTP: **axios** (base URL from env, JWT auto-attached interceptor)
- API contracts auto-typed where possible from FastAPI OpenAPI
- Middleware in `middleware.ts` — validates JWT, redirects unauthed users to `/main/otp`
- PWA: service worker registered in `app/layout.tsx`, `manifest.json` present
- MediaPipe runs client-side for skin landmark detection before scan upload

## Halo Design System

**Location:** `packages/web/halo-ds/`
**Full docs:** `packages/web/halo-ds/CLAUDE.md` — READ THIS before touching UI.

### Rules

- **Colors only via CSS tokens** (`--halo-accent`, `--halo-ink-soft`, etc.) — no hardcoded hex/rgb
- **4 themes:** `cream` (default/warm), `rose`, `sage`, `midnight` (dark)
- **Typography:** Inter (body), Instrument Serif (display), JetBrains Mono (code) — applied via Halo Heading / text classes; do NOT pick raw `font-*` Tailwind classes
- **Key components:** `HaloGlass`, `HaloButton`, `HaloRing`, `HaloTabBar`, `HaloSheet`, `HaloHeading` — reuse, don't reinvent
- **Variants** via `class-variance-authority`; utility merging via `cn()` (clsx + tailwind-merge)
- Tokens file: `packages/web/halo-ds/tokens.css`

## Routing (Next.js App Router)

**Public (no JWT):**
- `/main/welcome` — Landing, theme picker
- `/main/otp` — Phone + OTP verification
- `/main/scan` — Anonymous skin scan
- `/main/scan/result` — Scan result preview
- `/callback` — OAuth callback

**Protected (JWT required):**
- `/main/home` — Dashboard
- `/main/chat` — AI FAQ chat
- `/main/diary` — Skin diary + streaks
- `/main/profile` — User profile + onboarding
- `/main/onboarding` — Initial skin setup
- `/main/scan/[id]` — Scan detail

Bottom tab bar (`HaloTabBar`): Home / Chat / Diary / Profile.

## Forbidden

- `any` type except extreme cases with `// eslint-disable` + comment why
- Default exports for components (named exports only)
- `console.log` in production code (use a proper logger)
- Direct `fetch()` — only through axios client
- Hardcoded hex/rgb colors — always Halo tokens
- shadcn/ui or Material UI — Halo DS only
- Raw Tailwind `font-*` classes — use Halo typography classes
- Hardcoded text outside i18n catalog (if i18n exists in the repo — follow it)

## Tests

- Vitest + React Testing Library
- Test user-facing behavior, not internals
- E2E in `packages/web/e2e/` via Playwright — don't add new e2e without explicit instruction

## Accessibility & mobile

- **Mobile-first**: every new feature must work at 375px width before desktop is considered
- Semantic tags (`<button>` for clickables, not `<div onClick>`)
- `aria-labels` for icon-only buttons
- AA contrast minimum for text
