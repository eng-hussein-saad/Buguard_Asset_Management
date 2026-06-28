# Contract: Asset Certificate Lifecycle API

## Shared Lifecycle Status

Certificate assets derive `certificate_lifecycle_status` from
`metadata.expires`.

Allowed values:

- `expired`
- `expiring_soon`
- `valid`
- `unknown`

The raw `metadata.expires` value remains unchanged in `metadata`.

## GET `/assets/{asset_id}`

### Certificate Response Addition

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "type": "certificate",
  "value": "cert-api-example",
  "status": "active",
  "source": "assessment-sample",
  "tags": ["tls"],
  "metadata": {
    "issuer": "Example CA",
    "expires": "2026-07-15"
  },
  "certificate_lifecycle_status": "expiring_soon",
  "first_seen": "2026-06-28T12:00:00Z",
  "last_seen": "2026-06-28T12:00:00Z",
  "created_at": "2026-06-28T12:00:00Z",
  "updated_at": "2026-06-28T12:00:00Z"
}
```

Non-certificate assets may omit the field or return `null`, as long as the
contract is documented consistently in OpenAPI and README examples.

## GET `/assets`

### Query Addition

`certificate_lifecycle_status=expired|expiring_soon|valid|unknown`

### Required Behavior

- Filtering applies only to certificate assets in the authenticated organization.
- The filter must never count, return, or imply certificates from another
  organization.
- The list response includes derived lifecycle status for certificate assets.

## GET `/assets/{asset_id}/graph`

### Certificate Node Addition

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "type": "certificate",
  "value": "cert-api-example",
  "label": "cert-api-example",
  "certificate_lifecycle_status": "expiring_soon"
}
```

### Required Behavior

- Certificate graph nodes expose lifecycle status when graph data includes
  certificates.
- `covers` relationship edges appear with `relationship_type` and `label` set to
  `covers`.
- Graph data remains one-hop and organization-scoped according to existing graph
  behavior.

## Import Reporting Addition

Malformed certificate `metadata.expires` values are reported without removing
unrelated valid records from the same batch.

```json
{
  "created": 2,
  "updated": 0,
  "failed": 1,
  "errors": [
    {
      "index": 2,
      "reason": "Certificate metadata.expires is malformed."
    }
  ]
}
```
