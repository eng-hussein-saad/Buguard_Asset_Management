# Contract: Analysis Report API

## POST `/analysis/report`

Generates an authenticated inventory risk report from assets in the current
user's organization.

### Authentication

Requires a valid bearer access token. Organization scope is derived from the
token and current user only.

### Rate Limit

Uses the documented AI analysis rate limit policy.

### Request

```json
{
  "filters": {
    "type": "certificate",
    "status": "active",
    "tag": "production",
    "source": "assessment-sample",
    "value_contains": "example.com",
    "certificate_lifecycle_status": "expiring_soon"
  },
  "limit": 100
}
```

All fields are optional except authentication. `organization_id` is not accepted.

### Successful Completed Response: `200`

```json
{
  "status": "completed",
  "summary": "The selected inventory contains expiring certificate exposure for api.example.com.",
  "risks": [
    {
      "title": "Certificate expiring soon",
      "severity": "medium",
      "description": "Certificate expires within 30 calendar days.",
      "evidence_asset_ids": ["00000000-0000-0000-0000-000000000001"]
    }
  ],
  "evidence_asset_ids": ["00000000-0000-0000-0000-000000000001"],
  "generated_at": "2026-06-28T12:00:00Z",
  "message": null
}
```

### No Matching Assets Response: `200`

```json
{
  "status": "no_data",
  "summary": "No matching assets were available for analysis.",
  "risks": [],
  "evidence_asset_ids": [],
  "generated_at": "2026-06-28T12:00:00Z",
  "message": "No matching assets were available for the requested filters."
}
```

### Provider Unavailable Response: `503`

```json
{
  "error": {
    "code": "analysis_unavailable",
    "message": "Analysis provider is not configured or unavailable.",
    "details": {}
  }
}
```

### Provider Failure Response: `502`

```json
{
  "error": {
    "code": "analysis_failed",
    "message": "Analysis provider could not complete the report.",
    "details": {}
  }
}
```

### Validation or Grounding Failure Response: `502`

```json
{
  "error": {
    "code": "analysis_grounding_failed",
    "message": "Analysis provider returned unsupported evidence.",
    "details": {}
  }
}
```

### Required Behaviors

- Authenticate before selecting organization-owned assets.
- Apply filters only within the authenticated organization.
- Return no data rather than fabricated analysis for empty matches.
- Validate every risk evidence ID against the selected evidence set.
- Include expired and expiring-soon certificate lifecycle risks using the shared
  certificate lifecycle classifier.
- Never expose provider secrets, prompts containing secrets, internal exception
  details, or cross-tenant facts.
