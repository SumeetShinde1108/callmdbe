# Accounts API Documentation

Base URL prefix: `/api/v1/auth/`

Auth: Bearer JWT in `Authorization: Bearer <access>` header unless endpoint is public.

## Contents
- Register
- Email Verification
- Login (Email/Password)
- Login (Google OAuth id_token)
- Token Refresh
- Me (Profile)
- Password Reset (Request + Confirm)
- TOTP 2FA (Enable, Verify, Disable)
- Domain Restriction and Audit Logging

---

## Register
- **URL**: `POST /api/v1/auth/register/`
- **Auth**: Public
- **Body**:
```json
{
  "email": "user@example.com",
  "name": "Test User",
  "password": "StrongPass!234",
  "password2": "StrongPass!234"
}
```
- **Response 201**:
```json
{
  "detail": "Registration successful. Please verify your email to activate your account.",
  "email_verification_token": "<only-in-DEBUG>"
}
```
- **Notes**:
  - Users are created inactive until email verification.
  - In DEBUG, token is returned for testing.

## Email Verification
- **URL**: `POST /api/v1/auth/verify-email/`
- **Auth**: Public
- **Body**:
```json
{ "token": "<email_verification_token>" }
```
- **Response 200**:
```json
{ "detail": "Email verified. You can now log in." }
```

## Login (Email/Password)
- **URL**: `POST /api/v1/auth/login/`
- **Auth**: Public
- **Body**:
```json
{ "email": "user@example.com", "password": "StrongPass!234" }
```
- **Response 200**:
```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "id": "<uuid>",
  "email": "user@example.com",
  "name": "Test User",
  "company": "",
  "job_title": "",
  "phone": "",
  "date_joined": "2025-10-01T12:34:56Z"
}
```
- **Errors**:
  - 400: `{"non_field_errors": ["Account is inactive. Please verify your email."]}` if not verified.

## Login (Google OAuth id_token)
- **URL**: `POST /api/v1/auth/login/google/`
- **Auth**: Public
- **Body**:
```json
{ "id_token": "<google_id_token_from_client>" }
```
- **Response 200**:
```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "id": "<uuid>",
  "email": "googleuser@example.com",
  "name": "Google User",
  "company": "",
  "job_title": "",
  "phone": "",
  "date_joined": "2025-10-01T12:34:56Z"
}
```
- **Notes**:
  - Validates `id_token` via Google tokeninfo; enforces `aud` matches configured client ID if set.
  - Auto-creates user if not found, sets `is_active=True` (Google verified email).
  - Subject (`sub`) is validated but not persisted unless you extend the model.

## Token Refresh
- **URL**: `POST /api/v1/auth/token/refresh/`
- **Auth**: Public
- **Body**:
```json
{ "refresh": "<jwt>" }
```
- **Response 200**:
```json
{ "access": "<new_access_jwt>" }
```

## Me (Profile)
- **URL**: `GET /api/v1/auth/me/`
- **Auth**: Bearer token
- **Response 200**:
```json
{
  "id": "<uuid>",
  "email": "user@example.com",
  "name": "Test User",
  "company": "",
  "job_title": "",
  "phone": "",
  "date_joined": "2025-10-01T12:34:56Z"
}
```

## Password Reset

### Request
- **URL**: `POST /api/v1/auth/password/reset/`
- **Auth**: Public
- **Body**:
```json
{ "email": "user@example.com" }
```
- **Response 200**:
```json
{ "detail": "If an account with that email exists, a password reset link has been sent." }
```
- **Notes**: In DEBUG, the response includes `uid` and `token` for testing:
```json
{ "detail": "...", "uid": "<uidb64>", "token": "<token>" }
```

### Confirm
- **URL**: `POST /api/v1/auth/password/reset/confirm/`
- **Auth**: Public
- **Body**:
```json
{
  "uid": "<uidb64>",
  "token": "<token>",
  "new_password": "NewPass!234",
  "new_password2": "NewPass!234"
}
```
- **Response 200**:
```json
{ "detail": "Password has been reset successfully." }
```

## TOTP 2FA

### Enable
- **URL**: `POST /api/v1/auth/2fa/totp/enable/`
- **Auth**: Bearer token
- **Response 200**:
```json
{ "device_id": 1, "provisioning_uri": "otpauth://totp/..." }
```
- **Notes**: `provisioning_uri` may be present depending on device implementation.

### Verify
- **URL**: `POST /api/v1/auth/2fa/totp/verify/`
- **Auth**: Bearer token
- **Body**:
```json
{ "code": "123456" }
```
- **Response 200**:
```json
{ "detail": "2FA enabled." }
```
- **Error 400**: `{ "detail": "Invalid code." }`

### Disable
- **URL**: `POST /api/v1/auth/2fa/totp/disable/`
- **Auth**: Bearer token
- **Response 200**:
```json
{ "detail": "2FA disabled." }
```

## Domain Restriction and Audit Logging
- **Domain restriction**: If any active entries exist in `AllowedEmailDomain`, Google logins are limited to those domains. Otherwise, all domains are allowed.
  - Error when blocked: HTTP 403 `{ "detail": "Email domain not allowed." }`
- **Audit logging**: Every Google login attempt is recorded in `GoogleSignInAudit` with `email`, `domain`, `success`, `reason`, `ip`, `user_agent`, and timestamp.

## Common Headers
- JSON requests: `Content-Type: application/json`
- Authenticated: `Authorization: Bearer <access>`

## Error Format
- Validation error (400):
```json
{ "field": ["message"], "non_field_errors": ["message"] }
```
- Unauthorized (401): missing/invalid token.
- Forbidden (403): domain restriction.

## cURL Examples

Login (email/password):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"StrongPass!234"}'
```

Me:
```bash
curl -X GET http://127.0.0.1:8000/api/v1/auth/me/ \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

Password Reset Request:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/password/reset/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com"}'
```
