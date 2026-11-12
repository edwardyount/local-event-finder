// ======================================
// Navbar: turn "Log In" into "Log out (name)" when signed in
// ======================================

document.addEventListener("DOMContentLoaded", async () => {
    const loginLink = document.querySelector(".login-btn");
    if (!loginLink) return;

    try {
        const { data } = await apiFetch("/api/auth/me");
        if (!data || !data.user) return;

        loginLink.textContent = `Log out (${data.user.name})`;
        loginLink.href = "#";
        loginLink.addEventListener("click", async (event) => {
            event.preventDefault();
            await apiFetch("/api/auth/logout", { method: "POST" });
            window.location.href = "/index.html";
        });
    } catch (error) {
        // Server unreachable: leave the Log In link as it is
    }
});
