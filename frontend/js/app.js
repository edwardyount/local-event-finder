
// ======================================
// LOCAL EVENT FINDER
// Main Application Logic
// ======================================

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

    // Favorites now live on the server (the API sends isFavorite)
    const isFavorite = Boolean(event.isFavorite);

    const image = document.createElement("div");
    image.className = "event-image";

    const img = document.createElement("img");
    img.src = event.categoryImage;
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

    favoriteButton.addEventListener("click", async () => {
        const result = await setFavorite(event.id, !event.isFavorite);

        if (result === "login") {
            window.location.href = "/pages/login.html";   // must be signed in
        } else if (result === "ok") {
            event.isFavorite = !event.isFavorite;
            document.getElementById("filterMessage").textContent = "";
            renderEvents();
        } else {
            document.getElementById("filterMessage").textContent =
                "Could not update favorites. Please try again.";
        }
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


// Events currently shown (the server does the searching and filtering)
let currentEvents = [];
let requestCounter = 0;


// Draw the events we already have (no network call)
function renderEvents() {

    const eventGrid = document.getElementById("eventGrid");
    const eventCount = document.getElementById("eventCount");
    const emptyMessage = document.getElementById("emptyMessage");
    const errorMessage = document.getElementById("errorMessage");

    if (!eventGrid) return;

    eventGrid.replaceChildren();

    currentEvents.forEach(event => {
        eventGrid.appendChild(createEventCard(event));
    });

    const failed = !errorMessage.hidden;

    eventCount.textContent = failed ? "" : `${currentEvents.length} events found`;
    emptyMessage.hidden = failed || currentEvents.length !== 0;
}


// Build /api/events query string from the search box, categories and dates
function buildQuery() {
    const params = new URLSearchParams();

    const term = document.getElementById("searchInput").value.trim();
    if (term) params.set("q", term);

    selectedCategories.forEach(category => params.append("categories", category));

    const startDate = document.getElementById("startDate").value;
    const endDate = document.getElementById("endDate").value;
    if (startDate) params.set("startDate", startDate);
    if (endDate) params.set("endDate", endDate);

    return params.toString();
}


// Ask the server for events, then draw them
async function loadEvents() {

    const myRequest = ++requestCounter;
    const errorMessage = document.getElementById("errorMessage");
    const filterMessage = document.getElementById("filterMessage");

    filterMessage.textContent = "";

    try {
        const { ok, status, data } = await apiFetch("/api/events?" + buildQuery());

        if (myRequest !== requestCounter) return;   // a newer search already started

        if (status === 400 && data && data.error) {
            // Invalid dates: show the message and keep the last valid results
            filterMessage.textContent = data.error;
            return;
        }
        if (!ok) throw new Error("Bad response");

        errorMessage.hidden = true;
        currentEvents = data.events;
        renderEvents();

    } catch (error) {
        if (myRequest !== requestCounter) return;
        // Retry message, never a false "no events found"
        errorMessage.hidden = false;
        renderEvents();
    }
}


function debounce(fn, delay) {
    let timer;
    return () => {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
    };
}


// Initialize homepage interactions
document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");

    // Search as the user types (waits 250 ms after the last key)
    searchInput.addEventListener("input", debounce(loadEvents, 250));

    // Search button
    searchButton.addEventListener("click", loadEvents);

    // Date range
    document.getElementById("startDate").addEventListener("change", loadEvents);
    document.getElementById("endDate").addEventListener("change", loadEvents);

    // Retry after a failed load
    document.getElementById("retryButton").addEventListener("click", loadEvents);

    // Category selection
    document.querySelectorAll(".category-btn").forEach(button => {

        button.addEventListener("click", () => {

            toggleCategory(button.dataset.category);

            button.classList.toggle("active");

            button.setAttribute(
                "aria-pressed",
                button.classList.contains("active")
            );

            loadEvents();
        });

    });

    // Initial event display
    loadEvents();

});
