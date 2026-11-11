// ======================================
// Date and time formatting (same output as the home page cards)
// Used by the Favorites and RSVP pages.
// ======================================

function formatDate(dateString) {
    const date = new Date(dateString + "T12:00:00Z");

    return new Intl.DateTimeFormat("en-US", {
        timeZone: "UTC",
        month: "short",
        day: "numeric",
        year: "numeric"
    }).format(date);
}

function formatTime(timeString) {
    const [hour, minute] = timeString.split(":").map(Number);

    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;

    return `${displayHour}:${String(minute).padStart(2, "0")} ${period} ET`;
}
