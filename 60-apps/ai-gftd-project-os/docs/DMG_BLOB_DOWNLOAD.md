# os.etzhayyim.com DMG Blob Download

`os-ui-6s80i2ya` now serves installer downloads from App `wasi:blobstore`:

- Download endpoint: `GET /download/{filename}`
- List endpoint: `GET /api/downloads`
- Upload endpoint (admin): `PUT /api/downloads/{filename}`
  - Header: `X-GFTD-Upload-Token: <token>`
  - Token config key: `OS_DMGS_UPLOAD_TOKEN`

## Upload Example

```bash
curl -X PUT \
  -H "X-GFTD-Upload-Token: ${OS_DMGS_UPLOAD_TOKEN}" \
  --data-binary @GFTD-OS_0.1.0_aarch64.dmg \
  https://os.etzhayyim.com/api/downloads/GFTD-OS_0.1.0_aarch64.dmg
```

## Download Example

```bash
curl -L -o GFTD-OS_0.1.0_aarch64.dmg \
  https://os.etzhayyim.com/download/GFTD-OS_0.1.0_aarch64.dmg
```
