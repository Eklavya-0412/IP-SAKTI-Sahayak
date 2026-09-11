#!/bin/sh
set -eu
# Run from repository root. Store backups on encrypted storage.
destination="${1:?Usage: scripts/backup.sh /encrypted/backup/directory}"
mkdir -p "$destination"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose exec -T db pg_dump -U ipsakti -d ipsakti -Fc > "$destination/database-$stamp.dump"
docker compose exec -T api tar -czf - -C /app/data . > "$destination/documents-$stamp.tar.gz"
printf 'Backup pair written with stamp %s. Retain at most 30 days; restrict directory access.\n' "$stamp"
