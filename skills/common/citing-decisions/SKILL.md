# Citing decisions

## When to apply
You are about to make a recommendation, design choice, or technical decision.

## Rule
Before recommending anything that touches a previously-decided area, **first call `read_decisions`** and check if your direction conflicts with an active CEO decision.

If it does conflict, explicitly call it out: "This contradicts decision #N (topic). I propose either: (a) keeping the old decision, (b) revising it because <new evidence>."

## Anti-pattern
Recommending something that contradicts an active decision without acknowledging it. The CEO will catch this and have to redo work.
