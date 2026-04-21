# API Conventions (Gateway)

## Versioning
- All business APIs are exposed under `/api/v1`.
- Gateway operational endpoints are under `/gateway/*`.

## Error Response Format
All normalized gateway errors use:

```json
{
  "error": {
    "code": "machine_readable_code",
    "message": "Human-readable summary",
    "details": {}
  },
  "request_id": "uuid-or-client-request-id"
}
```

## Pagination Format
Paginated endpoints should return:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 145,
    "total_pages": 8
  },
  "request_id": "uuid"
}
```

## Status Code Conventions
- `200` for successful reads.
- `201` for successful creates.
- `204` for successful delete/update without body.
- `400` for validation errors.
- `401` for unauthenticated requests.
- `403` for forbidden requests.
- `404` for unknown routes/resources.
- `429` for rate-limited requests.
- `502` when an upstream service is unreachable.

