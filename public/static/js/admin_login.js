/**
 * Dedicated Admin Login Handler
 * Surgical implementation for Single Admin Authentication
 * Allows LOGIN ONLY for configured System Administrator
 */

async function handleAdminAuthFormSubmit(event) {
    if (event) event.preventDefault();

    const emailInput = document.getElementById("adminAuthEmail");
    const passwordInput = document.getElementById("adminAuthPassword");

    const email = emailInput ? emailInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value : "";

    if (!email || !password) {
        if (typeof showNotification === "function") {
            showNotification("Error", "Please enter both Admin Email and Password.", "error");
        }
        return;
    }

    const btnSubmit = document.getElementById("btnAdminAuthSubmit");
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Authenticating...`;
    }

    try {
        const response = await fetch("/api/admin/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Invalid Admin Credentials.");
        }

        // Store separate admin auth session
        if (typeof persistAuthSession === "function") {
            persistAuthSession(data);
        }

        if (typeof showNotification === "function") {
            showNotification("Success", "Welcome Administrator. Access Granted.", "success");
        }

        // Open existing Admin Dashboard
        if (typeof switchView === "function") {
            switchView("admin");
        }
        if (typeof loadAdminDashboard === "function") {
            loadAdminDashboard();
        }
    } catch (err) {
        if (typeof showNotification === "function") {
            showNotification("Admin Authentication Failed", err.message, "error");
        } else {
            alert(err.message);
        }
    } finally {
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = `<i data-lucide="log-in" class="w-4 h-4"></i> Admin Sign In`;
        }
        if (typeof initLucide === "function") {
            initLucide();
        }
    }
}
