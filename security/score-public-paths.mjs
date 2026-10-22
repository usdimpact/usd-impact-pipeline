// Only artifacts already published as public methodology/reproducibility data
// bypass the membership gate. Never open a directory prefix: archive HTML,
// dashboard pages and future unpublished files must still require a session.
const PUBLIC_PATHS = new Set([
  '/member-required', '/member-required.html', '/robots.txt', '/favicon.ico',
  '/data/backtest_results.json',
  '/data/score_repro_bundle_latest.json',
  '/data/score_v2_data_semantics.json',
  '/data/score_v2_data_semantics.schema.json',
  '/data/score_v2_methodology.json',
  '/data/score_v2_methodology.schema.json',
  '/data/usd_impact_score_v2.csv',
  '/data/usd_impact_score_v2.json',
  '/data/weekly_input_latest.json',
  '/data/research/independent_replication_protocol.json',
  '/data/research/score_v2_point_in_time_latest.json',
  '/data/research/score_v2_robustness_latest.json',
  '/data/research/score_v2_vintage_comparison_latest.csv',
  '/data/research/score_v2_vintage_comparison_latest.json',
  '/data/research/score_v2_vintage_comparison_latest.html',
  '/data/research/score_v2_vintage_comparison_latest', // Pages clean URL
]);
const PUBLIC_DATED_ARCHIVE_RE = /^\/archive\/\d{4}-\d{2}-\d{2}\/(?:score|weekly_input|repro_bundle)\.json$/;
export function isPublicScorePath(pathname) {
  return PUBLIC_PATHS.has(pathname) || PUBLIC_DATED_ARCHIVE_RE.test(pathname);
}
