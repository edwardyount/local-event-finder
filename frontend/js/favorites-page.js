// ======================================
// Favorites page: list the signed-in user's saved events
// ======================================

const grid = document.getElementById("favoritesGrid");
const countLabel = document.getElementById("favoritesCount");
const emptyMessage = document.getElementById("favoritesEmpty");
const errorMessage = document.getElementById("favoritesError");
const statusMessage = document.getElementById("favoritesMessage");

let favoriteEvents = [];


function createFavoriteCard(event) {
    const card = document.createElement("article");
    card.className = "event-card";

    const imageBox = document.createElement("div");
    imageBox.className = "event-image";
    const img = document.createElement("img");
    img.src = event.categoryImage;
    img.alt = `${event.category} event`;
    img.loading = "lazy";
    img.addEventListener("error", () => img.remove());
    imageBox.appendChild(img);

    const content = document.createElement("div");
    content.className = "event-content";

    const category = document.createElement("p");
    category.className = "event-category";
    category.textContent = event.category;

    const title = document.createElement("h3");
    title.textContent = event.title;

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
    detailsLink.href = `event-details.html?id=${encodeURIComponent(event.id)}`;
    detailsLink.textContent = "View Details";

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-favorite-btn";
    removeButton.textContent = "♥ Remove Favorite";
    removeButton.addEventListener("click", async () => {
        removeButton.disabled = true;
        const result = await setFavorite(event.id, false);

        if (result === "login") {
            window.location.href = "/pages/login.html";
        } else if (result === "ok") {
            favoriteEvents = favoriteEvents.filter(item => item.id !== event.id);
            statusMessage.textContent = "";
            render();
        } else {
            removeButton.disabled = false;
            statusMessage.textContent = "Could not remove that favorite. Please try again.";
        }
    });

    actions.appendChild(detailsLink);
    actions.appendChild(removeButton);

    content.appendChild(category);
    content.appendChild(title);
    content.appendChild(date);
    content.appendChild(location);
    content.appendChild(actions);

    card.appendChild(imageBox);
    card.appendChild(content);
    return card;
}


function render() {
    grid.replaceChildren();
    favoriteEvents.forEach(event => grid.appendChild(createFavoriteCard(event)));

    const failed = !errorMessage.hidden;
    countLabel.textContent = failed ? "" : `${favoriteEvents.length} saved events`;
    emptyMessage.hidden = failed || favoriteEvents.length !== 0;
}


async function loadFavorites() {
    try {
        const { ok, status, data } = await apiFetch("/api/favorites");

        if (status === 401) {                       // visitors go to the login page
            window.location.href = "/pages/login.html";
            return;
        }
        if (!ok) throw new Error("Bad response");

        errorMessage.hidden = true;
        favoriteEvents = data.events;
    } catch (error) {
        errorMessage.hidden = false;                // retry message, not a false "empty"
    }
    render();
}


document.getElementById("favoritesRetry").addEventListener("click", loadFavorites);
loadFavorites();
