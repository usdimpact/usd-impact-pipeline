# Score public archive — 2026-10-29 metadata-only inventory and preservation gate

**Scope:** review-only, historical evidence for [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155) and [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). Neither source-rights approval nor Production remediation. Snapshot anchored to protected main commit `19c75a5a517d508b27aa3e52b24a04d0870150be`; the inventory is not a mirror, backup or cache purge request.

## Findings verified from current Git tree

- `public/archive` contains **27 dated directories** (April 10–October 23, 2026). They contain **27** Score JSON, **14** weekly-input JSON, and **9** strict-reproduction JSON files: **50 dated Class C** artifacts.
- `public/data` contains **4** additional current Class C files; **54 current-tree Class C files total**, before separately categorized research diagnostics.
- `public/data/research` has one D aggregate/provenance file, one E robustness file and three F vintage-research files; provider/counsel may assign different handling by class. These are not counted within the 54.
- `data/weekly_input_*.json` contains **15** separate Git-only dated bridge files and should not be assumed hidden merely because Pages middleware does not serve the `data/` path.
- **Both historical index pages each list 23 dated prior issues.** Three dated directories present in Git are not listed: `2026-05-02`, `2026-05-09` and `2026-05-16`. The current `2026-10-23` issue is also absent from those *prior-history* indexes. This is a difference in the index scope versus the Git tree, not proof that the three releases should be reindexed or republished.
- An additional 54 dated EN/ES HTML files are present in Git; the current Pages premium HTML middleware denies anonymous/current Pages route access, which is not the same as removing these HTML files from Git.

The source snapshot is recorded in `governance/score-current-tree-exposure-inventory-2026-10-29.json`. Its offline regression test, `tests/test_score_current_tree_exposure_inventory.py`, checks **only path names, counts, and the controlling rights HOLD**. It never opens archived/market-data file bodies, calls providers, writes backup files, or changes data.

## Cloudflare deployment-history metadata and CI-artifact limits (read-only, 2026-10-29)

The Cloudflare Pages API's **77 deployment-listing pages** were fully enumerated in four read-only groups (pages 1–20, 21–40, 41–60, 61–77). All 77 requests succeeded and reported the same `total_count=1921`; each group reported no duplicate IDs **within that group**, and neighboring time windows were ordered consistently. The provider listing is not a transactional snapshot across calls, so do not claim stronger historical consistency than the available API evidence.

| Deployment-listing metadata | Count |
|---|---:|
| Total Pages deployment records | **1,921** |
| `environment=preview` | **1,678** |
| `environment=production` | **243** |
| `latest_stage.status=success` | **1,340** |
| `latest_stage.status=idle` | **559** |
| `latest_stage.status=failure` | **12** |
| `latest_stage.status=skipped` | **10** |
| Pages successfully enumerated | **77 / 77** |
| Earliest recorded deployment timestamp | **2026-04-10 17:44:11 UTC** |
| Latest observed deployment timestamp | **2026-10-29 18:22:31 UTC** |

The counts reconcile: environments 1,678 + 243 = 1,921, and statuses 1,340 + 559 + 12 + 10 = 1,921. They represent **deployment records**, not 1,921 public disclosure incidents, active historical URLs, distinct website versions, legally restricted objects or cache copies. No historical response content was fetched by this metadata audit. The canonical successful Pages Production deployment is a separate current project setting; a newly created **idle** production record does not imply a new live release.

**Access scope:** The active Cloudflare Access policy was independently verified against sampled historical preview hostnames, but it does **not** protect the root `usd-impact-pipeline.pages.dev` or custom `score.usd-impact.com` domains. This inventory does not establish reachability/denial for every prior preview hash or any cached historical response. A future approved audit should stratify by successful/production deployments, branch and source-era, then test *headers/status only* using a privacy- and rights-reviewed sampling protocol.

**GitHub Actions metadata limitation:** Known [pre-HOLD release run #40044029286](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40044029286) and [synthetic write run #40617195348](https://github.com/usdimpact/usd-impact-pipeline/actions/runs/40617195348) returned **zero downloadable Actions artifacts** through the run-level artifacts endpoint. The connector disallowed repository-wide Actions artifact and cache listing. Therefore cached dependencies, logs and unsampled runs **cannot** be classified as cleared or fully enumerated. Two zero-artifact samples do not imply expired/deleted historical files.

**Remediation boundary:** This metadata audit does not authorize Pages deployment deletion, Access-policy changes, Git history rewrite, CDN purge, source/provider retrieval, additional retention copies or Production rollout. Preserve current canonical deployment and maintain the Score publication HOLD while provider/counsel decides the permitted public/private and historical treatment.

## Required preservation and restore sequencing before any eventual cleanup

1. **Rights gate first.** Obtain provider/counsel instructions by source and field class: whether commercial internal historical retention, reproduced private evidence, aggregates, derivatives and external dissemination are permitted. If permission is absent, do not duplicate provider data to create a new backup. A hash-only/count-only metadata snapshot is not permission to retain restricted content.
2. **Freeze a reproducibility and access map** describing provider-origin artifacts, downstream consumer routes, exact Git revision and immutable archive dates. Keep historic snapshot metadata/version and explicit unknowns. No overwrites or history rewrite.
3. **Choose a lawful preservation boundary** before redaction: approved private storage, encryption/access audit, allowable retention and deletion schedule, proof of exact-byte transfer only where retention rights are cleared. Do not assume that Development's synthetic-only bucket is licensed for real provider evidence.
4. **Publish no new public component values while HOLD**. Validate aggregate-only schema and all research consumers against synthetic test data. Where legally allowed, migrate strict evidence privately **before** narrowing public outputs.
5. **Prepare a two-phase Production change**: separately approved candidate and rollback candidate, exact-head CI, baseline deployment ID, current root-domain/preview/source blob inventory, verified independent member login and anonymous endpoint matrix. Do not change the existing Cloudflare Access policy incidentally.
6. **Deploy only under explicit Production authorization**, confirm old Class C/E/F paths no longer leak restricted values, check main and legacy root domains, preview hashes and CDN response behavior. CDN invalidation is a separate approved action; never treat a future build as sufficient to invalidate old copies.
7. **Rollback must remain legally safe**: reverting the website or functionality must not automatically restore restricted public provider-derived artifacts. If a release fails, prefer a publication-off/aggregate-only fallback with preserved, rights-approved private evidence; do not republish old Class C files solely to fix an outage.
8. **Git history and mirrors are a separate decision**. Rewriting commits or taking the repo private is not the first containment step, does not erase clones, and may impair research, CI and member site. Approve only after counsel and an off-platform backup/restore plan suitable for restricted source material.

## Gate outcomes

| Gate | Current state |
|---|---|
| GitHub current-tree metadata and three index omissions | **Documented** |
| Development synthetic-only write/read, immutable reject and locked-reader acceptance | **Passed in separate tests** |
| Rights to retain or copy real provider-derived archive evidence | **Not established** |
| All historical Git objects, external mirrors, Cloudflare old deployments, CDN, and backups inventoried | **Not complete** |
| Public aggregate-only output schema accepted by provider/counsel and website readers | **Pending** |
| Production roll-forward + legal-safe rollback approved | **No** |
| Score publication | **HOLD** |

## Non-action statement

No existing public page/index, CSV/JSON artifact, Git history, Cloudflare deployment, Supabase object, license, paid service, auth policy, Score formula, data feed or Production environment has been changed by this documentation and offline test candidate.
