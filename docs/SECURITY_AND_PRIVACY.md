# MIRA Security and Privacy

## Development Status

MIRA is a development and portfolio system.

Use synthetic medical documents only.

MIRA is not represented as HIPAA compliant, production-ready for PHI,
or suitable for clinical decision making.

## Authentication

Browser authentication uses:

- short-lived access JWTs stored in HttpOnly cookies
- refresh JWTs stored in HttpOnly cookies
- rotating server-side refresh sessions
- server-side refresh-token revocation
- logout revocation
- JWT issuer, audience, expiry, and token-type validation

JWT access and refresh tokens are not stored in localStorage or
sessionStorage.

## CSRF Protection

Cookie-authenticated state-changing requests require a CSRF token.

The CSRF value is stored in a non-HttpOnly cookie and must be copied
into the X-CSRF-Token request header.

Authentication cookies remain HttpOnly.

## Authorization

Medical documents and structured extractions remain scoped by the
authenticated user's user_id.

Cross-account document identifiers must not reveal whether a resource
exists under another account.

## Audit Logging

Security-sensitive application actions are persisted in the
audit_events database table.

Audit events may contain:

- opaque user identifiers
- opaque document identifiers
- action type
- outcome
- HTTP status
- timestamp

Audit events must never contain:

- passwords
- JWTs
- refresh tokens
- CSRF tokens
- medical document text
- vector embeddings
- medical queries
- generated medical answers
- structured medical extraction contents

## Rate Limiting

The current development rate limiter is process-local.

This is appropriate for the current single-instance development
environment but is not a distributed production rate limiter.

A multi-instance deployment should use a shared rate-limit backend such
as Redis or an API gateway.

## Transport Encryption

Local development uses HTTP.

Production medical-data traffic must use TLS/HTTPS.

Secure cookies must be enabled in production.

HSTS should only be enabled once HTTPS is correctly configured.

## Encryption at Rest

The current application does not independently encrypt PostgreSQL data,
pgvector embeddings, uploaded files, or backups at the application
layer.

Production deployment must provide encryption at rest through the
storage/database infrastructure or a separately designed application
encryption layer.

Do not claim encryption at rest until that infrastructure has been
configured and verified.

## Secrets

Real credentials belong only in local or deployment secret storage.

Do not commit:

- .env
- JWT signing secrets
- database passwords
- Groq API keys
- Tavily API keys
- cloud credentials

.env.example must contain placeholders only.

## File Deletion

MIRA removes owned document database records and the corresponding
application-managed uploaded file.

Database/storage infrastructure may retain data through snapshots,
transaction logs, replicas, or backups.

Therefore application deletion must not be described as cryptographic
erasure of all historical copies.

## Retention

For the current development environment:

- use synthetic data only
- remove unnecessary test uploads
- do not create backups containing real patient information
- periodically remove expired/revoked refresh sessions
- define production retention periods before accepting real data

## Backups

Production backup design must define:

- encryption
- access controls
- retention duration
- restore testing
- deletion lifecycle
- auditability

This is deployment work and is not considered complete merely because
the application database is backed up.

## Compliance

These controls improve application security but do not establish
HIPAA compliance or any other regulatory certification.

Compliance depends on technical controls, infrastructure, operational
processes, organizational policies, agreements, risk assessments, and
ongoing verification.