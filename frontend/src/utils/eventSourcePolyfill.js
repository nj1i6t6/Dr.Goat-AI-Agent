// Minimal EventSource POST polyfill using fetch + ReadableStream reader.
// Usage: new EventSourcePolyfill(url, { headers, payload })

export class EventSourcePolyfill {
  constructor(url, { headers = {}, payload = undefined } = {}) {
    this.url = url;
    this.headers = headers;
    this.payload = payload;
    this.controller = new AbortController();
    this.onmessage = null;
    this.onerror = null;
    this._run();
  }

  async _run() {
    try {
      const res = await fetch(this.url, {
        method: 'POST',
        headers: { 'Accept': 'text/event-stream', ...this.headers },
        body: this.payload,
        signal: this.controller.signal,
      });
      if (!res.ok || !res.body) throw new Error('SSE connection failed');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const rawEvent = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const lines = rawEvent.split('\n');
          let eventType = 'message';
          let data = '';
          for (const line of lines) {
            if (line.startsWith('event:')) eventType = line.slice(6).trim();
            if (line.startsWith('data:')) data += line.slice(5).trim();
          }
          if (eventType === 'message' && this.onmessage) this.onmessage({ data });
          if (eventType !== 'message' && this[`on${eventType}`]) this[`on${eventType}`]({ data });
        }
      }
    } catch (err) {
      if (this.onerror) this.onerror(err);
    }
  }

  addEventListener(type, handler) {
    this[`on${type}`] = handler;
  }

  close() {
    this.controller.abort();
  }
}
