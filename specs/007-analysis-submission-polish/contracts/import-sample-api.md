# Contract: Sample-Shaped Bulk Import API

## POST `/assets/import`

Imports evaluator dataset records using the existing authenticated bulk import
endpoint.

### Authentication and Authorization

Requires a valid bearer token and the existing bulk import permission. The
server derives organization ownership from the authenticated user only.

### Request

```json
{
  "items": [
    {
      "id": "a1",
      "type": "domain",
      "value": "example.com",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["external"],
      "metadata": {
        "registrar": "Example Registrar"
      }
    },
    {
      "id": "a2",
      "type": "subdomain",
      "value": "api.example.com",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["api"],
      "metadata": {},
      "parent": "a1"
    },
    {
      "id": "a3",
      "type": "certificate",
      "value": "cert-api-example",
      "status": "active",
      "source": "assessment-sample",
      "tags": ["tls"],
      "metadata": {
        "issuer": "Example CA",
        "expires": "2026-07-15"
      },
      "covers": "a2"
    }
  ]
}
```

### Success Response: `200`

```json
{
  "created": 3,
  "updated": 0,
  "failed": 0,
  "errors": []
}
```

### Partial Success Response: `207`

```json
{
  "created": 2,
  "updated": 0,
  "failed": 2,
  "errors": [
    {
      "index": 2,
      "reason": "Certificate metadata.expires is malformed."
    },
    {
      "index": 3,
      "reason": "Unresolved covers reference: missing-record."
    }
  ]
}
```

### No Accepted Records Response: `422`

```json
{
  "created": 0,
  "updated": 0,
  "failed": 1,
  "errors": [
    {
      "index": 0,
      "reason": "Asset value must not be blank."
    }
  ]
}
```

### Relationship Mapping

- `parent` creates a `parent` relationship from the subdomain asset to the
  referenced domain asset.
- `covers` creates a `covers` relationship from the certificate asset to the
  referenced subdomain asset.

### Required Behaviors

- `id` is an import-local external reference only.
- `organization_id` is rejected if supplied.
- Valid records are created or refreshed even when unrelated records fail.
- Relationship references resolve only within the same authenticated import
  context.
- Relationships are not created for missing, invalid, skipped, duplicate,
  ambiguous, or unsafe references.
- Tags and metadata, including nested certificate issuer and expiry values, are
  preserved according to existing import merge behavior.
- Larger datasets use the same shape and record-level reporting semantics.
