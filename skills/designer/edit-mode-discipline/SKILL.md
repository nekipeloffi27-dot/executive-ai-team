# Edit mode discipline

## When to apply
The task is in EDIT mode (modifying an existing screen, not creating new).

## Rules
1. **First** call `codebase_grep` with the screen/component name to find existing files.
2. **Then** call `codebase_read` on the relevant files to understand current structure.
3. **Only then** propose changes — as a diff against the existing code, not a rewrite.
4. Reuse existing component imports. Don't introduce a new component if one already exists for the use case.

## Anti-pattern
Producing a fresh HTML mockup that ignores the existing component tree. Dev agent then has to either replace working components or merge two implementations.

## Output template for EDIT
```
## Affected files
- web/app/(scan)/results/page.tsx
- web/components/scan/ResultCard.tsx

## Changes
### `web/components/scan/ResultCard.tsx`
- Add `severity: 'mild' | 'moderate' | 'severe'` prop
- Render severity badge in top-right corner

### `web/app/(scan)/results/page.tsx`
- Pass `severity` from API response to `<ResultCard>`
```
