# API contract discipline

## When to apply
Task involves a new or modified API endpoint.

## Rule
The `api_contract` field in the task JSON must be **exact**:

```json
{
  "endpoint": "POST /api/v1/scan",
  "request": {
    "Content-Type": "multipart/form-data",
    "fields": {"image": "binary, ≤10MB, jpeg/png", "user_id": "uuid"}
  },
  "response_201": {"scan_id": "uuid", "queued_at": "iso8601"},
  "response_400": {"error": "string", "code": "string"},
  "response_413": {"error": "image too large", "code": "PAYLOAD_TOO_LARGE"}
}
```

## Why
- Frontend dev parallelizes with backend dev because contract is fixed.
- cto_review checks contract drift in PR review — automatic catch.
- Без contract review approval → request_changes по contract drift в 60% случаев.

## Anti-pattern
Writing "return scan info" instead of explicit response shape. Then frontend assumes one structure, backend returns another, PR ping-pong.
