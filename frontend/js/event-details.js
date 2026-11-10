
const params = new URLSearchParams(window.location.search);
const eventId = Number(params.get("id"));

const selectedEvent = events.find(event => event.id === eventId);
const detailsContainer = document.getElementById("eventDetails");

function formatEventDate(dateString) {
    const date = new Date(dateString + "T12:00:00Z");
    return new Intl.DateTimeFormat("en-US", {
        timeZone: "UTC",
        month: "long",
        day: "numeric",
        year: "numeric"
    }).format(date);
}

function formatEventTime(timeString) {
    const [hour, minute] = timeString.split(":").map(Number);
    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;

    return `${displayHour}:${String(minute).padStart(2, "0")} ${period} ET`;
}

if (!selectedEvent) {
    detailsContainer.textContent = "Event not found.";
} else {
    detailsContainer.innerHTML = `
        <img
            class="details-image"
            src="${getCategoryImage(selectedEvent.category)}"
            alt="${selectedEvent.category} event"
        >

        <p class="event-category">${selectedEvent.category}</p>
        <h1>${selectedEvent.title}</h1>
        <p>${selectedEvent.description}</p>

        <div class="details-information">
            <p><strong>Date:</strong> ${formatEventDate(selectedEvent.date)}</p>
            <p><strong>Time:</strong> ${formatEventTime(selectedEvent.startTime)} – ${formatEventTime(selectedEvent.endTime)}</p>
            <p><strong>Location:</strong> ${selectedEvent.location}</p>
            <p><strong>Created by:</strong> ${selectedEvent.creator}</p>
            <p><strong>Capacity:</strong> ${selectedEvent.capacity}</p>
            <p><strong>Active RSVPs:</strong> ${selectedEvent.activeRSVPCount}</p>
        </div>
    `;
}
