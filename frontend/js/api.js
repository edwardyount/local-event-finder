// ======================================
// Shared helper for talking to the Flask API
// Adds the CSRF token to every state-changing request.
// ======================================

let csrfToken = null;

async function getCsrfToken() {
    if (!csrfToken) {
        const res = await fetch("/api/csrf-token", { credentials: "same-origin" });
        csrfToken = (await res.json()).csrfToken;
    }
    return csrfToken;
}

// Returns { ok, status, data }. Throws only if the server can't be reached.
async function apiFetch(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };

    if (method !== "GET") {
        headers["X-CSRFToken"] = await getCsrfToken();
    }

    const res = await fetch(url, { ...options, headers, credentials: "same-origin" });

    let data = null;
    try { data = await res.json(); } catch (e) { /* non-JSON response */ }

    // Login/logout replace the session, which invalidates the old CSRF token.
    if (url.startsWith("/api/auth/")) csrfToken = null;

    return { ok: res.ok, status: res.status, data };
}
