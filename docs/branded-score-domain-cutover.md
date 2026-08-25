# Branded Score domain cutover

## Target

- Branded origin: `https://score.usd-impact.com`
- Existing production Pages origin: `https://usd-impact-pipeline.pages.dev`
- Cloudflare Pages project: `usd-impact-pipeline`

This change is branding and infrastructure only. It must not alter Score calculation, publication history, methodology, source provenance, archives, or research artifacts.

## Safety rule

Do not replace public website links or iframe sources until Cloudflare reports the custom domain as active and the read-only `Branded Score domain readiness` workflow passes against the branded origin.

The legacy `pages.dev` origin must remain available during the migration so historical links and reproducibility references do not break.

## Cloudflare association

Use the Cloudflare Pages custom-domain flow for the existing `usd-impact-pipeline` Pages project:

1. Open Workers & Pages in the authenticated Cloudflare account.
2. Select the `usd-impact-pipeline` Pages project.
3. Open **Custom domains**.
4. Select **Set up a domain**.
5. Enter exactly `score.usd-impact.com`.
6. Continue through activation.
7. If `usd-impact.com` is already a zone in the same Cloudflare account, allow Cloudflare to create the required DNS record automatically.
8. If DNS is hosted elsewhere, first associate the custom domain in Pages and then create the requested CNAME. Do not create only a manual CNAME without the Pages association.
9. Wait for the Pages custom-domain status to become **Active** and for HTTPS certificate issuance to complete.

Do not disable or redirect `usd-impact-pipeline.pages.dev` at this stage.

## Read-only verification

After Cloudflare reports `score.usd-impact.com` as active, run:

**Actions → Branded Score domain readiness → Run workflow**

Use the default origin `https://score.usd-impact.com`.

The workflow fails closed unless all of these conditions pass:

- the requested origin is exactly the approved branded hostname;
- the existing `pages.dev` origin still returns HTTP 200;
- the branded origin returns HTTP 200;
- the branded request does not redirect back to `pages.dev`;
- the branded and legacy origins return byte-equivalent content for the checked static artifacts;
- the English dashboard contains the expected USD Impact Score marker;
- security headers remain present;
- CSP continues to allow framing only by the USD Impact site origins already approved in the Pages security policy.

The checked paths are:

- `/en/`
- `/archive/en/`
- `/data/research/score_v2_vintage_comparison_latest.html`
- `/data/research/score_v2_vintage_comparison_latest.json`
- `/data/research/score_v2_vintage_comparison_latest.csv`
- `/data/score_v2_data_semantics.json`
- `/data/weekly_input_latest.json`

A passing run means only **ready for website cutover review**. It does not mutate DNS, Pages, the repository, deployments, or production data.

## Website cutover

After the readiness workflow passes:

1. Change the USD Impact website's Score-pipeline origin to `https://score.usd-impact.com` in one bounded pull request or validated build-time setting.
2. Update the main Score dashboard, archive links, revision-audit links, data-semantics links, About/Transparency references, methodology references, and any current weekly-report external links intended to use the branded host.
3. Update the website CSP narrowly for the branded frame origin. Do not weaken unrelated CSP directives.
4. Preserve historical `pages.dev` compatibility or redirects.
5. Run the full website Web quality, CodeQL, dependency review, and Preview visual verification before merge.
6. Verify the live USD Impact Score iframe, standalone dashboard, archive, JSON/CSV research artifacts, and methodology links after deployment.

## Rollback

If the branded origin or website cutover fails:

- keep or restore the website references to `https://usd-impact-pipeline.pages.dev`;
- leave the published Score artifacts and history unchanged;
- do not delete the Pages project or historical archives;
- correct the Cloudflare custom-domain/DNS issue separately and rerun the readiness workflow.

The migration is complete only when the branded origin and website integration are both verified, while the legacy origin remains non-destructive for old links.
