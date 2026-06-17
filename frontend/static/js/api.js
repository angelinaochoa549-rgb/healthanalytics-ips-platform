const API = {
  async request(method, url, body = null, auth = true) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth) {
      const token = localStorage.getItem('access_token');
      if (!token) {
        window.location.href = '/login/';
        return;
      }
      headers['Authorization'] = `Bearer ${token}`;
    }
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    let res = await fetch(url, opts);

    if (res.status === 401 && auth) {
      localStorage.clear();
      window.location.href = '/login/';
      return;
    }

    if (!res.ok) {
      const err = new Error(`HTTP ${res.status}`);
      err.status = res.status;
      try { err.data = await res.json(); } catch(_) {}
      throw err;
    }

    const text = await res.text();
    return text ? JSON.parse(text) : null;
  },

  get(url, auth = true)        { return this.request('GET', url, null, auth); },
  post(url, body, auth = true) { return this.request('POST', url, body, auth); },
};