// Check for saved theme preference
const currentTheme = localStorage.getItem("theme") || "light";

// Apply the saved theme if exists
if (currentTheme) {
    document.documentElement.setAttribute("data-theme", currentTheme);
    if (currentTheme === "dark") {
        document.body.classList.add("dark-theme");
        const themeIcon = document.getElementById("theme-icon");
        if (themeIcon) {
            themeIcon.classList.replace("bx-moon", "bx-sun");
        }
    }
}

// Theme toggle functionality
document.getElementById("theme-toggle").addEventListener("click", function() {
    // Toggle dark theme class
    document.body.classList.toggle("dark-theme");

    // Check if dark theme is active
    let theme = "light";
    if (document.body.classList.contains("dark-theme")) {
        theme = "dark";
        const themeIcon = document.getElementById("theme-icon");
        if (themeIcon) {
            themeIcon.classList.replace("bx-moon", "bx-sun");
        }
    } else {
        const themeIcon = document.getElementById("theme-icon");
        if (themeIcon) {
            themeIcon.classList.replace("bx-sun", "bx-moon");
        }
    }

    // Save the theme preference
    localStorage.setItem("theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
});