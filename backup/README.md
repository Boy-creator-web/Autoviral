# Backup & Restore (Production Hardening)

Script backup/restore PostgreSQL untuk Autoviral.

## Backup database

```bash
cd /root/autoviral
./backup/backup_postgres.sh
```

Hasil backup tersimpan default di:

```text
/root/autoviral/backups/autoviral_YYYYmmdd_HHMMSS.sql.gz
```

Opsional:

```bash
BACKUP_DIR=/data/backups KEEP_COUNT=30 ./backup/backup_postgres.sh
```

## Restore database

```bash
cd /root/autoviral
./backup/restore_postgres.sh /root/autoviral/backups/autoviral_YYYYmmdd_HHMMSS.sql.gz
```

Script akan minta konfirmasi `yes` sebelum overwrite data.

## Saran cron backup harian

```bash
crontab -e
```

Tambahkan:

```cron
15 2 * * * cd /root/autoviral && /bin/bash ./backup/backup_postgres.sh >> /var/log/autoviral-backup.log 2>&1
```
