# usd-impact-pipeline
USD Impact Score weekly pipeline

## Publication workflow

The score, deterministic English and Spanish commentary, dashboards, bridge data, and dated archive are generated every Friday at 22:00 UTC.

Generated releases are committed to an automation branch and merged into `main` only after the exact publication commit passes the `Weekly score quality` workflow. Cloudflare Pages deploys the validated `main` branch. Failed generation or validation leaves the current production release unchanged.

The Saturday health workflow verifies the completed GitHub Actions release, deployed bridge JSON, and both public dashboards.

## Connection to usd-impact

This repository prepares and publishes the weekly USD Impact score/data pipeline used by the main USD Impact website.

Expected bridge output:

```text
data/weekly_input_YYYY-MM-DD.json
```
