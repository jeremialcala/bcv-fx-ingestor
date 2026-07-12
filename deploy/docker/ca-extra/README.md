# CA intermedia vendorizada

`sectigo-public-server-authentication-ca-dv-r36.crt` es el certificado **intermedio
público** de Sectigo que emite el certificado hoja de `www.bcv.org.ve`.

**Por qué está aquí:** el servidor del BCV envía una cadena TLS incompleta (adjunta un
intermedio de otra CA). En Windows el verificador del SO resuelve el intermedio correcto
vía AIA, pero OpenSSL (Linux / contenedor) no hace AIA fetching, así que la descarga
fallaría dentro de la imagen. Se añade el intermedio al almacén del contenedor
(`update-ca-certificates`) para compensar la mala configuración del servidor.

**Esto NO debilita la política TLS (ADR-0004):** la verificación sigue siendo estricta —
la cadena debe terminar en una raíz de confianza del sistema ("Sectigo Public Server
Authentication Root R46", incluida en los bundles estándar); solo se aporta el eslabón
que el servidor debería enviar.

Identidad del certificado (verificada 2026-07-12, obtenido del URI CA Issuers del AIA
del certificado hoja: `http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt`):

- Subject: `C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication CA DV R36`
- Issuer: `C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication Root R46`
- Vigencia: 2021-03-22 → 2036-03-21
- SHA-256: `8C:54:C3:34:B6:6B:A4:E4:26:77:2A:F4:A3:F9:13:6C:19:A1:AE:C7:29:FD:B2:8C:53:5C:07:A5:A4:EF:22:E0`

Si el BCV rota a otra CA emisora, actualizar este archivo (runbook en
`docs/05-deployment/deployment.md`).
