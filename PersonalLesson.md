# Personal Lessons — E-commerce Project (from git history)

Lessons extracted from real production bugs during the Render deployment (Oct-Nov 2026).

## Lesson 1: ALLOWED_HOSTS and env-var drift between dev and prod
Commits 71d9b6, a700bdd: hardcoded ALLOWED_HOSTS and restructured the start command.

- Symptom: app boots locally but 400s / fails health check on Render.
- Root cause: localhost-style config (or empty env vars) doesn't exist in the container.
- Lesson: production config must come from a single source of truth. Keep an
  env var contract (DJANGO_ALLOWED_HOSTS, DJANGO_DEBUG, etc.) and set them in
  the platform dashboard or render.yaml. Test with DEBUG=False LOCALLY before
  pushing — most prod failures are reproducible at home in one command:
  `DJANGO_DEBUG=False python manage.py runserver`.

## Lesson 2: Static files 404 in production (Unfold CSS missing)
Commit c154a6e: added WhiteNoise middleware + CompressedManifestStaticFilesStorage.

- Symptom: site loads but is unstyled on Render — admin CSS (Unfold) 404s.
- Root cause: runserver serves static files automatically; gunicorn does NOT.
  Django only serves STATIC_ROOT when collectstatic has run and something
  (WhiteNoise, nginx, or a CDN) is configured to serve it.
- Lesson: "it worked in dev" is meaningless for static files. The checklist:
  whitenoise in MIDDLEWARE (right after SecurityMiddleware), STATIC_ROOT set,
  collectstatic in the build/start pipeline, STORAGES with CompressedManifest
  for hashed filenames. Verify by hard-refreshing the deployed admin page.

## Lesson 3: Same object, two shapes — dev API object vs prod webhook dict
Commit 60a4e4b: `session_id = session['id'] if isinstance(session, dict) else session.id`

- Symptom: Stripe checkout works in dev, but the webhook that marks orders
  paid crashes on Render.
- Root cause: with `stripe listen` locally, `event['data']['object']` is a
  Stripe SDK object (attribute access: session.id). Real production webhooks
  POST raw JSON — it's a plain dict (key access: session['id']).
- Lesson: never assume library objects at a trust boundary. Webhooks receive
  deserialized JSON, not SDK instances. Defensive shape handling:
  `isinstance(x, dict)` then key access, else attribute access. Same class of
  bug as SQLite hiding what Postgres exposes: the dev environment silently
  differs from prod, so the bug only fires where you can't see it.
- Also: Stripe webhooks need the raw body — the view must use
  `stripe.Webhook.construct_event` for signature verification, and nothing
  (middleware, parsers) can consume request.body first.

## Lesson 4: Procfile vs render.yaml — one deployment entry point
Commits 71d9b6, a700bdd: migrate + seed_data moved into the start command.

- On Render, migrations and data seeding must run before gunicorn binds.
  Either use a release command or chain them in startCommand:
  `python manage.py migrate && python manage.py seed_data && gunicorn ...`
- Lesson: pick ONE deployment config file and treat it as the source of truth.
  Having both Procfile and render.yaml risks them drifting apart — which is
  exactly what happened here.
- TODO: seed_data.py creates a superuser with hardcoded admin/admin123 —
  fine for a demo, unacceptable for anything user-facing. Env-var the
  credentials before this repo goes on a portfolio README link.
