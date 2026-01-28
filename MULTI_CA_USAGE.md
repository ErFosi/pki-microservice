# Multi-CA Support - Usage Guide

## Overview

The PKI microservice now supports handling multiple Certificate Authorities (CAs). You can specify which CA to use when signing CSRs, and validation automatically detects the issuing CA from the certificate.

## Changes Made

### 1. CSR Signing (`POST /crt`)

**New Field:** `ca_common_name` (optional)

- **Purpose:** Specify which CA should sign the CSR
- **Type:** String (common name of the CA)
- **Behavior:**
  - If specified: Uses the CA with the matching common name
  - If not specified: Uses the first available CA (default behavior)

**Example Request:**
```json
{
  "csr": "-----BEGIN CERTIFICATE REQUEST-----\n...\n-----END CERTIFICATE REQUEST-----",
  "ca_common_name": "MyRootCA"
}
```

**Example Request (without specifying CA):**
```json
{
  "csr": "-----BEGIN CERTIFICATE REQUEST-----\n...\n-----END CERTIFICATE REQUEST-----"
}
```

### 2. Certificate Validation (`POST /validate`)

**New Field:** `ca_common_name` (optional)

- **Purpose:** Manually specify which CA to validate against
- **Type:** String (common name of the CA)
- **Behavior:**
  - If specified: Validates only against the specified CA
  - If not specified: **Automatically extracts the issuer's common name from the certificate** and uses that CA for validation
  - Fallback: If the issuer CA is not found in the database, validates against all available CAs

**Example Request (automatic detection):**
```json
{
  "crt": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
}
```

**Example Request (manual specification):**
```json
{
  "crt": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
  "ca_common_name": "MyRootCA"
}
```

## Why Common Name vs ID?

**Common Name** was chosen over ID because:

1. **User-Friendly:** More meaningful and memorable than numeric IDs
2. **Stable:** Common names are defined when creating the CA and don't change
3. **Self-Documenting:** Certificates already contain the issuer's common name
4. **API Clarity:** Makes API calls more readable and maintainable

## Testing the Changes

### 1. Create Multiple CAs

```bash
# Create first CA
curl -X POST http://localhost:8080/crypto/ca \
  -H "Content-Type: application/json" \
  -d '{
    "common_name": "RootCA-1"
  }'

# Create second CA
curl -X POST http://localhost:8080/crypto/ca \
  -H "Content-Type: application/json" \
  -d '{
    "common_name": "RootCA-2"
  }'
```

### 2. Sign CSR with Specific CA

```bash
# Sign with RootCA-1
curl -X POST http://localhost:8080/crypto/crt \
  -H "Content-Type: application/json" \
  -d '{
    "csr": "<YOUR_CSR_PEM>",
    "ca_common_name": "RootCA-1"
  }'

# Sign with RootCA-2
curl -X POST http://localhost:8080/crypto/crt \
  -H "Content-Type: application/json" \
  -d '{
    "csr": "<YOUR_CSR_PEM>",
    "ca_common_name": "RootCA-2"
  }'
```

### 3. Validate Certificate

```bash
# Automatic validation (extracts issuer from certificate)
curl -X POST http://localhost:8080/crypto/validate \
  -H "Content-Type: application/json" \
  -d '{
    "crt": "<YOUR_CERTIFICATE_PEM>"
  }'

# Manual validation (specify CA)
curl -X POST http://localhost:8080/crypto/validate \
  -H "Content-Type: application/json" \
  -d '{
    "crt": "<YOUR_CERTIFICATE_PEM>",
    "ca_common_name": "RootCA-1"
  }'
```

## Schema Changes

### schemas.py

```python
class CSRSignRequest(BaseModel):
    csr: str = Field(..., description="Certificate Signing Request en formato PEM")
    ca_common_name: str | None = Field(None, description="Common name de la CA que firmará el CSR")

class CertificateValidateRequest(BaseModel):
    crt: str = Field(..., description="Certificado en formato PEM a validar")
    ca_common_name: str | None = Field(None, description="Common name de la CA emisora")
```

## Error Handling

### Sign CSR Errors
- **404:** CA with specified common_name not found
- **404:** No CA available (if no common_name specified and no CAs exist)

### Validate Certificate Errors
- **404:** Specified CA not found (only if manually specified)
- **Invalid:** Certificate not valid (signature/expiry issues)
- **Revoked:** Certificate has been revoked

## Benefits

1. **Flexibility:** Support for multiple CAs in a single system
2. **Automatic Detection:** Validation intelligently determines the issuing CA
3. **Backwards Compatible:** Existing code without `ca_common_name` continues to work
4. **Explicit Control:** Can override automatic detection when needed
5. **Better Scalability:** Different services can use different CAs within the same PKI infrastructure
