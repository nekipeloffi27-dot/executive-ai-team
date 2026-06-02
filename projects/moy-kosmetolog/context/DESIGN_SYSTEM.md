# Halo Design System — moy-kosmetolog

> Полная DS живёт в коде продукта в `web/lib/halo/`. Этот файл — выжимка для Designer-агента чтобы не блуждать по репо.

## Color tokens

### Base (поверхности)
- `halo-base-50` — почти белый фон (#FAFAF8)
- `halo-base-100` — светло-нейтральный (#F4F3EE)
- `halo-base-200` — карточки на сером фоне
- `halo-base-300` — границы

### Ink (текст)
- `halo-ink-900` — основной текст (почти чёрный)
- `halo-ink-700` — secondary
- `halo-ink-500` — placeholder
- `halo-ink-400` — disabled

### Accent (бренд)
- `halo-accent-500` — основной акцент (CTA, links). Тёплый розово-бежевый, не яркий.
- `halo-accent-300` — light version (hover, focus rings)
- `halo-accent-700` — dark version (pressed states)

### Semantic
- `halo-success-500` (зелёный травяной, приглушённый)
- `halo-warn-500` (тёплый жёлто-янтарный)
- `halo-danger-500` (красно-терракотовый, не алый)

### Line
- `halo-line-200` — divider тонкие
- `halo-line-300` — divider обычные

## Spacing scale (в Tailwind classes)
`gap-2 (8px), gap-3 (12px), gap-4 (16px), gap-6 (24px), gap-8 (32px), gap-12 (48px), gap-16 (64px)`

## Radius
`rounded-md (6px), rounded-lg (10px), rounded-xl (16px), rounded-2xl (20px), rounded-full`

## Typography classes
- `text-display-xl` — hero (40-48px), Halo Display, weight 700
- `text-display-lg` — section header (32-36px)
- `text-display-md` — card title (24-28px)
- `text-display-sm` — subhead (20px)
- `text-body-lg` — основной текст (18px)
- `text-body-md` — обычный (16px)
- `text-body-sm` — мелкий (14px)
- `text-body-xs` — caption (12px)
- `text-label-lg/md/sm` — labels на кнопках, формах

## Brand voice (для микрокопи)
- Тон: тёплый, экспертный, не снисходительный
- "Ты" обращение
- Без американизмов («great»), без эмодзи в системных текстах
- Никаких «*WoW*», «*Magic*», «*AI-powered*»
- Скорее: «Понял твою кожу», «Подобрал уход», «Ещё 2 шага»

## Anti-patterns (что НЕ делаем)
- Глянцевые градиенты (Lóvi и AI-генераторы их любят, мы — нет)
- Яркие неоновые акценты
- Декоративные иконки которые не несут информации
- Stock photos с пластиковыми улыбками
- "AI shimmer" анимации (можно лёгкий fade-in, но не больше)
