# Production Hardening Checklist

## 1) Pull latest code

```bash
cd /root/autoviral
git pull origin cursor/mesin-scraper-autoviral-a805
```

## 2) Set environment secrets (recommended)

Tambahkan `.env` di `/root/autoviral/backend/.env`:

```env
SECRET_KEY=change-me-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
PAYMENT_WEBHOOK_SECRET=change-me-webhook-secret
ALLOWED_ORIGINS=https://synapsetech.my.id
DATABASE_URL=postgresql+psycopg2://autoviral:autoviral@postgres:5432/autoviral
```

## 3) Rebuild backend

```bash
cd /root/autoviral
docker compose down
docker compose up -d --build
```

## 4) Create first admin user

```bash
curl -X POST https://synapsetech.my.id/api/v1/users/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@synapsetech.my.id","full_name":"Admin","phone":"0812","password":"StrongPass123!"}'
```

User pertama otomatis role `admin`.

## 5) Login and get token

```bash
curl -X POST https://synapsetech.my.id/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@synapsetech.my.id&password=StrongPass123!'
```

Gunakan `access_token` untuk endpoint yang butuh auth.

## 6) Test protected endpoint

```bash
TOKEN="<paste_access_token>"
curl -H "Authorization: Bearer $TOKEN" https://synapsetech.my.id/api/v1/operations/summary
```

## 7) Webhook payment signature format

String yang di-hash:

```text
user_id|subscription_id|amount|provider|PAYMENT_WEBHOOK_SECRET
```

Header yang wajib dikirim:

```text
X-Signature: <sha256-hexdigest>
```

## 8) Backup routine

```bash
cd /root/autoviral
./backup/backup_postgres.sh
```

Restore:

```bash
./backup/restore_postgres.sh /root/autoviral/backups/autoviral_YYYYmmdd_HHMMSS.sql.gz
```

## 9) Monitor endpoint (scheduled health + backup)

Endpoint admin-only:

```bash
curl -H "Authorization: Bearer <TOKEN_ADMIN>" \
  https://synapsetech.my.id/api/v1/monitor/status
```

Respons memuat:
- status database
- status redis
- status backup terakhir (stale/tidak)

Contoh cron check (setiap 5 menit):

```cron
*/5 * * * * /usr/bin/curl -fsS -H "Authorization: Bearer <TOKEN_ADMIN>" https://synapsetech.my.id/api/v1/monitor/status > /dev/null || echo "monitor failed"
```
