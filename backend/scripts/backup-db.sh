#!/bin/sh
# Shadow database backup script
# Run via cron or manually: ./backup-db.sh
set -e

BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/shadow_db}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."
pg_dump "$DB_URL" | gzip > "$BACKUP_DIR/shadow_db_${TIMESTAMP}.sql.gz"
echo "[$(date)] Backup complete: shadow_db_${TIMESTAMP}.sql.gz"

# Clean up old backups
find "$BACKUP_DIR" -name "shadow_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Cleaned backups older than ${RETENTION_DAYS} days"
