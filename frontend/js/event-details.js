// ======================================
// Event details page (data comes from /api/events/<id>)
// All user text is set with textContent, so it can never run as script.
// ======================================

const detailsContainer = document.getElementById("eventDetails");
const eventId = new URLSearchParams(window.location.search).get("id");


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


function addText(parent, tag, text, className) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
}

function addInfoRow(parent, label, value) {
    const row = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = label + " ";
    row.appendChild(strong);
    row.appendChild(document.createTextNode(value));
    parent.appendChild(row);
}


function renderEvent(event) {
    detailsContainer.replaceChildren();

    const image = document.createElement("img");
    image.className = "details-image";
    image.src = event.categoryImage;
    image.alt = `${event.category} event`;
    // A broken image must not stop the rest of the page from showing
    image.addEventListener("error", () => image.remove());
    detailsContainer.appendChild(image);

    addText(detailsContainer, "p", event.category, "event-category");
    addText(detailsContainer, "h1", event.title);

    if (event.status === "started") {
        addText(detailsContainer, "p", "This event has already started.", "form-message");
    } else if (event.status === "cancelled") {
        addText(detailsContainer, "p", "This event was cancelled.", "form-message");
    }

    addText(detailsContainer, "p", event.description);

    const info = document.createElement("div");
    info.className = "details-information";
    addInfoRow(info, "Date:", formatEventDate(event.date));
    addInfoRow(info, "Time:", `${formatEventTime(event.startTime)} – ${formatEventTime(event.endTime)}`);
    addInfoRow(info, "Location:", event.location);
    addInfoRow(info, "Created by:", event.creator);
    addInfoRow(info, "Capacity:", String(event.capacity));
    addInfoRow(info, "Active RSVPs:", String(event.activeRSVPCount));
    detailsContainer.appendChild(info);

    // Add / remove favorite (needs a signed-in user)
    const favoriteButton = document.createElement("button");
    favoriteButton.type = "button";
    favoriteButton.className = "favorite-toggle";

    const favoriteMessage = document.createElement("p");
    favoriteMessage.className = "form-message";
    favoriteMessage.setAttribute("role", "status");

    function paintFavorite() {
        favoriteButton.textContent = event.isFavorite ? "♥ Remove from Favorites" : "♡ Add to Favorites";
        favoriteButton.classList.toggle("active", event.isFavorite);
    }

    favoriteButton.addEventListener("click", async () => {
        const result = await setFavorite(event.id, !event.isFavorite);

        if (result === "login") {
            window.location.href = "/pages/login.html";
        } else if (result === "ok") {
            event.isFavorite = !event.isFavorite;
            favoriteMessage.textContent = "";
            paintFavorite();
        } else {
            favoriteMessage.textContent = "Could not update favorites. Please try again.";
        }
    });

    paintFavorite();
    detailsContainer.appendChild(favoriteButton);
    detailsContainer.appendChild(favoriteMessage);
}


function showRetry() {
    detailsContainer.replaceChildren();
    addText(detailsContainer, "p", "Could not load this event. ");

    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Retry";
    retry.addEventListener("click", loadEvent);
    detailsContainer.lastChild.appendChild(retry);
}


async function loadEvent() {
    detailsContainer.textContent = "Loading...";

    try {
        const { ok, status, data } = await apiFetch(`/api/events/${encodeURIComponent(eventId)}`);

        if (ok) {
            renderEvent(data.event);
        } else if (status === 404) {
            detailsContainer.textContent = "Event not found.";
        } else {
            showRetry();
        }
    } catch (error) {
        showRetry();
    }
}

loadEvent();
