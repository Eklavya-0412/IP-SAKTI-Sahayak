#!/bin/sh
set -eu
# Restore into a separate database only, never overwrite the running pilot.
archive="${1:?Usage: scripts/restore-check.sh /path/database.dump}"
docker compose exec -T db createdb -U ipsakti ipsakti_restore_check
docker compose exec -T db pg_restore -U ipsakti -d ipsakti_restore_check --no-owner --exit-on-error < "$archive"
docker compose exec -T db psql -U ipsakti -d ipsakti_restore_check -c 'SELECT count(*) AS source_versions FROM source_versions;'
printf 'Restore check succeeded. Inspect ipsakti_restore_check, then remove it explicitly.\n'
