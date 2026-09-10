# Deployment and operations runbook

## Installation

Run `python scripts/configure.py`, then `docker compose up -d --build`. The configuration generator refuses to overwrite an existing file and never prints secrets. Use `docker compose ps` and `docker compose logs --tail=100 api worker migrate` to diagnose startup. Health requires a reachable database. Nginx serves the built client and proxies `/api/`.

For this workspace's rehearsal use `--env-file .env.docker` on every Compose command. Do not copy that file into a submission or commit it. For a fresh deployment create a new `.env`. Configure a real HTTPS `PUBLIC_ORIGIN`, `COOKIE_SECURE=true` and `APP_ENV=production` before exposing the app. `deploy/Caddyfile.example` shows TLS termination; the owner supplies domain, certificate configuration and hosting.

## Corpus release procedure

1. Generate the manifest: `python scripts/build_manifest.py`.
2. Acquire local PDFs and remote candidates using the CLI. `--pending` skips sources that already have chunks. The worker checks public sources daily; it does not automatically activate changes.
3. Inspect actual snapshot contents, publisher provenance, checksum, extraction quality, effective dates, amendment relationships and access conditions. Empty or inaccessible sources cannot support answers.
4. Use `python -m app.cli ocr --source SOURCE_ID` inside the container for sparse/scanned pages. OCR appends new recovered chunks, preserving previous identifiers. A curator must inspect recovery quality. Approved extractions cannot be changed through this command.
5. For discovery only, `reference-release` creates a visibly reference-only release. To enable generated legal information, a qualified curator must review source applicability and set approved status with a meaningful note. Drafts, notices, statistics and forms cannot become governing answer authority.
6. Run benchmark and focused regression tests. Review source/version changes and record results with the release note. Select at most one version per source and activate the candidate release through the admin interface.
7. Roll back by activating the prior release. Do not delete source snapshots that existing citations reference. A withdrawn source must be marked rejected and the replacement release activated.

Source statuses can change after a release; saved traces preserve IDs but current eligibility is deliberately reevaluated. Full historical legal reconstruction needs the review audit and source snapshots, not a current source status alone.

## Backups and recovery

`scripts/backup.sh /encrypted/backup/directory` writes a custom-format PostgreSQL dump and paired document archive. Run from a shell with Docker access. In rehearsal export `ENV_FILE=.env.docker` and use equivalent `docker compose --env-file .env.docker` commands. On Windows, the Python rehearsal script provides a binary-safe backup/restore check.

Store both files together, restrict access and encrypt backups. Retain backups for no more than the documented 30-day operational default unless a reviewed legal retention requirement applies. Schedule rotation with the deployment's backup system; this project does not provision an external backup service. Record checksum, timestamp and release ID. Test restoration into an isolated database and document volume before relying on the backup.

`scripts/restore-check.sh database.dump` restores into `ipsakti_restore_check` and never overwrites the live database. An existing restore-check database causes the command to stop. Verify source counts, cases, permissions and document checksums before a production recovery. After recovery reapply deletion requests and consent revocations that postdate the backup. Explicitly retire the isolated restore database when finished.

## Incident handling

For suspected leakage, disable hosted generation and external language processing, restrict ingress, preserve content-minimized audit evidence, rotate affected credentials and invalidate sessions. Identify affected cases and connector consents, investigate the actual data path and involve the designated privacy/security owner. The owner determines applicable notification obligations and deadlines with qualified counsel. Do not place raw case documents in issue trackers or general logs.

## Retention and availability

The worker purges expired sessions (guest default 24 hours), inactive cases (90 days), associated files and aged traces/audits (365-day configurable operational default). Raw audio is processed in memory and is not deliberately persisted. These defaults are product choices pending legal review. Database and archive backups must follow their own expiry schedule.

Provider outages, quotas and missing credentials fall back to source excerpts or explicit unavailability. Registry CAPTCHA requires user navigation. Paid connectors have no live implementation until a subscription and permitted interface are supplied. Do not bypass access controls.

## Upgrade checklist

Back up; rebuild pinned dependencies; apply migrations; run tests; review OpenAPI changes; regenerate frontend types; run the benchmark against the candidate corpus; inspect language and jurisdiction behavior; smoke-test on the intended hardware; record limitations. Dependency and container pins require deliberate security updates. Never activate a new legal corpus merely because acquisition succeeded.
