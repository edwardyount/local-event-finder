// ======================================
// Create Event and Edit Event form (one script, two pages)
// The server does the real validation; this shows its messages next to each field.
// ======================================

const form = document.getElementById("eventForm");
const mode = form.dataset.mode;                    // "create" or "edit"
const editId = new URLSearchParams(window.location.search).get("id");

const FIELDS = ["title", "categoryId", "description", "date", "startTime", "endTime", "location", "capacity"];
const formMessage = document.getElementById("formMessage");
const formStatus = document.getElementById("formStatus");
const submitButton = document.getElementById("submitButton");


function clearErrors() {
    FIELDS.forEach(name => {
        document.getElementById(`error-${name}`).textContent = "";
        const input = document.getElementById(name);
        input.removeAttribute("aria-invalid");
        input.removeAttribute("aria-describedby");
    });
    formMessage.textContent = "";
}

function showErrors(errors) {
    let firstInvalid = null;

    FIELDS.forEach(name => {
        if (!errors[name]) return;
        document.getElementById(`error-${name}`).textContent = errors[name];
        const input = document.getElementById(name);
        input.setAttribute("aria-invalid", "true");
        input.setAttribute("aria-describedby", `error-${name}`);
        if (!firstInvalid) firstInvalid = input;
    });

    if (firstInvalid) firstInvalid.focus();
}

function showStatus(text) {
    formStatus.textContent = text;
}

function hideForm() {
    form.hidden = true;
}


async function requireLogin() {
    const { data } = await apiFetch("/api/auth/me");
    if (!data || !data.user) {
        window.location.href = "/pages/login.html";
        return false;
    }
    return true;
}

async function loadCategories() {
    const { ok, data } = await apiFetch("/api/categories");
    if (!ok) throw new Error("Could not load categories");

    const select = document.getElementById("categoryId");
    data.categories.forEach(category => {
        const option = document.createElement("option");
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
}

async function prefillForEdit() {
    const { ok, status, data } = await apiFetch(`/api/events/${encodeURIComponent(editId)}`);

    if (status === 404) { showStatus("Event not found."); hideForm(); return false; }
    if (!ok) throw new Error("Could not load event");

    const event = data.event;
    if (!event.isOwner) { showStatus("You can only edit your own events."); hideForm(); return false; }
    if (event.status !== "upcoming") { showStatus(`A ${event.status} event can't be edited.`); hideForm(); return false; }

    document.getElementById("title").value = event.title;
    document.getElementById("categoryId").value = event.categoryId;
    document.getElementById("description").value = event.description;
    document.getElementById("date").value = event.date;
    document.getElementById("startTime").value = event.startTime;
    document.getElementById("endTime").value = event.endTime;
    document.getElementById("location").value = event.location;
    document.getElementById("capacity").value = event.capacity;

    const hint = document.getElementById("capacityHint");
    hint.textContent = `Capacity cannot be less than current reservations (${event.activeRSVPCount} now).`;
    hint.hidden = false;
    return true;
}


form.addEventListener("submit", async (submitEvent) => {
    submitEvent.preventDefault();
    clearErrors();

    const body = {};
    FIELDS.forEach(name => { body[name] = document.getElementById(name).value; });

    submitButton.disabled = true;                  // stops double-clicks creating two listings

    try {
        const { ok, status, data } = await apiFetch(
            mode === "create" ? "/api/events" : `/api/events/${encodeURIComponent(editId)}`,
            { method: mode === "create" ? "POST" : "PUT", body: JSON.stringify(body) }
        );

        if (ok) {
            window.location.href = `/pages/event-details.html?id=${data.event.id}`;
            return;
        }
        if (status === 401) {
            window.location.href = "/pages/login.html";
            return;
        }

        if (data && data.errors) showErrors(data.errors);
        formMessage.textContent = (data && data.error) || "Could not save the event.";
    } catch (error) {
        formMessage.textContent = "Could not reach the server. Please try again.";
    }

    submitButton.disabled = false;
});


async function start() {
    try {
        if (!(await requireLogin())) return;
        await loadCategories();
        if (mode === "edit") await prefillForEdit();
    } catch (error) {
        showStatus("Could not load the form. Refresh the page to try again.");
        hideForm();
    }
}

start();
