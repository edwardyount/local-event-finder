
// ======================================
// LOCAL EVENT FINDER
// Search and Filtering Logic
// ======================================

let selectedCategories = [];

// Search events by title, description or location
function searchEvents(eventList, searchTerm) {

    const query = searchTerm.trim().toLowerCase();

    if (!query) {
        return eventList;
    }

    return eventList.filter(event => {

        return (
            event.title.toLowerCase().includes(query) ||
            event.description.toLowerCase().includes(query) ||
            event.location.toLowerCase().includes(query)
        );

    });
}


// Filter events by selected categories
function filterByCategory(eventList, selectedCategories) {

    // No selected categories means show all categories
    if (selectedCategories.length === 0) {
        return eventList;
    }

    return eventList.filter(event =>
        selectedCategories.includes(event.category)
    );
}


// Combine search and category filtering
function getFilteredEvents(eventList, searchTerm) {

    let filteredEvents = searchEvents(eventList, searchTerm);

    filteredEvents = filterByCategory(
        filteredEvents,
        selectedCategories
    );

    return filteredEvents;
}


// Toggle a category on or off
function toggleCategory(category) {

    if (selectedCategories.includes(category)) {

        selectedCategories = selectedCategories.filter(
            item => item !== category
        );

    } else {

        selectedCategories.push(category);

    }
}


// Clear all category selections
function clearCategories() {
    selectedCategories = [];
}
