
// ======================================
// LOCAL EVENT FINDER
// Main Application Logic
// ======================================

// Save favorite event IDs in the browser
function getFavorites() {
    return JSON.parse(localStorage.getItem("favoriteEvents") || "[]");
}

function saveFavorites(favorites) {
    localStorage.setItem("favoriteEvents", JSON.stringify(favorites));
}


// Determine whether an event is upcoming using Eastern Time
function isUpcoming(event) {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "America/New_York",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
    }).formatToParts(new Date());

    const values = {};
    parts.forEach(part => {
        values[part.type] = part.value;
    });

    const nowKey =
        `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`;

    return `${event.date}T${event.startTime}` > nowKey;
}


// Format event date
function formatDate(dateString) {
    const date = new Date(dateString + "T12:00:00Z");

    return new Intl.DateTimeFormat("en-US", {
        timeZone: "UTC",
        month: "short",
        day: "numeric",
        year: "numeric"
    }).format(date);
}


// Format event time
function formatTime(timeString) {
    const [hour, minute] = timeString.split(":").map(Number);

    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;

    return `${displayHour}:${String(minute).padStart(2, "0")} ${period} ET`;
}


// Create an individual event card
function createEventCard(event) {

    const card = document.createElement("article");
    card.className = "event-card";

    const favorites = getFavorites();
    const isFavorite = favorites.includes(event.id);

    const image = document.createElement("div");
    image.className = "event-image";

    const img = document.createElement("img");
    img.src = getCategoryImage(event.category);
    img.alt = `${event.category} event`;
    img.loading = "lazy";

    image.appendChild(img);

    const content = document.createElement("div");
    content.className = "event-content";

    const category = document.createElement("p");
    category.className = "event-category";
    category.textContent = event.category;

    const title = document.createElement("h3");
    title.textContent = event.title;

    const description = document.createElement("p");
    description.className = "event-description";
    description.textContent = event.description;

    const date = document.createElement("p");
    date.className = "event-info";
    date.textContent = `📅 ${formatDate(event.date)} · ${formatTime(event.startTime)}`;

    const location = document.createElement("p");
    location.className = "event-info";
    location.textContent = `📍 ${event.location}`;

    const actions = document.createElement("div");
    actions.className = "event-actions";

    const detailsLink = document.createElement("a");
    detailsLink.className = "details-btn";
    detailsLink.href = `pages/event-details.html?id=${encodeURIComponent(event.id)}`;
    detailsLink.textContent = "View Details";

    const favoriteButton = document.createElement("button");
    favoriteButton.className = "favorite-btn";
    favoriteButton.type = "button";
    favoriteButton.textContent = isFavorite ? "♥" : "♡";
    favoriteButton.classList.toggle("active", isFavorite);
    favoriteButton.setAttribute(
        "aria-label",
        isFavorite ? "Remove from favorites" : "Add to favorites"
    );

    favoriteButton.addEventListener("click", () => {
        toggleFavorite(event.id);
        renderEvents();
    });

    actions.appendChild(detailsLink);
    actions.appendChild(favoriteButton);

    content.appendChild(category);
    content.appendChild(title);
    content.appendChild(description);
    content.appendChild(date);
    content.appendChild(location);
    content.appendChild(actions);

    card.appendChild(image);
    card.appendChild(content);

    return card;
}


// Add or remove an event from favorites
function toggleFavorite(eventId) {

    let favorites = getFavorites();

    if (favorites.includes(eventId)) {
        favorites = favorites.filter(id => id !== eventId);
    } else {
        favorites.push(eventId);
    }

    saveFavorites(favorites);
}


// Display events on the homepage
function renderEvents() {

    const eventGrid = document.getElementById("eventGrid");
    const eventCount = document.getElementById("eventCount");
    const emptyMessage = document.getElementById("emptyMessage");

    if (!eventGrid) return;

    const searchInput = document.getElementById("searchInput");

    const searchTerm = searchInput ? searchInput.value : "";

    // Show upcoming events only
    const upcomingEvents = events.filter(isUpcoming);

    // Apply search and category filters
    const filteredEvents = getFilteredEvents(
        upcomingEvents,
        searchTerm
    );

    eventGrid.replaceChildren();

    filteredEvents.forEach(event => {
        eventGrid.appendChild(createEventCard(event));
    });

    eventCount.textContent =
        `${filteredEvents.length} events found`;

    emptyMessage.hidden = filteredEvents.length !== 0;
}


// Initialize homepage interactions
document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");

    // Search as the user types
    searchInput.addEventListener("input", renderEvents);

    // Search button
    searchButton.addEventListener("click", renderEvents);

    // Category selection
    document.querySelectorAll(".category-btn").forEach(button => {

        button.addEventListener("click", () => {

            const category = button.dataset.category;

            toggleCategory(category);

            button.classList.toggle("active");

            button.setAttribute(
                "aria-pressed",
                button.classList.contains("active")
            );

            renderEvents();
        });

    });

    // Initial event display
    renderEvents();

});
