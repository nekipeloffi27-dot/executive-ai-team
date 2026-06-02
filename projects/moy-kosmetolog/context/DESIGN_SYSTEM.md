# Halo Design System — moy-kosmetolog

> Полная DS живёт в коде продукта в `packages/web/halo-ds/`.
> Источник истины — `packages/web/halo-ds/CLAUDE.md` (читать при работе с UI).
> Этот файл — выжимка для Designer-агента чтобы не блуждать по репо.

## Tokens

Все цвета через CSS-переменные в `packages/web/halo-ds/tokens.css`. Примеры:
- `--halo-accent` — основной акцент темы
- `--halo-ink-soft` — текстовая краска (приглушённая)
- `--halo-ink-strong` — текстовая краска (сильная)
- `--halo-surface` — поверхности карточек
- `--halo-bg` — фон

**Никогда не хардкодим hex/rgb.** Только токены. Это даёт автоматическую поддержку 4 тем.

## Themes (4)

- `cream` (default) — тёплый кремовый, основной
- `rose` — розоватый, женственный
- `sage` — приглушённый зелёный
- `midnight` — тёмная тема

Пользователь выбирает на `/main/welcome` (theme picker). Дизайнер делает мокап в одной теме (`cream` по умолчанию), но классы должны переключаться корректно.

## Typography

- **Inter** — body, UI
- **Instrument Serif** — display (большие заголовки, hero)
- **JetBrains Mono** — code/mono блоки

Применяется через Halo-классы (см. `halo-ds/CLAUDE.md`), не через сырые `font-*` Tailwind.

## Key components (Halo DS)

- `HaloGlass` — стеклянный контейнер с blur (frosted)
- `HaloButton` — кнопки всех вариантов
- `HaloRing` — круговой progress / decorative ring
- `HaloTabBar` — нижняя навигация (Home / Chat / Diary / Profile)
- `HaloSheet` — bottom sheet / modal
- `HaloHeading` — типографические заголовки

Вариантность через `class-variance-authority`. Утилита `cn()` (clsx + tailwind-merge) для merge классов.

## Brand voice (микрокопи)

- Тон: тёплый, экспертный, не снисходительный
- **"Ты"** обращение
- Без американизмов («great»), без эмодзи в системных текстах
- Никаких «*WoW*», «*Magic*», «*AI-powered*»
- Скорее: «Понял твою кожу», «Подобрал уход», «Ещё 2 шага»

## Anti-patterns (что НЕ делаем)

- Глянцевые градиенты как dominant element
- Яркие неоновые акценты
- Декоративные иконки без функции
- Stock-фото с пластиковыми улыбками
- "AI shimmer" анимации (лёгкий fade-in допустим)
- shadcn/ui, Material UI — у нас Halo DS

## Density / layout

- Mobile-first: каждая фича должна работать на 375px width
- Воздух важнее наполнения
- Bottom tab bar — фикс на mobile
- Spacing scale: придерживаемся Tailwind v4 spacing (через токены, не arbitrary)
