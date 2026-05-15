---
description: Build the site and rsync to the Hetzner static host. Requires HETZNER_* env vars or explicit override. Asks before touching the remote.
---

# /deploy

Manual deploy. Normally GitHub Actions handles this; use this skill only when you
need to push outside the regular flow.

## Pre-flight

1. Check env or `.env`:
   - `HETZNER_HOST`, `HETZNER_USER`, `HETZNER_PATH`
2. Confirm working tree is clean. If not, ask whether to deploy from current state anyway.
3. Show the user:
   - target host + path
   - current git HEAD (short SHA + subject)
   - `pnpm build` summary (file count, total size)

## Build

```bash
pnpm install --frozen-lockfile
pnpm build
```

If `astro build` fails, stop. Don't ship a broken site.

## Confirm

Ask the user explicitly: "Deploy `<sha>` to `<host>:<path>`?" — accept only `yes`.

## Deploy

```bash
rsync -avz --delete dist/ "$HETZNER_USER@$HETZNER_HOST:$HETZNER_PATH/"
```

Then ping `https://<host>/` once and report the status code.

## Don't

- Don't deploy without explicit `yes`.
- Don't deploy a build that hasn't completed cleanly.
- Don't `rsync --delete` if `HETZNER_PATH` is `/` or empty (sanity-check before running).
