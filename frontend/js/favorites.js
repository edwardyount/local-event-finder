// ======================================
// Save / remove a favorite on the server
// Returns "ok", "login" (not signed in) or "error".
// ======================================

async function setFavorite(eventId, save) {
    try {
        const { ok, status } = await apiFetch(
            `/api/favorites/${encodeURIComponent(eventId)}`,
            { method: save ? "POST" : "DELETE" }
        );

        if (ok) return "ok";
        if (status === 401) return "login";
        if (!save && status === 404) return "ok";   // already gone
        return "error";

    } catch (error) {
        return "error";
    }
}
