-- Read-only verification for the Development private Score evidence bucket.

select
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types,
  created_at,
  updated_at
from storage.buckets
where id = 'score-private-evidence';

select
  count(*)::bigint as object_count
from storage.objects
where bucket_id = 'score-private-evidence';
