// ======================================
// RSVP to an event on the server
// result: "ok" | "login" (not signed in) | "refused" (full, started, not found) | "error"
// ======================================

async function rsvpToEvent(eventId) {
    try {
        const { ok, status, data } = await apiFetch(
            `/api/rsvps/${encodeURIComponent(eventId)}`,
            { method: "POST" }
        );

        if (ok) return { result: "ok", data };
        if (status === 401) return { result: "login" };
        if (status === 404 || status === 409) {
            return { result: "refused", message: (data && data.error) || "Could not RSVP." };
        }
        return { result: "error" };

    } catch (error) {
        return { result: "error" };
    }
}
