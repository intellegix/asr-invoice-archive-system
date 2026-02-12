# Code Signing for ASR Production Server EXE

## Overview

Windows Authenticode code signing eliminates "Unknown Publisher" warnings
and verifies the EXE has not been tampered with after build.

## Prerequisites

1. **Code Signing Certificate** — purchase from a trusted CA (DigiCert,
   Sectigo, GlobalSign). EV certificates are recommended for SmartScreen
   reputation.
2. **SignTool** — included with the Windows SDK
   (`C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe`).

## Signing Steps

```powershell
# 1. Build the EXE
python build_production_server.py

# 2. Sign the EXE (certificate stored in Windows certificate store)
signtool sign /tr http://timestamp.digicert.com /td sha256 ^
  /fd sha256 /a dist\ASR_Production_Server\ASR_Production_Server.exe

# 3. Verify the signature
signtool verify /pa /v dist\ASR_Production_Server\ASR_Production_Server.exe
```

## CI Integration

Store the `.pfx` certificate as a GitHub Actions secret
(`CODE_SIGNING_CERT_BASE64` + `CODE_SIGNING_PASSWORD`) and decode it in
the build workflow:

```yaml
- name: Sign EXE
  if: runner.os == 'Windows'
  run: |
    echo ${{ secrets.CODE_SIGNING_CERT_BASE64 }} | base64 -d > cert.pfx
    signtool sign /f cert.pfx /p ${{ secrets.CODE_SIGNING_PASSWORD }} \
      /tr http://timestamp.digicert.com /td sha256 /fd sha256 \
      dist/ASR_Production_Server/ASR_Production_Server.exe
    rm cert.pfx
```

## Status

- [ ] Purchase code signing certificate
- [ ] Add certificate to GitHub Secrets
- [ ] Add signing step to CI workflow
