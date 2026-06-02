# Test coverage target

## When to apply
Backend task with acceptance criterion mentioning new endpoint or new business logic.

## Rule
For every new public function or endpoint, write at minimum:
1. Happy path test
2. One error path test (validation error or not-found)

For new endpoints additionally:
3. Auth test (401 if not authenticated, where applicable)

Tests in `tests/<mirroring source path>/test_<filename>.py`.

## Anti-pattern
Skipping tests "for speed". cto_review will request_changes for missing tests on new public API.
