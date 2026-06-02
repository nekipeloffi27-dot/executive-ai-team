# Halo DS — spacing and color

## When to apply
You are writing HTML+Tailwind for a moy-kosmetolog mockup.

## Rules
- **Spacing scale only**: `gap-2, gap-3, gap-4, gap-6, gap-8, gap-12, gap-16`. Never arbitrary like `gap-[13px]`.
- **Color tokens only**: `bg-halo-base-50/100/200`, `text-halo-ink-700/900`, `border-halo-line-200`. Never raw hex.
- **Radius scale only**: `rounded-md, rounded-lg, rounded-xl, rounded-2xl, rounded-full`.
- **Padding scale**: same as spacing — multiples of 4 only.

## Why
The product app uses Halo DS tokens. If your mockup uses arbitrary values, the dev agent has to translate them and often picks slightly wrong values → visual drift between mockup and shipped code.

## Reference
See `DESIGN_SYSTEM.md` for the token list.
