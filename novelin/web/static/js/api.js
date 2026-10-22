async function request(url, options = {}) {
  const response = await fetch(url, options);
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.error || `Permintaan gagal (HTTP ${response.status}).`);
  }
  return payload;
}

export function loadNovel(url) {
  return request(`/api/novel?url=${encodeURIComponent(url)}`);
}

export function loadChapter(url, cookie) {
  return request("/api/chapter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, cookie }),
  });
}

export function startJob(payload) {
  return request("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function cancelJob(jobId) {
  return request(`/api/jobs/${jobId}/cancel`, { method: "POST" });
}

export function watchJob(jobId, handlers) {
  const source = new EventSource(`/api/jobs/${jobId}/events`);
  let finished = false;

  source.onmessage = (message) => {
    let event;
    try {
      event = JSON.parse(message.data);
    } catch {
      return;
    }

    handlers.onEvent?.(event);
    if (event.type === "done" || event.type === "error") {
      finished = true;
      source.close();
      handlers.onClose?.(event);
    }
  };

  source.onerror = () => {
    if (!finished) handlers.onError?.();
  };

  return source;
}
