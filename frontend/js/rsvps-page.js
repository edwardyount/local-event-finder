// ======================================
// My RSVPs page: the signed-in user's own RSVPs
// ======================================

const tableWrap = document.getElementById("rsvpTableWrap");
const rows = document.getElementById("rsvpRows");
const countLabel = document.getElementById("rsvpCount");
const emptyMessage = document.getElementById("rsvpEmpty");
const errorMessage = document.getElementById("rsvpError");

const STATUS_LABELS = { upcoming: "Upcoming", started: "Started", cancelled: "Cancelled" };


function addCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
    return cell;
}

function addPill(row, text, kind) {
    const cell = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `status-pill ${kind}`;
    pill.textContent = text;
    cell.appendChild(pill);
    row.appendChild(cell);
}


function renderRsvps(events) {
    rows.replaceChildren();

    events.forEach(event => {
        const row = document.createElement("tr");

        const titleCell = document.createElement("td");
        const link = document.createElement("a");
        link.href = `event-details.html?id=${encodeURIComponent(event.id)}`;
        link.textContent = event.title;
        const category = document.createElement("small");
        category.className = "cell-sub";
        category.textContent = event.category;
        titleCell.appendChild(link);
        titleCell.appendChild(category);
        row.appendChild(titleCell);

        const whenCell = addCell(row, formatDate(event.date));
        const time = document.createElement("small");
        time.className = "cell-sub";
        time.textContent = `${formatTime(event.startTime)} – ${formatTime(event.endTime)}`;
        whenCell.appendChild(time);

        addCell(row, event.location);
        addPill(row, STATUS_LABELS[event.status] || event.status, event.status);
        addPill(row, event.participation, "confirmed");

        rows.appendChild(row);
    });

    errorMessage.hidden = true;
    tableWrap.hidden = events.length === 0;
    emptyMessage.hidden = events.length !== 0;
    countLabel.textContent = `${events.length} confirmed reservations`;
}


async function loadRsvps() {
    try {
        const { ok, status, data } = await apiFetch("/api/rsvps");

        if (status === 401) {                       // visitors go to the login page
            window.location.href = "/pages/login.html";
            return;
        }
        if (!ok) throw new Error("Bad response");

        renderRsvps(data.events);
    } catch (error) {
        tableWrap.hidden = true;
        emptyMessage.hidden = true;
        countLabel.textContent = "";
        errorMessage.hidden = false;                // retry message, not a false "empty"
    }
}


document.getElementById("rsvpRetry").addEventListener("click", loadRsvps);
loadRsvps();
