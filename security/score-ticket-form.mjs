// A hostile client can omit or falsify Content-Length. Cap the streamed bytes
// before building a form body, rather than buffering an unbounded Request.text().
const MAX_HANDOFF_BYTES = 2048;
const OPAQUE_TICKET = /^[A-Za-z0-9_-]{43}$/;
export async function parseBoundedScoreTicket(request) {
  const media = (request.headers.get('content-type') || '').split(';', 1)[0].trim().toLowerCase();
  if (media !== 'application/x-www-form-urlencoded') return null;
  const advertised = request.headers.get('content-length');
  if (advertised !== null &&
      (!/^\d+$/.test(advertised) || Number(advertised) > MAX_HANDOFF_BYTES)) return null;
  const reader = request.body?.getReader();
  if (!reader) return null;
  let bytes = 0;
  const chunks = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_HANDOFF_BYTES) {
        await reader.cancel().catch(() => {});
        return null;
      }
      chunks.push(value);
    }
    const payload = new Uint8Array(bytes);
    let offset = 0;
    for (const chunk of chunks) {
      payload.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const body = new TextDecoder('utf-8', { fatal: true }).decode(payload);
    const fields = new URLSearchParams(body);
    if ([...fields.keys()].length !== 1 || !fields.has('ticket')) return null;
    const ticket = fields.get('ticket');
    return OPAQUE_TICKET.test(ticket || '') ? ticket : null;
  } catch {
    return null;
  }
}

