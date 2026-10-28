-- Development-only private Score evidence bucket provisioning.
-- REVIEW SOURCE ONLY. Do not execute before explicit owner authorization.
--
-- Current Supabase documentation supports creating Storage buckets by inserting
-- into storage.buckets. This statement is intentionally fail-closed: if the
-- bucket already exists, the insert fails instead of mutating an existing
-- bucket silently.

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'score-private-evidence',
  'score-private-evidence',
  false,
  1048576,
  array['application/json']::text[]
);
