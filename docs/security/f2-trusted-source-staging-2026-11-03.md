# F2 trusted Score rights -- separate review-only source
Status: DRAFT. NO CHECK PUBLISHER, APP, POLICY ACTIVATION, LICENCE OR PUBLIC RELEASE.
Origin: usdimpact/usd-impact-site PR #1094 at 44a94fc64d2f9d73aab08b4f71e4c9e463f9a490 (exact-head six checks PASS, including CodeQL).
Staged source: protected usdimpact/usd-impact-pipeline main e9a04b7576cbfd842cec7cbf0b18cfb2022ceb77; this PR is unmerged and must not be regarded as independently approved.
Purpose: isolate a future verified Git-tree evaluator from the website candidate PR trust boundary.
Test: node tools/f2/test-f2-trusted-git-tree-review.mjs; only synthetic file metadata and policy bytes are used.
Policy must be reviewed and pinned outside the candidate: 775 immutable files, three guard files, exact policy SHA256, authenticated GitHub tree SHA, exact PR head SHA, independent baseline source.
Observed PR #1089 research snapshot (not a final approved policy): website head 376e0905e055d1650a1e099f9c32621d4698dac2, tree c8fb91df369ecbfa3e0278773f575da3765743f9; 775/775 frozen file hashes match, 3 audit files, 90 dynamic, no unexpected tracked files.
Independent GitHub App still required: Metadata read, Contents read, Pull requests read, Checks write, signed webhooks, exact-head API recheck, isolated untrusted byte parsing, required source App ID in website ruleset only after complete negative tests.
Do NOT run candidate PR scripts with credentials. Dynamic News/Catalyst modifications require accountable source-rights review. A synthetic pass cannot grant provider redistribution rights.
Keep original Score provider rights Issue #155, N1b semantic clearance, H-03/H-16, October Monthly/Spanish, Preview protection, public deployment, indexing, media and commerce HOLD.
Do not merge this Draft, change rulesets, activate an App, create secrets, modify Vercel or touch Production without separate explicit release/security approval.
