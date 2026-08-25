# Temporary ruleset negative-proof fixture

This file exists only on the temporary branch `agent/ruleset-negative-proof-2026-08-25` to verify that the future `main` ruleset rejects an out-of-date pull request.

Safety boundary:
- never merge this fixture;
- do not use it as production or research evidence;
- close the pull request and delete the branch after ruleset verification;
- no Score formula, source, data, release artifact, Cloudflare Production content, secret, or workflow behavior is changed by this fixture.

The branch intentionally starts from commit `0c1623a399a052063a22d4a2b619f31506f3d714`, which is behind the current `main` commit used for the ruleset test.
