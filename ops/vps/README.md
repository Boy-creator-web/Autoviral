# VPS Ops: Backup, Recovery, Healthcheck

Panduan ini untuk operasi cepat di VPS agar saat crash bisa recovery dengan cepat.

## 1) File yang disediakan

- `ops/vps/backup_autoviral.sh`
  - Backup PostgreSQL (`autoviral` + `postiz`)
  - Backup source code `/root/autoviral` (tar.gz)
  - Backup uploads Postiz (`/uploads`)
  - Simpan metadata Docker + env runtime container
  - Retention default: hapus backup > 14 hari

- `ops/vps/recover_autoviral.sh`
  - Restore DB dari backup
  - Restore uploads Postiz
  - Start ulang Postiz jika sempat dihentikan saat restore

- `ops/vps/install_backup_cron.sh`
  - Pasang cron harian untuk backup otomatis

- `ops/vps/healthcheck_stack.sh`
  - Cek container + endpoint utama

- `ops/vps/hardening_apply.sh`
  - Hardening baseline VPS:
    - UFW allow: SSH, `8000`, `4007`
    - deny internal port publik (`5432`, `6379`, `5001`, `3000`, `7233`, `8080`, `8969`)
    - tambah rule `DOCKER-USER` untuk block port internal yang dipublish Docker
    - rotate `SECRET_KEY` backend bila masih default
    - disable docs (`DOCS_ENABLED=false`)
    - aktifkan API key protection (`API_KEY_REQUIRED=true`)

- `ops/vps/hardening_verify.sh`
  - Verifikasi hasil hardening (port exposure, docs off, auth check)

- `ops/vps/hardening_phase2_apply.sh`
  - Hardening perimeter:
    - pasang Nginx reverse proxy untuk backend (`/` -> `127.0.0.1:8000`)
    - rate limiting + connection limiting
    - pasang fail2ban jail untuk abuse `401`/`429`

- `ops/vps/hardening_phase2_verify.sh`
  - Verifikasi service Nginx/fail2ban + proteksi API via reverse proxy

## 2) Lokasi backup

Default backup disimpan di:

```bash
/root/autoviral-backups/<timestamp>/
```

## 3) Menjalankan backup manual

Di VPS:

```bash
chmod +x /root/autoviral/ops/vps/*.sh
/root/autoviral/ops/vps/backup_autoviral.sh
```

Opsional override retention:

```bash
RETENTION_DAYS=30 /root/autoviral/ops/vps/backup_autoviral.sh
```

## 4) Pasang backup otomatis (cron)

Default: tiap hari jam 02:30 UTC.

```bash
chmod +x /root/autoviral/ops/vps/install_backup_cron.sh
/root/autoviral/ops/vps/install_backup_cron.sh
```

Custom schedule:

```bash
CRON_SCHEDULE="0 */6 * * *" /root/autoviral/ops/vps/install_backup_cron.sh
```

## 5) Cek kesehatan stack

```bash
chmod +x /root/autoviral/ops/vps/healthcheck_stack.sh
/root/autoviral/ops/vps/healthcheck_stack.sh
```

## 6) Hardening keamanan baseline (disarankan)

Jalankan sekali:

```bash
chmod +x /root/autoviral/ops/vps/hardening_apply.sh
/root/autoviral/ops/vps/hardening_apply.sh
```

Lalu verifikasi:

```bash
chmod +x /root/autoviral/ops/vps/hardening_verify.sh
/root/autoviral/ops/vps/hardening_verify.sh
```

Catatan:
- Script hardening menyimpan API key backend yang digenerate otomatis ke:
  - `/root/autoviral-secrets.env`
- Gunakan nilainya pada header request:
  - `X-API-Key: <AUTOVIRAL_API_KEY>`

## 7) Recovery cepat saat crash

### Restore dari backup terbaru

```bash
chmod +x /root/autoviral/ops/vps/recover_autoviral.sh
/root/autoviral/ops/vps/recover_autoviral.sh
```

### Restore dari backup tertentu

```bash
/root/autoviral/ops/vps/recover_autoviral.sh 20260330T120000Z
```

## 8) Catatan penting

- Script recovery mengasumsikan container DB sudah running.
- Untuk data Postiz, restore uploads menggunakan volume `postiz_uploads`.
- Simpan backup off-site juga (mis. object storage) untuk DR yang lebih aman.

## 9) Hardening tahap 2 (Nginx + Fail2ban)

Jalankan:

```bash
chmod +x /root/autoviral/ops/vps/hardening_phase2_apply.sh
/root/autoviral/ops/vps/hardening_phase2_apply.sh
```

Verifikasi:

```bash
chmod +x /root/autoviral/ops/vps/hardening_phase2_verify.sh
/root/autoviral/ops/vps/hardening_phase2_verify.sh
```
