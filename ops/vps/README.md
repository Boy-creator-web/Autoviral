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

## 6) Recovery cepat saat crash

### Restore dari backup terbaru

```bash
chmod +x /root/autoviral/ops/vps/recover_autoviral.sh
/root/autoviral/ops/vps/recover_autoviral.sh
```

### Restore dari backup tertentu

```bash
/root/autoviral/ops/vps/recover_autoviral.sh 20260330T120000Z
```

## 7) Catatan penting

- Script recovery mengasumsikan container DB sudah running.
- Untuk data Postiz, restore uploads menggunakan volume `postiz_uploads`.
- Simpan backup off-site juga (mis. object storage) untuk DR yang lebih aman.
