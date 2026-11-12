// ======================================
// Login and Register forms
// ======================================

const SERVER_ERROR = "Could not reach the server. Please try again.";

function errorText(data, fallback) {
    if (data && data.errors && Object.keys(data.errors).length) {
        return Object.values(data.errors).join(" ");
    }
    return (data && data.error) || fallback;
}

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const message = document.getElementById("loginMessage");
            message.textContent = "";

            try {
                const { ok, data } = await apiFetch("/api/auth/login", {
                    method: "POST",
                    body: JSON.stringify({
                        email: document.getElementById("email").value,
                        password: document.getElementById("password").value
                    })
                });
                if (ok) {
                    window.location.href = "../index.html";
                } else {
                    message.textContent = errorText(data, "Login failed.");
                }
            } catch (e) {
                message.textContent = SERVER_ERROR;
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const message = document.getElementById("registerMessage");
            message.textContent = "";

            const password = document.getElementById("password").value;
            if (password !== document.getElementById("confirmPassword").value) {
                message.textContent = "Passwords do not match.";
                return;
            }

            try {
                const { ok, data } = await apiFetch("/api/auth/register", {
                    method: "POST",
                    body: JSON.stringify({
                        displayName: document.getElementById("displayName").value,
                        email: document.getElementById("email").value,
                        password: password
                    })
                });
                if (ok) {
                    window.location.href = "../index.html";   // registration also signs you in
                } else {
                    message.textContent = errorText(data, "Registration failed.");
                }
            } catch (e) {
                message.textContent = SERVER_ERROR;
            }
        });
    }
});
