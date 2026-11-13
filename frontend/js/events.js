
// ======================================
// LOCAL EVENT FINDER
// Sample Event Data
// Temporary data until Flask integration
// ======================================

const categories = [
    "Arts and Culture",
    "Sports and Fitness",
    "Education",
    "Community and Volunteering",
    "Food and Drink",
    "Social and Recreation"
];


// Fixed image for each event category
const categoryImages = {
    "Arts and Culture": "/images/events/louisville-art-walk.jpg",
    "Sports and Fitness": "/images/events/fitness-meetup.jpg",
    "Education": "/images/events/data-science.jpg",
    "Community and Volunteering": "/images/events/volunteer-day.jpg",
    "Food and Drink": "/images/events/food-festival.jpg",
    "Social and Recreation": "/images/events/board-game-night.jpg"
};


// Temporary demonstration events
const events = [
    {
        id: 1,
        title: "Louisville Art Walk",
        description: "Explore local artists, creative exhibits and galleries.",
        location: "NuLu, Louisville",
        category: "Arts and Culture",
        date: "2026-11-14",
        startTime: "14:00",
        endTime: "17:00",
        creator: "Community Arts",
        capacity: 100,
        activeRSVPCount: 35
    },

    {
        id: 2,
        title: "Saturday Fitness Meetup",
        description: "Join a community workout and meet new fitness enthusiasts.",
        location: "Waterfront Park, Louisville",
        category: "Sports and Fitness",
        date: "2026-11-15",
        startTime: "09:00",
        endTime: "11:00",
        creator: "Louisville Fitness",
        capacity: 50,
        activeRSVPCount: 22
    },

    {
        id: 3,
        title: "Introduction to Data Science",
        description: "Learn about data analytics, technology and career opportunities.",
        location: "University of Louisville",
        category: "Education",
        date: "2026-11-18",
        startTime: "16:00",
        endTime: "18:00",
        creator: "Student Organization",
        capacity: 75,
        activeRSVPCount: 40
    },

    {
        id: 4,
        title: "Community Volunteer Day",
        description: "Give back to the community through a local volunteer initiative.",
        location: "Downtown Louisville",
        category: "Community and Volunteering",
        date: "2026-11-20",
        startTime: "10:00",
        endTime: "13:00",
        creator: "Community Volunteers",
        capacity: 60,
        activeRSVPCount: 18
    },

    {
        id: 5,
        title: "Louisville Food Festival",
        description: "Discover local restaurants, food vendors and new flavors.",
        location: "Fourth Street Live, Louisville",
        category: "Food and Drink",
        date: "2026-11-21",
        startTime: "12:00",
        endTime: "16:00",
        creator: "Local Food Events",
        capacity: 150,
        activeRSVPCount: 90
    },

    {
        id: 6,
        title: "Board Game Social Night",
        description: "Meet new people and enjoy a relaxed evening of games.",
        location: "Highlands, Louisville",
        category: "Social and Recreation",
        date: "2026-11-22",
        startTime: "18:00",
        endTime: "21:00",
        creator: "Louisville Social Club",
        capacity: 40,
        activeRSVPCount: 12
    }
];

// Get the image assigned to an event's category
function getCategoryImage(category) {
    return categoryImages[category];
}
