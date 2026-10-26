# Frozen research residual-risk review — 2026-10-26

## Decision scope

This review covers newly disclosed dependency findings in the immutable root `requirements.lock` used only by frozen prospective research and historical-release provenance.

It does **not** authorize rewriting that lock, changing Score formulas, changing research preregistration, changing provider data, or deploying application code.

## Active online runtime

The active runtime lock is patched in this security candidate:

- `certifi 2026.7.22 -> 2026.10.23`
- `Pillow 12.3.0 -> 13.0.0`

The active online environment must pass `pip-audit` with no known findings before release.

## Frozen historical/research lock

The root `requirements.lock` remains byte-identical at SHA-256:

`a4c6fb90909a04eb267057d3e31049c7fc38b12e8a7d556e79c0141aa0d52db6`

Newly disclosed findings are accepted only inside the existing isolated frozen-research boundary through **2026-11-05**. The expiry is not extended by this review.

The exact-match audit remains fail-closed: any added, removed, or changed finding requires another review.

## Isolation evidence

The repository's frozen-research contract provides all of the following:

- build networking disabled when frozen wheels are installed;
- runtime networking disabled;
- read-only container root;
- all Linux capabilities dropped;
- `no-new-privileges` enabled;
- non-root runtime UID;
- resource bounds;
- only two preregistered modes are dispatchable;
- only preregistered append-only research paths may leave the worker;
- frozen research consumes already-published reproduction bundles rather than refetching providers.

The two frozen ingestion modes do not contain live provider fetch paths. They do not invoke image opening or chart rendering. Pillow is present transitively for the frozen environment but the reviewed prospective ingestion paths do not exercise its image decoders/encoders.

## Newly reviewed advisory classes

### certifi

`PYSEC-2026-4320` concerns compromised intermediate CA keys chaining to an emSign root in older certifi bundles. This is critical for networked TLS clients. The frozen runtime has no network access, while the active runtime is upgraded to certifi 2026.10.23.

Reference:
- https://osv.dev/vulnerability/PYSEC-2026-4320

### Pillow

Pillow 13.0.0 is a security release addressing numerous image parser/encoder memory-safety and denial-of-service issues, including critical/high findings and the bundled OpenJPEG advisory `GHSA-78g4-xqwv-q3g8`.

Those findings are material for software that processes attacker-controlled images. The frozen research modes reviewed here consume repository JSON/reproduction artifacts and do not open untrusted image inputs. The active runtime is upgraded to Pillow 13.0.0.

References:
- https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-78g4-xqwv-q3g8

## Acceptance boundary

Residual acceptance applies only while all of these remain true:

1. `requirements.lock` hash remains exactly the reviewed hash above.
2. frozen runtime network remains `none`.
3. read-only root, dropped capabilities, no-new-privileges, non-root execution, and resource bounds remain enforced.
4. only preregistered research modes and append-only outputs are allowed.
5. the finding set matches the exact reviewed set in `.github/workflows/python-security.yml`.
6. the calendar date is not later than 2026-11-05.

Any boundary change or finding-set change fails closed and requires fresh review.
