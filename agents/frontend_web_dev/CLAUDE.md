# Frontend web dev agent — operating rules

You are a frontend dev agent for the **web** app (Next.js 14 App Router) inside a sandbox.

## Tech stack rules (moy-kosmetolog web)

- Next.js 14 App Router, React 18, TypeScript strict mode
- Styling: Tailwind CSS + Halo Design System tokens (see `web/lib/halo/` for DS components)
- State: TanStack Query for server state, Zustand for client state
- Forms: react-hook-form + zod
- API client: `web/lib/api/` (existing patterns, auto-typed from FastAPI OpenAPI)
- Components: `web/components/` for shared, `web/app/(route)/_components/` for route-local
- Никаких inline-стилей, никаких style={{}} prop'ов кроме абсолютно крайних случаев
- Анимации: framer-motion, либо CSS keyframes

## Halo Design System

- **Spacing** только из шкалы DS: `gap-2`, `gap-3`, `gap-4`, `gap-6`, `gap-8`. Никаких `gap-[13px]`.
- **Цвета** только из палитры DS: `bg-halo-base-50`, `text-halo-ink-900`, etc. Никаких arbitrary hex.
- **Шрифты** только Halo Display / Halo Text (см. `web/lib/halo/typography.ts`)
- **Радиусы** только из шкалы: rounded-sm/md/lg/xl/2xl

## Forbidden

- `any` тип кроме крайних случаев с // eslint-disable + комментарием почему
- Default exports для компонентов (named exports only)
- console.log в production коде (используй `lib/log.ts`)
- Прямые fetch — только через api-клиент

## Tests

- Vitest + React Testing Library
- Не тестируй внутренности — тестируй user-facing поведение
- E2E тесты в `web/e2e/` через Playwright (не пиши новые без явного указания)

## Accessibility

- Семантические теги (`<button>` для кликабельных штук, не `<div onClick>`)
- aria-labels для иконок
- Контраст ≥ AA для текста
