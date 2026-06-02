# Halo typography tokens

## When to apply
Any text styling in moy-kosmetolog web.

## Rule
Only use these classes from `web/lib/halo/typography.ts`:
- `text-display-xl, text-display-lg, text-display-md, text-display-sm`
- `text-body-lg, text-body-md, text-body-sm, text-body-xs`
- `text-label-lg, text-label-md, text-label-sm`

Never raw `text-2xl`, `font-bold`, etc.

## Why
Halo DS controls font family (Halo Display / Halo Text), weight, line-height, letter-spacing per token. Raw Tailwind text-* classes will break visual consistency.
