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


### 27 October 2026 advisory-database refresh

The frozen lock and isolation boundary are unchanged, but the upstream vulnerability database changed its Pillow finding identifiers. This triggered the intended fail-closed review gate.

- `PYSEC-2026-4328` is the PySec identifier for the already-reviewed `CVE-2026-112396` / `GHSA-4rr5-89j8-mwwm` TIFF encoder use-after-free. The underlying vulnerability and the fix in Pillow 13.0.0 are unchanged; only the audit identifier emitted by the current feed changed.
- `PYSEC-2026-4327` aliases `CVE-2026-112394` / `GHSA-4558-3h8r-v8xp`, a raw-decoder over-read reachable through `Image.frombytes()` or `Image.frombuffer()` with the `P;2L` or `P;4L` raw modes. Repository search confirms the frozen research code contains none of those calls or raw modes.
- `PYSEC-2026-4326` aliases the already-reviewed `CVE-2026-112392` / `GHSA-27h8-gf7j-v5hc` zero-size-image rank-filter crash. The current audit feed changed the emitted identifier; the underlying issue, fix in Pillow 13.0.0, and frozen-boundary assessment are unchanged.
- The reviewed frozen execution modes still do not open or decode image inputs and do not render charts. The only repository `BytesIO` use in the active Score generator is Matplotlib PNG output, not TIFF encoding.
- The active online runtime remains on Pillow 13.0.0, where both findings are fixed.
- The root `requirements.lock` hash remains `a4c6fb90909a04eb267057d3e31049c7fc38b12e8a7d556e79c0141aa0d52db6`.
- The existing residual-risk acceptance expiry remains **2026-11-05**. This review does not extend it.
- The CI exact-match gate now canonicalizes only these three verified PySec aliases before comparison: `PYSEC-2026-4326 -> CVE-2026-112392`, `PYSEC-2026-4327 -> CVE-2026-112394`, and `PYSEC-2026-4328 -> CVE-2026-112396`. No other advisory identifiers are normalized; any other added, removed, or changed finding still fails closed.

References:
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-4558-3h8r-v8xp
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-27h8-gf7j-v5hc
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-4rr5-89j8-mwwm
- https://github.com/python-pillow/Pillow/blob/main/docs/releasenotes/13.0.0.rst


### 28 October 2026 advisory-database refresh

The upstream PyPA advisory database changed the emitted identifiers for additional already-reviewed Pillow findings and introduced one newly surfaced finding, `CVE-2026-112403`.

Verified alias updates:
- `PYSEC-2026-4329 -> CVE-2026-112397`
- `PYSEC-2026-4330 -> CVE-2026-112398`
- `PYSEC-2026-4331 -> CVE-2026-112402`
- `PYSEC-2026-4333 -> CVE-2026-112405`
- `PYSEC-2026-4334 -> CVE-2026-112896`
- `PYSEC-2026-4335 -> CVE-2026-112901`
- `PYSEC-2026-4336 -> CVE-2026-114501`
- `PYSEC-2026-4337 -> CVE-2026-96636`
- `PYSEC-2026-4338 -> CVE-2026-96637`
- `PYSEC-2026-4339 -> CVE-2026-96639`
- `PYSEC-2026-4340 -> CVE-2026-96641`
- `PYSEC-2026-4341 -> CVE-2026-96642`
- `PYSEC-2026-4342 -> CVE-2026-96643`
- `PYSEC-2026-4343 -> CVE-2026-96644`

New finding:
- `PYSEC-2026-4332` aliases `CVE-2026-112403` / `GHSA-8g5g-8vmr-9782`.
- It affects Pillow JPEG decoding when an application requests draft/downscaled decoding of a crafted 8-bit lossless SOF3 JPEG under affected libjpeg-turbo builds, potentially causing heap corruption.
- The issue is fixed in Pillow 13.0.0.
- Repository review confirms the frozen research modes do not call Pillow image-opening APIs, `draft()`, or `thumbnail()`; they consume repository JSON/reproduction artifacts and do not render charts.
- The active online runtime is already pinned to Pillow 13.0.0.
- The frozen root lock remains byte-identical and network-isolated.
- The existing residual-risk acceptance expiry remains **2026-11-05**; this review does not extend it.

The exact-match gate now canonicalizes the verified PySec identifiers above to their CVE aliases before comparison and adds `CVE-2026-112403` to the explicitly reviewed frozen finding set. Any other finding change still fails closed.

Reference:
- https://github.com/pypa/advisory-database/blob/main/vulns/pillow/PYSEC-2026-4332.yaml

## Acceptance boundary

Residual acceptance applies only while all of these remain true:

1. `requirements.lock` hash remains exactly the reviewed hash above.
2. frozen runtime network remains `none`.
3. read-only root, dropped capabilities, no-new-privileges, non-root execution, and resource bounds remain enforced.
4. only preregistered research modes and append-only outputs are allowed.
5. the finding set matches the exact reviewed set in `.github/workflows/python-security.yml`.
6. the calendar date is not later than 2026-11-05.

Any boundary change or finding-set change fails closed and requires fresh review.
