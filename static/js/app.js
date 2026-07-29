// Core App State
let state = {
    currentUser: null, // Starts unauthenticated
    currentProfile: null,
    recommendations: [],
    applications: [],
    schemes: [],
    currentWizardStep: 1,
    selectedCategory: "All",
    searchQuery: "",
    activeApplyScheme: null,
    uploadedApplyDocs: {}, // doc_name -> { file_name, file_url, status }
    hasEvaluatedQuestionnaire: false
};

document.addEventListener("DOMContentLoaded", async () => {
    // Restore session if user is logged in
    const savedUser = localStorage.getItem("welfare_user");
    const savedToken = localStorage.getItem("welfare_token");

    initLucide();
    setupEventListeners();

    if (savedUser && savedToken) {
        try {
            state.currentUser = JSON.parse(savedUser);
            ApiService.setAuthToken(savedToken);
            updateAuthUI();
            await loadUserData();
            if (state.currentUser.role === "admin") {
                switchView("admin");
            } else {
                switchView("recommendations");
            }
        } catch (e) {
            console.warn("Session restore error:", e);
            logout();
        }
    } else {
        updateAuthUI();
        switchView("auth-landing");
    }

    setLanguage("en");
});

function initLucide() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function setElementText(id, txt) {
    const item = document.getElementById(id);
    if (item) item.textContent = txt;
}

function el(id, txt) {
    setElementText(id, txt);
}

function showNotification(title, message, type = "info") {
    let container = document.getElementById("appToastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "appToastContainer";
        container.className = "fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm";
        document.body.appendChild(container);
    }

    const toneStyles = {
        success: "bg-emerald-600/95 border-emerald-400/60",
        error: "bg-rose-600/95 border-rose-400/60",
        info: "bg-slate-800/95 border-slate-600/60",
        warning: "bg-amber-600/95 border-amber-400/60"
    };

    const toast = document.createElement("div");
    toast.className = `border rounded-2xl px-4 py-3 text-white shadow-xl backdrop-blur ${toneStyles[type] || toneStyles.info}`;
    toast.innerHTML = `<div class="font-semibold text-sm">${title}</div><div class="text-xs opacity-90 mt-1">${message}</div>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2", "transition-all", "duration-300");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function loadUserData() {
    if (!state.currentUser) return;
    try {
        if (state.currentUser.role === "citizen") {
            const p = await ApiService.getProfile();
            state.currentProfile = p || {};
        }
    } catch (e) {
        console.warn("Profile load warning:", e);
    }
}

function persistAuthSession(authData) {
    state.currentUser = authData;
    localStorage.setItem("welfare_user", JSON.stringify(authData));
    if (authData.access_token) {
        localStorage.setItem("welfare_token", authData.access_token);
        ApiService.setAuthToken(authData.access_token);
    }
    updateAuthUI();
}

async function finalizeAuthFlow(authData, defaultView = "recommendations") {
    persistAuthSession(authData);
    showNotification("Welcome", `Signed in as ${authData.name || 'User'}`, "success");

    if (authData.role === "admin") {
        switchView("admin");
    } else {
        await loadUserData();
        switchView(defaultView);
        if (!state.currentProfile || !state.currentProfile.age) {
            openWizardModal();
        }
    }
}

function setupEventListeners() {
    // Navigation links
    document.querySelectorAll(".nav-link").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const view = btn.getAttribute("data-view");
            switchView(view);
        });
    });

    // Language switcher
    const langSelect = document.getElementById("languageSelector");
    if (langSelect) {
        langSelect.addEventListener("change", (e) => {
            setLanguage(e.target.value);
        });
    }

    // Wizard stepper controls
    document.getElementById("btnWizardNext")?.addEventListener("click", () => changeWizardStep(1));
    document.getElementById("btnWizardPrev")?.addEventListener("click", () => changeWizardStep(-1));
    document.getElementById("wizardForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        await submitWizard();
    });

    // Chatbot Drawer
    document.getElementById("btnToggleChat")?.addEventListener("click", toggleChatDrawer);
    document.getElementById("btnCloseChat")?.addEventListener("click", toggleChatDrawer);
    document.getElementById("chatForm")?.addEventListener("submit", sendChatMessage);

    // Search and filter
    document.getElementById("schemeSearchInput")?.addEventListener("input", (e) => {
        state.searchQuery = e.target.value.toLowerCase();
        renderRecommendations();
    });
}

function switchView(viewId) {
    // STRICT ROUTE GUARD: Prevent unauthorized access to protected user views
    const protectedViews = ["recommendations", "applications", "profile", "documents", "admin"];
    if (protectedViews.includes(viewId) && !state.currentUser) {
        showNotification("Authentication Required", "Please log in to access your welfare portal.", "warning");
        document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("hidden"));
        document.getElementById("view-auth-landing")?.classList.remove("hidden");
        updateAuthUI();
        return;
    }

    // STRICT ADMIN GUARD: Block non-admin users from accessing administrative tools
    if (viewId === "admin" && state.currentUser?.role !== "admin") {
        showNotification("Access Denied", "Administrator access required.", "error");
        switchView("recommendations");
        return;
    }

    const isAdmin = state.currentUser?.role === "admin" || viewId === "admin";
    const userPortal = document.getElementById("userLayoutPortal");
    const adminPortal = document.getElementById("adminLayoutPortal");

    if (isAdmin) {
        if (userPortal) userPortal.classList.add("hidden");
        if (adminPortal) adminPortal.classList.remove("hidden");
        const adminView = document.getElementById("view-admin");
        if (adminView) adminView.classList.remove("hidden");
        loadAdminView();
    } else {
        if (adminPortal) adminPortal.classList.add("hidden");
        if (userPortal) userPortal.classList.remove("hidden");

        document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("hidden"));
        const target = document.getElementById(`view-${viewId}`);
        if (target) target.classList.remove("hidden");

        const heroSection = document.getElementById("heroSection");
        if (viewId === "auth-landing" || viewId === "admin-auth" || !state.currentUser) {
            if (heroSection) heroSection.classList.add("hidden");
        } else {
            if (heroSection) heroSection.classList.remove("hidden");
        }

        // Update active nav link
        document.querySelectorAll(".nav-link").forEach(link => {
            if (link.getAttribute("data-view") === viewId) {
                link.classList.add("text-indigo-400", "font-bold");
                link.classList.remove("text-slate-300");
            } else {
                link.classList.remove("text-indigo-400", "font-bold");
                link.classList.add("text-slate-300");
            }
        });

        if (viewId === "recommendations") {
            renderRecommendations();
        } else if (viewId === "applications") {
            loadApplicationsView();
        } else if (viewId === "profile") {
            loadProfileView();
        }
    }

    updateAuthUI();
    initLucide();
}

// AUTH LANDING LOGIC
function toggleLandingAuthMode(mode) {
    const isRegister = mode === "register";
    
    document.getElementById("landingAuthNameGroup").style.display = isRegister ? "block" : "none";
    document.getElementById("landingAuthMobileGroup").style.display = isRegister ? "block" : "none";

    const tabLogin = document.getElementById("tabAuthLogin");
    const tabReg = document.getElementById("tabAuthRegister");
    
    if (isRegister) {
        tabReg.className = "py-2.5 rounded-xl bg-indigo-600 text-white shadow-sm transition";
        tabLogin.className = "py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition";
        document.getElementById("authLandingTitle").textContent = "Create Citizen Account";
        document.getElementById("authLandingSubtitle").textContent = "Register with your details to start personalized government scheme assessment.";
        document.getElementById("btnLandingAuthSubmit").innerHTML = '<i data-lucide="user-plus" class="w-4 h-4"></i> Register New Account';
    } else {
        tabLogin.className = "py-2.5 rounded-xl bg-indigo-600 text-white shadow-sm transition";
        tabReg.className = "py-2.5 rounded-xl text-slate-600 hover:text-slate-900 transition";
        document.getElementById("authLandingTitle").textContent = "Sign In to Welfare Portal";
        document.getElementById("authLandingSubtitle").textContent = "Access personalized scheme recommendations, document verification & applications.";
        document.getElementById("btnLandingAuthSubmit").innerHTML = '<i data-lucide="log-in" class="w-4 h-4"></i> Login to Portal';
    }
    initLucide();
}

// ADMIN AUTH LANDING LOGIC
function toggleAdminAuthMode(mode) {
    const isRegister = mode === "register";

    document.getElementById("adminAuthNameGroup").style.display = isRegister ? "block" : "none";
    document.getElementById("adminAuthMobileGroup").style.display = isRegister ? "block" : "none";
    document.getElementById("adminAuthCodeGroup").style.display = isRegister ? "block" : "none";

    const tabLogin = document.getElementById("tabAdminLogin");
    const tabReg = document.getElementById("tabAdminRegister");

    if (isRegister) {
        tabReg.className = "py-2.5 rounded-xl bg-purple-600 text-white shadow-md transition-all duration-200 flex items-center justify-center gap-1.5";
        tabLogin.className = "py-2.5 rounded-xl text-purple-500 hover:text-purple-800 transition-all duration-200 flex items-center justify-center gap-1.5";
        document.getElementById("adminAuthTitle").textContent = "Create Admin Account";
        document.getElementById("adminAuthSubtitle").textContent = "Register as an administrator with your invite code.";
        document.getElementById("btnAdminAuthSubmit").innerHTML = '<i data-lucide="user-plus" class="w-4 h-4"></i> Register Admin Account';
    } else {
        tabLogin.className = "py-2.5 rounded-xl bg-purple-600 text-white shadow-md transition-all duration-200 flex items-center justify-center gap-1.5";
        tabReg.className = "py-2.5 rounded-xl text-purple-500 hover:text-purple-800 transition-all duration-200 flex items-center justify-center gap-1.5";
        document.getElementById("adminAuthTitle").textContent = "Admin Sign In";
        document.getElementById("adminAuthSubtitle").textContent = "Access the administrative control panel";
        document.getElementById("btnAdminAuthSubmit").innerHTML = '<i data-lucide="log-in" class="w-4 h-4"></i> Admin Sign In';
    }
    initLucide();
}

async function handleAdminAuthFormSubmit(e) {
    e.preventDefault();
    const email = document.getElementById("adminAuthEmail").value.trim();
    const password = document.getElementById("adminAuthPassword").value;
    const name = document.getElementById("adminAuthName").value.trim();
    const mobile = document.getElementById("adminAuthMobile").value.trim();
    const inviteCode = document.getElementById("adminAuthCode").value.trim();
    const isRegister = document.getElementById("adminAuthNameGroup").style.display !== "none";

    try {
        if (isRegister) {
            if (!name || !mobile) {
                showNotification("Validation Error", "Please provide your Name and Mobile Number.", "error");
                return;
            }
            if (!inviteCode || inviteCode !== "ADMIN2026") {
                showNotification("Invalid Invite Code", "The admin invite code is invalid. Contact the system administrator.", "error");
                return;
            }
            const authData = await ApiService.register(name, email, mobile, password, "admin");
            showNotification("Admin Registration Successful", `Welcome ${authData.name || 'Admin'}! You now have administrative access.`, "success");
            await finalizeAuthFlow(authData, "admin");
            return;
        }

        const authData = await ApiService.login(email, password);
        if (authData.role !== "admin") {
            showNotification("Access Denied", "This portal is for administrators only. Please use the Citizen Portal.", "error");
            logout();
            return;
        }
        await finalizeAuthFlow(authData, "admin");
    } catch (err) {
        const errorTitle = isRegister ? "Admin Registration Failed" : "Admin Authentication Failed";
        showNotification(errorTitle, err.message || "Invalid credentials or request failed.", "error");
    }
}

async function handleAuthLandingFormSubmit(e) {
    e.preventDefault();
    const email = document.getElementById("landingAuthEmail").value.trim();
    const password = document.getElementById("landingAuthPassword").value;
    const name = document.getElementById("landingAuthName").value.trim();
    const mobile = document.getElementById("landingAuthMobile").value.trim();
    const isRegister = document.getElementById("landingAuthNameGroup").style.display !== "none";

    try {
        if (isRegister) {
            if (!name || !mobile) {
                showNotification("Validation Error", "Please provide your Name and Mobile Number for registration.", "error");
                return;
            }
            const authData = await ApiService.register(name, email, mobile, password, "citizen");
            showNotification("Registration Successful", `Welcome ${authData.name || 'Citizen'}! Complete the quick questionnaire to view all eligible schemes.`, "success");
            await finalizeAuthFlow(authData, "recommendations");
            openWizardModal();
            return;
        }

        const authData = await ApiService.login(email, password);
        if (authData.role === "admin") {
            await finalizeAuthFlow(authData, "admin");
        } else {
            await finalizeAuthFlow(authData, "recommendations");
        }
    } catch (err) {
        const errorTitle = isRegister ? "Registration Failed" : "Authentication Failed";
        showNotification(errorTitle, err.message || "Invalid credentials or request failed.", "error");
    }
}

async function quickDemoLogin(role) {
    try {
        let authData;
        if (role === "citizen") {
            try {
                authData = await ApiService.login("citizen@welfare.gov", "password123");
            } catch (e) {
                // Auto-register if not exists
                authData = await ApiService.register("Demo Citizen", "citizen@welfare.gov", "9876543210", "password123", "citizen");
            }
            await finalizeAuthFlow(authData, "recommendations");
        } else {
            try {
                authData = await ApiService.login("admin@welfare.gov", "admin123");
            } catch (e) {
                // Auto-register if not exists
                authData = await ApiService.register("System Admin", "admin@welfare.gov", "9999999999", "admin123", "admin");
            }
            await finalizeAuthFlow(authData, "admin");
        }
    } catch (e) {
        showNotification("Demo Login Error", e.message || "Demo account unavailable", "error");
    }
}

function logout() {
    ApiService.setAuthToken(null);
    localStorage.removeItem("welfare_user");
    localStorage.removeItem("welfare_token");
    state.currentUser = null;
    state.currentProfile = null;
    state.recommendations = [];
    state.applications = [];
    state.hasEvaluatedQuestionnaire = false;
    updateAuthUI();
    showNotification("Logged Out", "You have been logged out safely.", "info");
    switchView("auth-landing");
}

function updateAuthUI() {
    const userPortal = document.getElementById("userLayoutPortal");
    const adminPortal = document.getElementById("adminLayoutPortal");
    const userContainer = document.getElementById("navUserContainer");
    const authBtnContainer = document.getElementById("navAuthBtnContainer");

    const isAdmin = state.currentUser?.role === "admin";

    if (isAdmin) {
        // RENDER ONLY DEDICATED ADMIN PORTAL LAYOUT
        if (userPortal) userPortal.classList.add("hidden");
        if (adminPortal) adminPortal.classList.remove("hidden");

        const adminNameEl = document.getElementById("adminProfileName");
        if (adminNameEl) adminNameEl.textContent = `${state.currentUser.name || "Admin"} 👤`;
    } else {
        // RENDER ONLY CITIZEN USER PORTAL LAYOUT
        if (adminPortal) adminPortal.classList.add("hidden");
        if (userPortal) userPortal.classList.remove("hidden");

        if (state.currentUser) {
            if (userContainer) {
                userContainer.style.display = "flex";
                const nameEl = document.getElementById("userNameLabel");
                const roleEl = document.getElementById("userRoleBadge");
                if (nameEl) nameEl.textContent = state.currentUser.name || "Citizen";
                if (roleEl) roleEl.textContent = "CITIZEN";
            }
            if (authBtnContainer) authBtnContainer.style.display = "none";
            
            const welcomeHeading = document.getElementById("welcomeUserHeading");
            if (welcomeHeading) welcomeHeading.textContent = `Welcome, ${state.currentUser.name}`;
        } else {
            if (userContainer) userContainer.style.display = "none";
            if (authBtnContainer) authBtnContainer.style.display = "flex";
        }
    }
}

async function loadUserData() {
    try {
        const profile = await ApiService.getProfile();
        if (profile) {
            state.currentProfile = profile;
        }
        const apps = await ApiService.getApplications();
        state.applications = apps || [];

        const userKey = state.currentUser?.email || "default";
        const isEvaluated = localStorage.getItem(`welfare_evaluated_${userKey}`) === "true";
        state.hasEvaluatedQuestionnaire = isEvaluated;

        if (isEvaluated) {
            await evaluateCurrentProfile();
        } else {
            renderRecommendations();
            updateQuickStats(0, state.applications.length);
            if (state.currentUser && state.currentUser.role === "citizen") {
                openWizardModal();
            }
        }
    } catch (e) {
        console.warn("Load user data exception:", e);
    }
}

// WIZARD QUESTIONNAIRE MODAL
function openWizardModal() {
    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }
    state.currentWizardStep = 1;
    prefillWizardForm();
    updateWizardStepUI();
    document.getElementById("wizardModal")?.classList.remove("hidden");
}

function closeWizardModal() {
    document.getElementById("wizardModal")?.classList.add("hidden");
}

function prefillWizardForm() {
    if (!state.currentProfile) return;
    const p = state.currentProfile;
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined) el.value = val;
    };
    const setCheck = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.checked = Boolean(val);
    };

    setVal("wizName", p.name || state.currentUser?.name || "");
    setVal("wizMobile", p.mobile_number || state.currentUser?.mobile_number || "");
    setVal("wizAge", p.age || 25);
    setVal("wizGender", p.gender || "Male");
    setVal("wizMarital", p.marital_status || "Single");
    setVal("wizState", p.state || "Uttar Pradesh");
    setVal("wizDistrict", p.district || "Varanasi");
    setVal("wizRuralUrban", p.rural_urban || "Rural");
    setVal("wizEducation", p.education || "Secondary");
    setVal("wizOccupation", p.occupation || "Farmer");
    setVal("wizIncome", p.annual_income || 150000);
    setVal("wizCaste", p.caste_category || "General");

    setCheck("wizFarmer", p.farmer_status);
    setCheck("wizStudent", p.student_status);
    setCheck("wizDisability", p.disability_status);
    setCheck("wizSenior", p.senior_citizen_status || (p.age >= 60));
    setCheck("wizWidow", p.widow_status);
    setCheck("wizBPL", p.bpl_status);
    setCheck("wizAadhaar", p.aadhaar_available !== false);
    setCheck("wizBank", p.bank_account_available !== false);
}

function changeWizardStep(delta) {
    state.currentWizardStep = Math.max(1, Math.min(4, state.currentWizardStep + delta));
    updateWizardStepUI();
}

function updateWizardStepUI() {
    document.querySelectorAll(".wizard-step-panel").forEach((panel, idx) => {
        if (idx + 1 === state.currentWizardStep) {
            panel.classList.remove("hidden");
        } else {
            panel.classList.add("hidden");
        }
    });

    const prevBtn = document.getElementById("btnWizardPrev");
    const nextBtn = document.getElementById("btnWizardNext");
    const submitBtn = document.getElementById("btnWizardSubmit");

    if (prevBtn) prevBtn.style.display = state.currentWizardStep === 1 ? "none" : "inline-flex";
    if (nextBtn) nextBtn.style.display = state.currentWizardStep === 4 ? "none" : "inline-flex";
    if (submitBtn) submitBtn.style.display = state.currentWizardStep === 4 ? "inline-flex" : "none";

    document.querySelectorAll(".wizard-badge").forEach((badge, idx) => {
        const stepNum = idx + 1;
        badge.className = "wizard-badge w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-bold text-xs sm:text-sm transition-all";
        if (stepNum === state.currentWizardStep) {
            badge.classList.add("wizard-step-active");
        } else if (stepNum < state.currentWizardStep) {
            badge.classList.add("wizard-step-completed");
        } else {
            badge.classList.add("wizard-step-pending");
        }
    });
}

async function submitWizard(e) {
    if (e && typeof e.preventDefault === "function") {
        e.preventDefault();
        e.stopPropagation();
    }

    const getVal = (id, def = "") => {
        const el = document.getElementById(id);
        return el ? el.value : def;
    };
    const getCheck = (id) => {
        const el = document.getElementById(id);
        return el ? Boolean(el.checked) : false;
    };

    const ageVal = parseInt(getVal("wizAge", "25")) || 25;
    const incomeVal = parseFloat(getVal("wizIncome", "150000")) || 150000;
    const maritalVal = getVal("wizMarital", "Single");

    state.currentProfile = {
        name: getVal("wizName", state.currentUser?.name || "Citizen").trim(),
        mobile_number: getVal("wizMobile", state.currentUser?.mobile_number || "").trim(),
        age: ageVal,
        gender: getVal("wizGender", "Male"),
        marital_status: maritalVal,
        state: getVal("wizState", "Uttar Pradesh").trim(),
        district: getVal("wizDistrict", "Varanasi").trim(),
        rural_urban: getVal("wizRuralUrban", "Rural"),
        education: getVal("wizEducation", "Secondary"),
        occupation: getVal("wizOccupation", "Farmer"),
        annual_income: incomeVal,
        caste_category: getVal("wizCaste", "General"),
        farmer_status: getCheck("wizFarmer"),
        student_status: getCheck("wizStudent"),
        disability_status: getCheck("wizDisability"),
        senior_citizen_status: getCheck("wizSenior") || (ageVal >= 60),
        widow_status: getCheck("wizWidow") || (maritalVal === "Widow"),
        bpl_status: getCheck("wizBPL") || (incomeVal <= 150000),
        aadhaar_available: getCheck("wizAadhaar"),
        bank_account_available: getCheck("wizBank")
    };

    state.hasEvaluatedQuestionnaire = true;
    const userKey = state.currentUser?.email || "default";
    localStorage.setItem(`welfare_evaluated_${userKey}`, "true");

    // 1. Close modal and ensure view remains stable
    closeWizardModal();
    switchView("recommendations");

    // 2. Inline loading indicator in schemesGrid
    const grid = document.getElementById("schemesGrid");
    if (grid) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                <div class="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <h3 class="text-base font-bold text-slate-800">Evaluating Schemes with AI...</h3>
                <p class="text-xs text-slate-500 mt-1">Matching your questionnaire answers with government eligibility rules.</p>
            </div>
        `;
    }

    try {
        await ApiService.updateProfile(state.currentProfile);
    } catch (err) {
        console.warn("Save profile warning:", err);
    }

    // 3. Run evaluation & render schemes cleanly
    await evaluateCurrentProfile();

    showNotification("AI Evaluation Completed", "Personalized scheme recommendations updated for your profile.", "success");
    return false;
}

async function evaluateCurrentProfile() {
    try {
        const res = await ApiService.evaluateProfile(state.currentProfile || {});
        state.recommendations = res.recommendations || [];
        renderRecommendations();
        const eligibleList = state.recommendations.filter(r => r.is_eligible);
        updateQuickStats(eligibleList.length, state.applications.length);
    } catch (e) {
        console.warn("Evaluation API exception:", e);
    }
}

function updateQuickStats(eligibleCount, appliedCount) {
    const elEligible = document.getElementById("statEligibleCount");
    const elApplied = document.getElementById("statAppliedCount");
    if (elEligible) elEligible.textContent = eligibleCount || "0";
    if (elApplied) elApplied.textContent = appliedCount || state.applications.length || "0";
}

// RECOMMENDATIONS VIEW (DISPLAYING ONLY ELIGIBLE SCHEMES)
function renderRecommendations() {
    const grid = document.getElementById("schemesGrid");
    if (!grid) return;

    grid.innerHTML = "";

    // If user has not completed questionnaire yet, prompt them to run AI Eligibility Check
    if (!state.hasEvaluatedQuestionnaire) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                <div class="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-4">
                    <i data-lucide="wand-2" class="w-8 h-8"></i>
                </div>
                <h3 class="text-xl font-extrabold text-slate-900">Start Your AI Eligibility Assessment</h3>
                <p class="text-slate-500 text-xs mt-1.5 max-w-md mx-auto mb-6">Click the button below to answer a few quick questions (Age, Location, Income, Occupation, Category & Special Status). Our AI will compare your profile with government scheme rules and display ONLY the schemes you qualify for.</p>
                <button onclick="openWizardModal()" class="px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-xl transition flex items-center gap-2 mx-auto cursor-pointer">
                    <i data-lucide="sparkles" class="w-4 h-4"></i> ⚡ Start AI Eligibility Check
                </button>
            </div>
        `;
        initLucide();
        return;
    }

    // STRICT REQUIREMENT: Display ONLY schemes where is_eligible === true!
    let eligibleOnly = state.recommendations.filter(item => item.is_eligible === true);

    let filtered = eligibleOnly.filter(item => {
        const matchesCategory = state.selectedCategory === "All" || item.category === state.selectedCategory;
        const matchesQuery = !state.searchQuery || item.scheme_name.toLowerCase().includes(state.searchQuery) || item.category.toLowerCase().includes(state.searchQuery);
        return matchesCategory && matchesQuery;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                <div class="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-3">
                    <i data-lucide="shield-alert" class="w-8 h-8"></i>
                </div>
                <h3 class="text-lg font-bold text-slate-800">No Eligible Schemes Matched</h3>
                <p class="text-slate-500 text-xs mt-1 max-w-md mx-auto mb-5">Our AI evaluated scheme criteria against your profile attributes. No matching schemes were found for your current answers.</p>
                <button onclick="openWizardModal()" class="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-xs shadow-md">⚡ Re-run AI Eligibility Questionnaire</button>
            </div>
        `;
        initLucide();
        return;
    }

    filtered.forEach(rec => {
        const card = document.createElement("div");
        card.className = "scheme-card bg-white rounded-2xl border border-slate-200/80 p-6 flex flex-col justify-between shadow-sm relative overflow-hidden";

        const whyEligibleHtml = rec.reasons_why_eligible.map(r => `
            <li class="flex items-start text-xs text-emerald-800 gap-1.5">
                <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5"></i>
                <span>${r}</span>
            </li>
        `).join("");

        const reqDocsHtml = rec.required_documents.map(d => `
            <span class="inline-flex items-center gap-1 text-[11px] font-medium bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md">
                <i data-lucide="file" class="w-3 h-3 text-indigo-500"></i> ${d}
            </span>
        `).join(" ");

        card.innerHTML = `
            <div class="top-content">
                <div class="flex items-center justify-between gap-2 mb-3">
                    <span class="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">${rec.category}</span>
                    <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1 shadow-sm">
                        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600"></i> Eligible (${rec.match_score}%)
                    </span>
                </div>
                <h3 class="text-base font-extrabold text-slate-900 leading-snug mb-2">${rec.scheme_name}</h3>
                <p class="text-xs text-slate-600 line-clamp-2 mb-4">${rec.scheme_details.description}</p>
                
                <!-- Financial Benefits callout -->
                <div class="p-3 rounded-xl bg-indigo-50/70 border border-indigo-100 mb-4">
                    <div class="text-[11px] font-bold text-indigo-900 uppercase tracking-wider mb-0.5">Scheme Benefits:</div>
                    <div class="text-xs font-bold text-indigo-700">${rec.benefits}</div>
                </div>

                <!-- Why Eligible Section -->
                <div class="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-100 mb-4">
                    <div class="text-xs font-bold text-emerald-900 mb-1.5 flex items-center gap-1">
                        <i data-lucide="sparkles" class="w-4 h-4 text-emerald-600"></i> Why You Are Eligible:
                    </div>
                    <ul class="space-y-1">${whyEligibleHtml}</ul>
                </div>

                <!-- Required Documents List -->
                <div class="mb-4">
                    <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Required Documents:</span>
                    <div class="flex flex-wrap gap-1.5">${reqDocsHtml}</div>
                </div>
            </div>

            <!-- Card Action Footer -->
            <div class="bottom-actions pt-4 border-t border-slate-100 flex items-center gap-2">
                <button onclick="openSchemeDetailModal('${rec.scheme_id}')" class="flex-1 py-2.5 px-3 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition flex items-center justify-center gap-1">
                    <i data-lucide="eye" class="w-3.5 h-3.5"></i> Details
                </button>
                <button onclick="openApplyModal('${rec.scheme_id}')" class="flex-1 py-2.5 px-3 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition flex items-center justify-center gap-1.5 shadow-md cursor-pointer">
                    <i data-lucide="send" class="w-3.5 h-3.5"></i> Apply Now
                </button>
            </div>
        `;

        grid.appendChild(card);
    });

    initLucide();
}

function filterCategory(category) {
    state.selectedCategory = category;
    document.querySelectorAll(".category-chip").forEach(chip => {
        if (chip.getAttribute("data-category") === category) {
            chip.className = "category-chip px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-sm cursor-pointer transition";
        } else {
            chip.className = "category-chip px-4 py-2 rounded-xl text-xs font-medium bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 cursor-pointer transition";
        }
    });
    renderRecommendations();
}

// APPLY MODAL & STRICT JPEG DOCUMENT UPLOAD LOGIC
async function openApplyModal(schemeId) {
    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }

    let rec = state.recommendations.find(r => r.scheme_id === schemeId || r.id === schemeId);
    let scheme = rec ? (rec.scheme_details || rec) : state.schemes.find(s => s.id === schemeId);

    if (!scheme) {
        try {
            const allSchemes = await ApiService.getSchemes();
            state.schemes = allSchemes || [];
            scheme = state.schemes.find(s => s.id === schemeId);
        } catch (err) {
            console.warn("Fetch scheme error:", err);
        }
    }

    if (!scheme) {
        showNotification("Scheme Error", "Could not load scheme details for application.", "error");
        return;
    }

    state.activeApplyScheme = scheme;
    state.uploadedApplyDocs = {}; // Clear uploaded state

    document.getElementById("applyModalSchemeTitle").textContent = `Apply for ${scheme.name}`;
    
    const container = document.getElementById("applyDocumentsContainer");
    container.innerHTML = "";

    const reqDocs = scheme.required_documents || ["Aadhaar Card", "Income Certificate", "Residence Certificate", "Active Bank Passbook"];

    reqDocs.forEach((docName, idx) => {
        state.uploadedApplyDocs[docName] = { status: "Missing", file_name: null, file_url: null };

        const safeId = `doc_${idx}_${docName.replace(/[^a-zA-Z0-9]/g, '_')}`;
        const row = document.createElement("div");
        row.className = "p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3";
        row.id = `docRow_${safeId}`;

        const escapedName = docName.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

        row.innerHTML = `
            <div>
                <div class="flex items-center gap-2">
                    <i data-lucide="file-check" class="w-4 h-4 text-indigo-600"></i>
                    <h4 class="text-xs font-bold text-slate-900">${escapedName}</h4>
                </div>
                <div class="text-[11px] text-slate-400 mt-0.5">JPEG format (.jpg / .jpeg) required</div>
            </div>

            <div class="flex items-center gap-2">
                <span id="docBadge_${safeId}" class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200">
                    Missing
                </span>
                <label class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs cursor-pointer transition shadow-sm flex items-center gap-1">
                    <i data-lucide="upload-cloud" class="w-3.5 h-3.5"></i> Upload JPEG
                    <input type="file" id="fileInput_${safeId}" accept=".jpg,.jpeg,image/jpeg" class="hidden">
                </label>
            </div>
        `;
        container.appendChild(row);

        const fileInput = row.querySelector(`#fileInput_${safeId}`);
        if (fileInput) {
            fileInput.addEventListener("change", (e) => {
                e.preventDefault();
                e.stopPropagation();
                handleJPEGFileSelect(e, docName, safeId);
            });
        }
    });

    checkApplyButtonState();
    document.getElementById("applyModal")?.classList.remove("hidden");
    initLucide();
}

function closeApplyModal() {
    document.getElementById("applyModal")?.classList.add("hidden");
    state.activeApplyScheme = null;
    state.uploadedApplyDocs = {};
}

async function handleJPEGFileSelect(event, docName, safeId) {
    if (event && event.preventDefault) {
        event.preventDefault();
        event.stopPropagation();
    }

    const file = event.target.files[0];
    if (!file) return;

    const filename = file.name.toLowerCase();
    const ext = filename.split('.').pop();
    const isJpegExt = ext === "jpg" || ext === "jpeg";
    const isJpegMime = file.type && file.type.includes("jpeg");

    // STRICT JPEG VALIDATION
    if (!isJpegExt && !isJpegMime) {
        event.target.value = ""; // Reset file input
        showNotification("Invalid File Format", "Only JPEG (.jpg / .jpeg) image documents are allowed!", "error");
        return;
    }

    const badgeEl = document.getElementById(`docBadge_${safeId}`);
    if (badgeEl) {
        badgeEl.textContent = "Uploading...";
        badgeEl.className = "px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200";
    }

    try {
        const uploadRes = await ApiService.uploadDocumentFile(file, docName);
        state.uploadedApplyDocs[docName] = {
            status: "Uploaded",
            file_name: uploadRes.file_name,
            file_url: uploadRes.file_url
        };

        if (badgeEl) {
            badgeEl.textContent = "Uploaded (JPEG ✓)";
            badgeEl.className = "px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200";
        }
        showNotification("Uploaded", `Successfully uploaded ${docName} in JPEG format`, "success");
    } catch (err) {
        if (badgeEl) {
            badgeEl.textContent = "Upload Failed";
            badgeEl.className = "px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200";
        }
        showNotification("Upload Error", err.message || "Failed to upload document", "error");
    }

    checkApplyButtonState();
}

function checkApplyButtonState() {
    const btn = document.getElementById("btnSubmitApplication");
    if (!btn || !state.activeApplyScheme) return;

    const reqDocs = state.activeApplyScheme.required_documents || [];
    const allUploaded = reqDocs.every(d => state.uploadedApplyDocs[d] && state.uploadedApplyDocs[d].status === "Uploaded");

    btn.disabled = !allUploaded;
}

async function submitApplicationWithDocs() {
    if (!state.activeApplyScheme) return;

    const schemeId = state.activeApplyScheme.id;
    const schemeName = state.activeApplyScheme.name;

    const docPayload = {};
    Object.keys(state.uploadedApplyDocs).forEach(d => {
        docPayload[d] = state.uploadedApplyDocs[d].file_url || state.uploadedApplyDocs[d].file_name || "document.jpg";
    });

    try {
        await ApiService.applyForScheme(schemeId, docPayload);
        closeApplyModal();

        // DISPLAY MANDATORY SUCCESS NOTIFICATION BANNER
        showNotification("Successfully Applied", `Successfully Applied for ${schemeName}`, "success");
        
        await loadUserData();
        switchView("applications");
    } catch (err) {
        showNotification("Application Notice", err.message || "Failed to submit application", "error");
    }
}

// SCHEME DETAIL MODAL
function openSchemeDetailModal(schemeId) {
    const rec = state.recommendations.find(r => r.scheme_id === schemeId);
    if (!rec) return;

    const modal = document.getElementById("schemeDetailModal");
    const container = document.getElementById("schemeDetailContent");
    if (!modal || !container) return;

    container.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <div>
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">${rec.category}</span>
                <h2 class="text-xl font-extrabold text-slate-900 mt-2">${rec.scheme_name}</h2>
            </div>
            <button onclick="closeSchemeDetailModal()" class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200">
                <i data-lucide="x" class="w-5 h-5"></i>
            </button>
        </div>

        <div class="space-y-4">
            <div>
                <h4 class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">Description</h4>
                <p class="text-xs text-slate-700 leading-relaxed">${rec.scheme_details.description}</p>
            </div>

            <div class="p-4 rounded-xl bg-indigo-50 border border-indigo-100">
                <h4 class="text-xs font-bold uppercase text-indigo-900 tracking-wider mb-1">Financial Benefits</h4>
                <p class="text-xs font-bold text-indigo-700">${rec.benefits}</p>
            </div>

            <div>
                <h4 class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2">Required Documents</h4>
                <div class="flex flex-wrap gap-2">
                    ${rec.required_documents.map(d => `<span class="px-3 py-1 rounded-lg bg-slate-100 text-xs font-semibold text-slate-700 flex items-center gap-1.5"><i data-lucide="file-check-2" class="w-3.5 h-3.5 text-indigo-600"></i> ${d}</span>`).join('')}
                </div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
                <a href="${rec.official_link}" target="_blank" class="flex-1 py-3 px-4 rounded-xl bg-slate-100 text-slate-700 text-center font-semibold text-xs hover:bg-slate-200 transition flex items-center justify-center gap-2">
                    <i data-lucide="external-link" class="w-4 h-4"></i> Official Portal
                </a>
                <button onclick="closeSchemeDetailModal(); openApplyModal('${rec.scheme_id}');" class="flex-1 py-3 px-4 rounded-xl bg-indigo-600 text-white text-center font-bold text-xs hover:bg-indigo-700 transition flex items-center justify-center gap-2 shadow-md">
                    <i data-lucide="send" class="w-4 h-4"></i> Apply Now
                </button>
            </div>
        </div>
    `;

    modal.classList.remove("hidden");
    initLucide();
}

function closeSchemeDetailModal() {
    document.getElementById("schemeDetailModal")?.classList.add("hidden");
}

// MY APPLICATIONS TRACKER & TIMELINE STEPPER
state.appTrackerFilter = "All";

function setAppTrackerFilter(filterName) {
    state.appTrackerFilter = filterName;

    document.querySelectorAll(".app-filter-chip").forEach(chip => {
        chip.className = "app-filter-chip px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition cursor-pointer";
    });
    const activeChip = document.getElementById(`appFilter-${filterName.replace(/\s+/g, '_')}`);
    if (activeChip) {
        activeChip.className = "app-filter-chip px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-sm transition cursor-pointer";
    }
    filterApplicationsTracker();
}

function filterApplicationsTracker() {
    const searchVal = (document.getElementById("appTrackerSearch")?.value || "").toLowerCase().trim();
    const filterStatus = state.appTrackerFilter || "All";

    const filtered = (state.applications || []).filter(app => {
        const matchesSearch = !searchVal || 
            (app.scheme_name && app.scheme_name.toLowerCase().includes(searchVal)) ||
            (app.id && app.id.toLowerCase().includes(searchVal));
        const matchesStatus = filterStatus === "All" || app.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    renderApplicationsList(filtered);
}

async function loadApplicationsView() {
    const trackerContainer = document.getElementById("applicationsListContainer");
    if (!trackerContainer) return;

    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }

    try {
        const apps = await ApiService.getApplications();
        state.applications = apps || [];
        filterApplicationsTracker();
    } catch (e) {
        console.error("App load error:", e);
    }
}

function renderApplicationsList(apps) {
    const trackerContainer = document.getElementById("applicationsListContainer");
    if (!trackerContainer) return;

    trackerContainer.innerHTML = "";

    if (apps.length === 0) {
        trackerContainer.innerHTML = `
            <div class="text-center py-12 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
                <i data-lucide="inbox" class="w-12 h-12 text-slate-400 mx-auto mb-3"></i>
                <h3 class="text-base font-bold text-slate-800">No applications found</h3>
                <p class="text-slate-500 text-xs mt-1 mb-4">Explore your eligible schemes and submit an application to track progress here.</p>
                <button onclick="switchView('recommendations')" class="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-xs shadow-md">View Matched Schemes</button>
            </div>
        `;
        initLucide();
        return;
    }

    apps.forEach(app => {
        const card = document.createElement("div");
        card.className = "bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:shadow-md transition space-y-4";

        let statusBadgeClass = "bg-indigo-50 text-indigo-700 border-indigo-200";
        let progressWidth = "33%";
        let step2Icon = "⏱️";
        let step2Bg = "bg-indigo-600";
        let step2Status = "In Progress";
        let step3Icon = "⏳";
        let step3Bg = "bg-slate-300";
        let step3Status = "Pending";

        if (app.status === "Approved") {
            statusBadgeClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
            progressWidth = "100%";
            step2Icon = "✓";
            step2Bg = "bg-emerald-600";
            step2Status = "Verified";
            step3Icon = "✓";
            step3Bg = "bg-emerald-600";
            step3Status = "Approved";
        } else if (app.status === "Under Verification") {
            statusBadgeClass = "bg-amber-50 text-amber-800 border-amber-200";
            progressWidth = "66%";
            step2Icon = "🔍";
            step2Bg = "bg-amber-500";
            step2Status = "Reviewing";
            step3Icon = "⏳";
            step3Bg = "bg-slate-300";
            step3Status = "Pending";
        } else if (app.status === "Rejected") {
            statusBadgeClass = "bg-rose-50 text-rose-700 border-rose-200";
            progressWidth = "100%";
            step2Icon = "✓";
            step2Bg = "bg-emerald-600";
            step2Status = "Reviewed";
            step3Icon = "✕";
            step3Bg = "bg-rose-600";
            step3Status = "Rejected";
        }

        const uploadedDocs = app.uploaded_documents || {};
        const docsCount = Object.keys(uploadedDocs).length;

        card.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs font-extrabold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">App Ref: ${app.id}</span>
                        <span class="text-[11px] text-slate-400">Applied: ${app.applied_date || 'Recent'}</span>
                    </div>
                    <h3 class="text-base font-extrabold text-slate-900">${app.scheme_name}</h3>
                </div>
                <span class="px-3.5 py-1.5 rounded-full text-xs font-extrabold border ${statusBadgeClass} flex items-center gap-1.5 self-start sm:self-center shadow-xs">
                    <i data-lucide="clock" class="w-3.5 h-3.5"></i> ${app.status}
                </span>
            </div>

            <!-- INTERACTIVE PROGRESS TIMELINE STEPPER -->
            <div class="py-2 px-4 rounded-2xl bg-slate-50 border border-slate-200/70">
                <div class="flex items-center justify-between relative py-2">
                    <div class="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-1 bg-slate-200 z-0"></div>
                    <div class="absolute left-6 top-1/2 -translate-y-1/2 h-1 bg-indigo-600 z-0 transition-all duration-500" style="width: calc(${progressWidth} - 24px);"></div>

                    <!-- Step 1 -->
                    <div class="relative z-10 flex flex-col items-center">
                        <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow">✓</div>
                        <span class="text-[10px] font-bold text-slate-800 mt-1">Submitted</span>
                        <span class="text-[9px] text-slate-400">${app.applied_date || 'Done'}</span>
                    </div>

                    <!-- Step 2 -->
                    <div class="relative z-10 flex flex-col items-center">
                        <div class="w-7 h-7 rounded-full ${step2Bg} text-white flex items-center justify-center text-xs font-bold shadow">${step2Icon}</div>
                        <span class="text-[10px] font-bold text-slate-800 mt-1">Verification</span>
                        <span class="text-[9px] text-slate-400">${step2Status}</span>
                    </div>

                    <!-- Step 3 -->
                    <div class="relative z-10 flex flex-col items-center">
                        <div class="w-7 h-7 rounded-full ${step3Bg} text-white flex items-center justify-center text-xs font-bold shadow">${step3Icon}</div>
                        <span class="text-[10px] font-bold text-slate-800 mt-1">Final Status</span>
                        <span class="text-[9px] text-slate-400">${step3Status}</span>
                    </div>
                </div>
            </div>

            ${app.remarks ? `
                <div class="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200/80 text-xs text-amber-900 flex items-start gap-2.5">
                    <i data-lucide="message-square" class="w-4 h-4 text-amber-600 shrink-0 mt-0.5"></i>
                    <div>
                        <strong>Official Remarks:</strong> ${app.remarks}
                    </div>
                </div>
            ` : ''}

            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                <span class="text-xs text-slate-500 flex items-center gap-1.5">
                    <i data-lucide="file-check-2" class="w-4 h-4 text-indigo-600"></i> ${docsCount} Verified JPEG Document(s) Attached
                </span>
                
                <div class="flex items-center gap-2">
                    <button onclick="printAppReceipt('${app.id}')" class="px-3 py-1.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-bold flex items-center gap-1.5 transition cursor-pointer">
                        <i data-lucide="printer" class="w-3.5 h-3.5 text-slate-600"></i> Receipt
                    </button>
                    <button onclick="openAppDetailModal('${app.id}')" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center gap-1.5 transition shadow-sm cursor-pointer">
                        <i data-lucide="eye" class="w-3.5 h-3.5"></i> Details
                    </button>
                </div>
            </div>
        `;
        trackerContainer.appendChild(card);
    });

    initLucide();
}

function openAppDetailModal(appId) {
    const app = (state.applications || []).find(a => a.id === appId);
    if (!app) return;

    const modal = document.getElementById("applicationDetailModal");
    const container = document.getElementById("applicationDetailContent");
    if (!modal || !container) return;

    let statusBadge = "bg-indigo-50 text-indigo-700 border-indigo-200";
    if (app.status === "Approved") statusBadge = "bg-emerald-50 text-emerald-700 border-emerald-200";
    else if (app.status === "Under Verification") statusBadge = "bg-amber-50 text-amber-800 border-amber-200";
    else if (app.status === "Rejected") statusBadge = "bg-rose-50 text-rose-700 border-rose-200";

    const docs = app.uploaded_documents || {};
    const docKeys = Object.keys(docs);

    container.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <div>
                <span class="px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold uppercase">Application Reference</span>
                <h3 class="text-xl font-extrabold text-slate-900 mt-1">${app.scheme_name}</h3>
                <p class="text-xs text-slate-400 mt-0.5">Reference ID: ${app.id}</p>
            </div>
            <button onclick="closeAppDetailModal()" class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200 cursor-pointer">
                <i data-lucide="x" class="w-5 h-5"></i>
            </button>
        </div>

        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase block">Application Status</span>
                    <span class="inline-block mt-1 px-3 py-1 rounded-full font-bold border ${statusBadge}">${app.status}</span>
                </div>
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase block">Applied Date</span>
                    <span class="font-bold text-slate-800 mt-1 block">${app.applied_date || 'N/A'}</span>
                </div>
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase block">Applicant Name</span>
                    <span class="font-bold text-slate-800 mt-1 block">${app.user_name || state.currentUser?.name || 'Citizen'}</span>
                </div>
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase block">Applicant Email</span>
                    <span class="font-bold text-slate-800 mt-1 block">${app.user_email || state.currentUser?.email || 'N/A'}</span>
                </div>
            </div>

            ${app.remarks ? `
                <div class="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-950">
                    <strong class="font-bold flex items-center gap-1.5 mb-1"><i data-lucide="message-square" class="w-4 h-4 text-amber-600"></i> Official Officer Remarks:</strong>
                    <p class="text-amber-900">${app.remarks}</p>
                </div>
            ` : ''}

            <div>
                <h4 class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-2">Attached JPEG Document Proofs</h4>
                <div class="space-y-2">
                    ${docKeys.length > 0 ? docKeys.map(dName => {
                        const url = docs[dName];
                        return `
                            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                                <div class="flex items-center gap-2">
                                    <i data-lucide="image" class="w-4 h-4 text-indigo-600"></i>
                                    <span class="font-bold text-slate-800">${dName}</span>
                                </div>
                                <a href="${url}" target="_blank" class="text-indigo-600 font-bold hover:underline text-[11px] flex items-center gap-1">
                                    <i data-lucide="external-link" class="w-3.5 h-3.5"></i> View JPEG File
                                </a>
                            </div>
                        `;
                    }).join('') : '<p class="text-xs text-slate-400 italic">No document links attached.</p>'}
                </div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
                <button onclick="printAppReceipt('${app.id}')" class="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 font-bold text-xs flex items-center gap-1.5 cursor-pointer">
                    <i data-lucide="printer" class="w-4 h-4"></i> Print Official Receipt
                </button>
                <button onclick="closeAppDetailModal()" class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs cursor-pointer">
                    Close
                </button>
            </div>
        </div>
    `;

    modal.classList.remove("hidden");
    initLucide();
}

function closeAppDetailModal() {
    document.getElementById("applicationDetailModal")?.classList.add("hidden");
}

function printAppReceipt(appId) {
    const app = (state.applications || []).find(a => a.id === appId);
    if (!app) return;

    const u = state.currentUser || {};
    const printWindow = window.open("", "_blank", "width=800,height=900");
    if (!printWindow) return;

    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Official Application Acknowledgement - ${app.id}</title>
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #1e293b; line-height: 1.5; }
                .header { border-bottom: 2px solid #4f46e5; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
                .title { font-size: 22px; font-weight: bold; color: #1e1b4b; text-transform: uppercase; }
                .subtitle { font-size: 12px; color: #64748b; margin-top: 4px; }
                .badge { display: inline-block; padding: 6px 14px; background: #e0e7ff; color: #3730a3; font-weight: bold; border-radius: 20px; font-size: 13px; }
                .section { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
                .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px; }
                .label { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; }
                .val { font-size: 14px; font-weight: bold; color: #0f172a; margin-top: 2px; }
                .footer { border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 40px; font-size: 11px; color: #94a3b8; text-align: center; }
                @media print { .no-print { display: none; } }
            </style>
        </head>
        <body>
            <div class="no-print" style="margin-bottom: 20px; text-align: right;">
                <button onclick="window.print()" style="padding: 10px 20px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">🖨️ Print / Save as PDF</button>
            </div>

            <div class="header">
                <div>
                    <div class="title">Direct Benefit Transfer Portal</div>
                    <div class="subtitle">Official Welfare Scheme Application Acknowledgement Receipt</div>
                </div>
                <div class="badge">Status: ${app.status}</div>
            </div>

            <div class="section">
                <div class="grid">
                    <div>
                        <div class="label">Application Reference ID</div>
                        <div class="val">${app.id}</div>
                    </div>
                    <div>
                        <div class="label">Submission Date</div>
                        <div class="val">${app.applied_date || 'Recent'}</div>
                    </div>
                    <div>
                        <div class="label">Scheme Name</div>
                        <div class="val">${app.scheme_name}</div>
                    </div>
                    <div>
                        <div class="label">Applicant Name</div>
                        <div class="val">${app.user_name || u.name || 'Citizen'}</div>
                    </div>
                    <div>
                        <div class="label">Applicant Email</div>
                        <div class="val">${app.user_email || u.email || 'N/A'}</div>
                    </div>
                    <div>
                        <div class="label">Verification Authority</div>
                        <div class="val">District Welfare Officer</div>
                    </div>
                </div>
            </div>

            ${app.remarks ? `
                <div class="section" style="background: #fffbeb; border-color: #fef3c7;">
                    <div class="label" style="color: #92400e;">Official Officer Remarks</div>
                    <div class="val" style="color: #78350f; font-weight: normal; margin-top: 5px;">${app.remarks}</div>
                </div>
            ` : ''}

            <div class="footer">
                <p>This is a computer-generated official receipt for Government Welfare Scheme Application ID ${app.id}.</p>
                <p>© 2026 AI Government Welfare Eligibility Portal. All rights reserved.</p>
            </div>
        </body>
        </html>
    `);
    printWindow.document.close();
}

// CITIZEN PROFILE VIEW & CHANGE PASSWORD
async function loadProfileView() {
    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }

    const p = state.currentProfile || {};
    const u = state.currentUser;

    setElementText("profDisplayName", p.name || u.name || "Citizen");
    setElementText("profDisplayEmail", u.email || "");
    setElementText("profDisplayRole", `${u.role || 'citizen'} account`);
    setElementText("profileInitials", (p.name || u.name || "C").charAt(0).toUpperCase());

    setElementText("profValMobile", p.mobile_number || u.mobile_number || "Not provided");
    setElementText("profValAgeGender", `${p.age || 25} Yrs, ${p.gender || 'Male'}`);
    setElementText("profValMarital", p.marital_status || "Single");
    setElementText("profValLocation", `${p.district || 'Varanasi'}, ${p.state || 'Uttar Pradesh'} (${p.rural_urban || 'Rural'})`);
    setElementText("profValOccIncome", `${p.occupation || 'Farmer'} (₹${(p.annual_income || 150000).toLocaleString()}/yr)`);
    setElementText("profValCategory", p.caste_category || "General");

    const badgeContainer = document.getElementById("profStatusBadges");
    if (badgeContainer) {
        badgeContainer.innerHTML = "";
        const flags = [
            { name: "Farmer Status", val: p.farmer_status },
            { name: "Student Status", val: p.student_status },
            { name: "Disability (40%+)", val: p.disability_status },
            { name: "Senior Citizen", val: p.senior_citizen_status || (p.age >= 60) },
            { name: "Widow Status", val: p.widow_status },
            { name: "BPL Ration Card", val: p.bpl_status },
            { name: "Aadhaar Card", val: p.aadhaar_available !== false },
            { name: "Bank Account", val: p.bank_account_available !== false }
        ];

        flags.forEach(f => {
            const pill = document.createElement("span");
            pill.className = `px-3 py-1 rounded-full text-xs font-bold border ${f.val ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-slate-100 text-slate-400 border-slate-200'}`;
            pill.textContent = `${f.val ? '✓' : '✗'} ${f.name}`;
            badgeContainer.appendChild(pill);
        });
    }
}

async function handleChangePasswordSubmit(e) {
    e.preventDefault();
    const oldPass = document.getElementById("changeOldPass").value;
    const newPass = document.getElementById("changeNewPass").value;
    const confirmPass = document.getElementById("changeConfirmPass").value;

    if (newPass !== confirmPass) {
        showNotification("Error", "New password and confirm password do not match.", "error");
        return;
    }

    if (newPass.length < 6) {
        showNotification("Error", "New password must be at least 6 characters long.", "error");
        return;
    }

    try {
        await ApiService.changePassword(oldPass, newPass);
        document.getElementById("changeOldPass").value = "";
        document.getElementById("changeNewPass").value = "";
        document.getElementById("changeConfirmPass").value = "";
        showNotification("Success", "Password updated successfully!", "success");
    } catch (err) {
        showNotification("Password Change Error", err.message || "Failed to update password.", "error");
    }
}

// CHATBOT DRAWER
function toggleChatDrawer() {
    const drawer = document.getElementById("chatDrawer");
    if (drawer) {
        drawer.classList.toggle("hidden");
    }
}

async function sendChatMessage(e) {
    if (e) e.preventDefault();
    const chatInput = document.getElementById("chatInput");
    const container = document.getElementById("chatMessagesContainer");
    if (!chatInput || !container) return;

    const message = chatInput.value.trim();
    if (!message) return;

    appendChatMessage(message, "user");
    chatInput.value = "";

    try {
        const res = await ApiService.sendChatMessage(message, currentLanguage, state.currentProfile);
        appendChatMessage(res.response, "bot");
    } catch (err) {
        appendChatMessage("Sorry, I encountered an error processing your query. Please try again.", "bot");
    }
}

function appendChatMessage(text, sender) {
    const container = document.getElementById("chatMessagesContainer");
    if (!container) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = `flex ${sender === "user" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className = `max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed shadow-sm ${sender === "user" ? "chat-message-user" : "chat-message-bot"}`;
    bubble.innerHTML = text.replace(/\n/g, "<br>");

    msgDiv.appendChild(bubble);
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

// ADMIN PORTAL SYSTEM (10 WELL-DESIGNED ADMIN SCREENS)
let adminCharts = {
    monthlyChart: null,
    statusChart: null,
    topSchemesChart: null
};

let currentAdminDocTarget = { userId: null, documentName: null };

async function loadAdminView() {
    if (!state.currentUser || state.currentUser.role !== "admin") {
        switchView("auth-landing");
        return;
    }

    const adminView = document.getElementById("view-admin");
    if (adminView) adminView.classList.remove("hidden");

    switchAdminSubTab("dashboard");
}

function switchAdminSubTab(subTabName) {
    // Hide all admin screens
    document.querySelectorAll(".admin-panel-screen").forEach(s => s.classList.add("hidden"));
    
    // Deactivate all sidebar nav buttons
    document.querySelectorAll(".admin-sidebar-btn").forEach(btn => {
        btn.className = "admin-sidebar-btn w-full px-3 py-2.5 rounded-xl flex items-center gap-2.5 text-slate-400 hover:text-white hover:bg-slate-800/80 transition";
    });

    // Show target screen
    const targetPanel = document.getElementById(`adminPanel-${subTabName}`);
    if (targetPanel) {
        targetPanel.classList.remove("hidden");
    }

    // Activate sidebar button
    const activeNavBtn = document.getElementById(`adminNav-${subTabName}`);
    if (activeNavBtn) {
        activeNavBtn.className = "admin-sidebar-btn w-full px-3 py-2.5 rounded-xl flex items-center gap-2.5 text-white bg-indigo-600/90 font-bold transition shadow-md";
    }

    if (subTabName === "dashboard") {
        refreshAdminDashboard();
    } else if (subTabName === "schemes") {
        loadAdminSchemes();
    } else if (subTabName === "rules") {
        loadAdminRulesScreen();
    } else if (subTabName === "users") {
        loadAdminUsers();
    } else if (subTabName === "applications") {
        loadAdminApplications();
    } else if (subTabName === "documents") {
        loadAdminDocVerificationQueue();
    } else if (subTabName === "reports") {
        loadAdminReports();
    } else if (subTabName === "profile") {
        loadAdminProfile();
    }

    initLucide();
}

// SCREEN 1: ADMIN LOGIN
async function handleAdminLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById("adminLoginEmail").value.trim();
    const pass = document.getElementById("adminLoginPass").value;

    try {
        const user = await ApiService.login(email, pass);
        if (user.role !== "admin") {
            showNotification("Access Denied", "This account does not have admin permissions.", "error");
            logout();
            return;
        }
        await finalizeAuthFlow(user, "admin");
    } catch (err) {
        showNotification("Login Failed", err.message || "Invalid credentials", "error");
    }
}

// SCREEN 2: DASHBOARD & CHARTS
async function refreshAdminDashboard() {
    try {
        const analytics = await ApiService.getAdminAnalytics();

        // Stat cards
        setElementText("dashTotalUsers", analytics.total_users || 0);
        setElementText("dashTotalSchemes", analytics.total_schemes || 0);
        setElementText("dashTotalApps", analytics.total_applications || 0);
        setElementText("dashPendingApps", analytics.pending_applications || 0);
        setElementText("dashApprovedApps", analytics.approved_applications || 0);
        setElementText("dashRejectedApps", analytics.rejected_applications || 0);

        // Render Chart 1: Monthly Apps Trend
        renderMonthlyAppsChart(analytics.monthly_applications || {});

        // Render Chart 2: Status Breakdown Doughnut
        renderStatusBreakdownChart(analytics.application_status_distribution || {});

        // Render Chart 3: Top Applied Schemes
        renderTopSchemesChart(analytics.top_applied_schemes || {});

        renderRecentAppsFeed(analytics.recent_applications || []);
        renderRecentUsersFeed(analytics.recent_users || []);
    } catch (e) {
        console.error("Dashboard refresh error:", e);
    }
}

function renderMonthlyAppsChart(monthlyData) {
    const ctx = document.getElementById("chartMonthlyApps");
    if (!ctx) return;

    if (adminCharts.monthlyChart) {
        adminCharts.monthlyChart.destroy();
    }

    const labels = Object.keys(monthlyData);
    const values = Object.values(monthlyData);

    adminCharts.monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                label: 'Submitted Applications',
                data: values.length ? values : [12, 19, 25, 22, 30, 38, 45],
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                borderColor: '#6366f1',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
            }
        }
    });
}

function renderStatusBreakdownChart(statusData) {
    const ctx = document.getElementById("chartStatusBreakdown");
    if (!ctx) return;

    if (adminCharts.statusChart) {
        adminCharts.statusChart.destroy();
    }

    adminCharts.statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Applied', 'Under Verification', 'Approved', 'Rejected'],
            datasets: [{
                data: [
                    statusData['Applied'] || 1,
                    statusData['Under Verification'] || 1,
                    statusData['Approved'] || 2,
                    statusData['Rejected'] || 0
                ],
                backgroundColor: ['#60a5fa', '#f59e0b', '#10b981', '#f43f5e']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 10 } } }
            }
        }
    });
}

function renderTopSchemesChart(topData) {
    const ctx = document.getElementById("chartTopSchemes");
    if (!ctx) return;

    if (adminCharts.topSchemesChart) {
        adminCharts.topSchemesChart.destroy();
    }

    const labels = Object.keys(topData).map(k => k.length > 25 ? k.substring(0, 22) + '...' : k);
    const values = Object.values(topData);

    adminCharts.topSchemesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['PM-Kisan', 'Ayushman Bharat', 'PMAY Housing', 'Post-Matric Scholarship', 'IGNOAPS Pension'],
            datasets: [{
                label: 'Applications',
                data: values.length ? values : [45, 32, 28, 20, 15],
                backgroundColor: 'rgba(168, 85, 247, 0.7)',
                borderColor: '#a855f7',
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } }
            }
        }
    });
}

function renderRecentAppsFeed(recentApps) {
    const container = document.getElementById("dashRecentAppsContainer");
    if (!container) return;
    container.innerHTML = "";

    if (!recentApps || recentApps.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-xs">No recent application activity.</p>`;
        return;
    }

    recentApps.forEach(a => {
        const div = document.createElement("div");
        div.className = "flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 border border-slate-800";
        div.innerHTML = `
            <div>
                <div class="font-bold text-white">${a.scheme_name}</div>
                <div class="text-[10px] text-slate-400">Applicant: ${a.user_name || a.user_id} (${a.applied_date})</div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${a.status === 'Approved' ? 'bg-emerald-500/20 text-emerald-400' : (a.status === 'Rejected' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400')}">${a.status}</span>
        `;
        container.appendChild(div);
    });
}

function renderRecentUsersFeed(recentUsers) {
    const container = document.getElementById("dashRecentUsersContainer");
    if (!container) return;
    container.innerHTML = "";

    if (!recentUsers || recentUsers.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-xs">No recent registrations.</p>`;
        return;
    }

    recentUsers.forEach(u => {
        const div = document.createElement("div");
        div.className = "flex items-center justify-between p-2.5 rounded-xl bg-slate-900/80 border border-slate-800";
        div.innerHTML = `
            <div>
                <div class="font-bold text-white">${u.name || u.email}</div>
                <div class="text-[10px] text-slate-400">${u.email}</div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${u.role === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-700 text-slate-300'}">${u.role || 'citizen'}</span>
        `;
        container.appendChild(div);
    });
}

// SCREEN 3: SCHEME MANAGEMENT
async function loadAdminSchemes() {
    try {
        state.schemes = await ApiService.getSchemes();
        renderAdminSchemesTable(state.schemes);
    } catch (e) {
        console.error("Error loading schemes:", e);
    }
}

function renderAdminSchemesTable(schemes) {
    const tbody = document.getElementById("adminSchemesTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    schemes.forEach(s => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800 hover:bg-slate-800/40 transition text-xs";
        tr.innerHTML = `
            <td class="p-3 font-bold text-white max-w-xs leading-snug">
                ${s.name}
                <div class="text-[10px] text-slate-400 font-normal">ID: ${s.id}</div>
            </td>
            <td class="p-3"><span class="px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">${s.category}</span></td>
            <td class="p-3 text-emerald-400 font-semibold max-w-xs truncate">${s.benefits}</td>
            <td class="p-3 text-slate-300">${s.last_date || 'Open'}</td>
            <td class="p-3">
                <div class="flex items-center gap-2">
                    <button onclick="openEditSchemeModal('${s.id}')" title="Edit Scheme" class="px-2.5 py-1 rounded-lg bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-600/50 transition cursor-pointer">Edit</button>
                    <button onclick="adminDeleteScheme('${s.id}')" title="Delete Scheme" class="p-1.5 rounded-lg bg-rose-950/60 text-rose-400 hover:bg-rose-900 border border-rose-800/50 transition cursor-pointer"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
    initLucide();
}

function filterSchemeTable() {
    const query = (document.getElementById("schemeSearchInput")?.value || "").toLowerCase();
    const cat = document.getElementById("schemeCategoryFilter")?.value || "All";

    const filtered = state.schemes.filter(s => {
        const matchQ = s.name.toLowerCase().includes(query) || (s.description || "").toLowerCase().includes(query);
        const matchC = (cat === "All") || s.category === cat;
        return matchQ && matchC;
    });
    renderAdminSchemesTable(filtered);
}

function openAddSchemeModal() {
    document.getElementById("addSchemeModalTitle").textContent = "Add New Welfare Scheme";
    document.getElementById("editSchemeId").value = "";
    document.getElementById("addSchemeForm").reset();
    document.getElementById("addSchemeModal")?.classList.remove("hidden");
}

function openEditSchemeModal(schemeId) {
    const s = state.schemes.find(x => x.id === schemeId);
    if (!s) return;

    document.getElementById("addSchemeModalTitle").textContent = "Edit Welfare Scheme";
    document.getElementById("editSchemeId").value = s.id;
    document.getElementById("schemeFormName").value = s.name;
    document.getElementById("schemeFormCategory").value = s.category;
    document.getElementById("schemeFormLastDate").value = s.last_date || "Open";
    document.getElementById("schemeFormDescription").value = s.description;
    document.getElementById("schemeFormBenefits").value = s.benefits;
    document.getElementById("schemeFormLink").value = s.official_link || "";

    document.getElementById("addSchemeModal")?.classList.remove("hidden");
}

function closeAddSchemeModal() {
    document.getElementById("addSchemeModal")?.classList.add("hidden");
}

async function handleSaveScheme(e) {
    e.preventDefault();
    const id = document.getElementById("editSchemeId").value;
    const schemeData = {
        name: document.getElementById("schemeFormName").value,
        category: document.getElementById("schemeFormCategory").value,
        description: document.getElementById("schemeFormDescription").value,
        benefits: document.getElementById("schemeFormBenefits").value,
        last_date: document.getElementById("schemeFormLastDate").value,
        official_link: document.getElementById("schemeFormLink").value || "https://gov.in",
        criteria: id ? (state.schemes.find(x => x.id === id)?.criteria || {}) : {},
        required_documents: id ? (state.schemes.find(x => x.id === id)?.required_documents || ["Aadhaar Card"]) : ["Aadhaar Card"]
    };

    try {
        if (id) {
            await ApiService.updateScheme(id, schemeData);
            showNotification("Success", "Scheme updated successfully", "success");
        } else {
            await ApiService.createScheme(schemeData);
            showNotification("Success", "New scheme published successfully", "success");
        }
        closeAddSchemeModal();
        await loadAdminSchemes();
    } catch (err) {
        showNotification("Error", err.message, "error");
    }
}

// SCREEN 4: ELIGIBILITY RULE MANAGEMENT (HEART OF PROJECT)
async function loadAdminRulesScreen() {
    if (!state.schemes || state.schemes.length === 0) {
        state.schemes = await ApiService.getSchemes();
    }
    const select = document.getElementById("ruleSchemeSelect");
    if (!select) return;

    select.innerHTML = "";
    state.schemes.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.textContent = `${s.name} (${s.category})`;
        select.appendChild(opt);
    });

    loadSchemeRulesForEdit();
}

function loadSchemeRulesForEdit() {
    const schemeId = document.getElementById("ruleSchemeSelect")?.value;
    const s = state.schemes.find(x => x.id === schemeId);
    if (!s) return;

    const c = s.criteria || {};

    document.getElementById("ruleMinAge").value = c.min_age !== undefined ? c.min_age : "";
    document.getElementById("ruleMaxAge").value = c.max_age !== undefined ? c.max_age : "";
    document.getElementById("ruleMaxIncome").value = c.max_income !== undefined ? c.max_income : "";
    document.getElementById("ruleGender").value = c.gender || "";
    document.getElementById("ruleState").value = s.state_restriction || "All";

    document.getElementById("ruleStudent").checked = !!c.student_status;
    document.getElementById("ruleFarmer").checked = !!c.farmer_status;
    document.getElementById("ruleBPL").checked = !!c.bpl_status;
    document.getElementById("ruleDisability").checked = !!c.disability_status;
    document.getElementById("ruleSenior").checked = !!c.senior_citizen_status;
    document.getElementById("ruleWidow").checked = !!c.widow_status;

    document.getElementById("ruleRequiredDocs").value = (s.required_documents || []).join(", ");

    updateRuleSummaryCard(s, c);
}

function updateRuleSummaryCard(scheme, c) {
    const card = document.getElementById("ruleSummaryCard");
    if (!card) return;

    const minAge = document.getElementById("ruleMinAge").value || c.min_age;
    const maxAge = document.getElementById("ruleMaxAge").value || c.max_age;
    const maxInc = document.getElementById("ruleMaxIncome").value || c.max_income;
    const docs = document.getElementById("ruleRequiredDocs").value || (scheme.required_documents || []).join(", ");

    card.innerHTML = `
        <div class="font-bold text-white text-sm border-b border-slate-800 pb-1 mb-2">📋 ${scheme.name}</div>
        <div><strong>Min Age:</strong> ${minAge !== undefined && minAge !== "" ? minAge + ' Years' : 'None'}</div>
        <div><strong>Max Age:</strong> ${maxAge !== undefined && maxAge !== "" ? maxAge + ' Years' : 'None'}</div>
        <div><strong>Income Limit:</strong> ${maxInc ? '₹' + Number(maxInc).toLocaleString() : 'No Limit'}</div>
        <div><strong>Student Required:</strong> ${document.getElementById("ruleStudent").checked ? '✓ Yes' : 'No'}</div>
        <div><strong>State Scope:</strong> ${document.getElementById("ruleState").value || 'All'}</div>
        <div class="pt-2 border-t border-slate-800 text-amber-300">
            <strong>Required Documents:</strong><br>
            ${docs.split(',').map(d => '✓ ' + d.trim()).join('<br>')}
        </div>
    `;
}

async function saveSchemeRules() {
    const schemeId = document.getElementById("ruleSchemeSelect")?.value;
    const s = state.schemes.find(x => x.id === schemeId);
    if (!s) return;

    const minAge = document.getElementById("ruleMinAge").value;
    const maxAge = document.getElementById("ruleMaxAge").value;
    const maxIncome = document.getElementById("ruleMaxIncome").value;
    const gender = document.getElementById("ruleGender").value;
    const reqDocs = document.getElementById("ruleRequiredDocs").value.split(',').map(x => x.trim()).filter(Boolean);

    const updatedCriteria = {
        min_age: minAge ? parseInt(minAge) : null,
        max_age: maxAge ? parseInt(maxAge) : null,
        max_income: maxIncome ? parseFloat(maxIncome) : null,
        gender: gender || null,
        student_status: document.getElementById("ruleStudent").checked,
        farmer_status: document.getElementById("ruleFarmer").checked,
        bpl_status: document.getElementById("ruleBPL").checked,
        disability_status: document.getElementById("ruleDisability").checked,
        senior_citizen_status: document.getElementById("ruleSenior").checked,
        widow_status: document.getElementById("ruleWidow").checked
    };

    // Remove None / undefined keys
    Object.keys(updatedCriteria).forEach(key => {
        if (updatedCriteria[key] === null || updatedCriteria[key] === undefined) {
            delete updatedCriteria[key];
        }
    });

    try {
        await ApiService.updateSchemeRules(schemeId, updatedCriteria, reqDocs);
        showNotification("Success", `AI Eligibility Rules updated for ${s.name}`, "success");
        await loadAdminSchemes();
        loadSchemeRulesForEdit();
    } catch (err) {
        showNotification("Error", err.message, "error");
    }
}

// SCREEN 5: USER MANAGEMENT
let adminUsersList = [];

async function loadAdminUsers() {
    try {
        adminUsersList = await ApiService.getAdminUsers();
        renderAdminUsersTable(adminUsersList);
    } catch (e) {
        console.error("Error loading admin users:", e);
    }
}

function renderAdminUsersTable(users) {
    const tbody = document.getElementById("adminUsersTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    users.forEach(u => {
        const isBlocked = !!u.is_blocked;
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800 hover:bg-slate-800/40 transition text-xs";
        tr.innerHTML = `
            <td class="p-3 font-bold text-white flex items-center gap-2">
                <div class="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">
                    ${(u.name || 'C').charAt(0).toUpperCase()}
                </div>
                ${u.name || 'Citizen'}
            </td>
            <td class="p-3 text-slate-300">${u.email}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${u.role === 'admin' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-slate-800 text-slate-300'}">${u.role}</span></td>
            <td class="p-3 font-bold text-indigo-400">${u.applications_count || 0} Submitted</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${isBlocked ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}">${isBlocked ? 'Blocked' : 'Active'}</span></td>
            <td class="p-3">
                <div class="flex items-center gap-2">
                    <button onclick="inspectUserProfile('${u.id}')" title="Inspect Profile" class="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition cursor-pointer">View Profile</button>
                    <button onclick="toggleUserBlockStatus('${u.id}', ${!isBlocked})" class="px-2.5 py-1 rounded-lg ${isBlocked ? 'bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/50' : 'bg-amber-600/30 text-amber-400 border border-amber-500/30 hover:bg-amber-600/50'} transition cursor-pointer">
                        ${isBlocked ? 'Unblock' : 'Block'}
                    </button>
                    ${u.role !== 'admin' ? `<button onclick="confirmDeleteUser('${u.id}')" title="Delete User" class="px-2.5 py-1 rounded-lg bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600 hover:text-white transition cursor-pointer">Delete</button>` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterUserTable() {
    const q = (document.getElementById("userSearchInput")?.value || "").toLowerCase();
    const filtered = adminUsersList.filter(u => 
        (u.name || "").toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    );
    renderAdminUsersTable(filtered);
}

async function toggleUserBlockStatus(userId, isBlocked) {
    try {
        await ApiService.updateUserStatus(userId, isBlocked);
        showNotification("Success", `User status updated to ${isBlocked ? 'Blocked' : 'Active'}`, "success");
        await loadAdminUsers();
    } catch (e) {
        showNotification("Error", e.message, "error");
    }
}

async function confirmDeleteUser(userId) {
    if (!confirm("Are you sure you want to delete this user and all associated records from the database?")) return;
    try {
        await ApiService.deleteUser(userId);
        showNotification("Success", "User deleted successfully from database", "success");
        await loadAdminUsers();
    } catch (e) {
        showNotification("Error", e.message, "error");
    }
}

function inspectUserProfile(userId) {
    const u = adminUsersList.find(x => x.id === userId);
    if (!u) return;

    const modalBody = document.getElementById("userProfileModalBody");
    const modal = document.getElementById("userProfileModal");
    if (!modalBody || !modal) return;

    const p = u.profile || {};
    modalBody.innerHTML = `
        <div class="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
            <p><strong>Name:</strong> ${u.name || p.name || 'N/A'}</p>
            <p><strong>Email:</strong> ${u.email}</p>
            <p><strong>Age / Gender:</strong> ${p.age || 25} Yrs, ${p.gender || 'Male'}</p>
            <p><strong>State / District:</strong> ${p.district || 'Varanasi'}, ${p.state || 'Uttar Pradesh'}</p>
            <p><strong>Occupation:</strong> ${p.occupation || 'Farmer'}</p>
            <p><strong>Annual Income:</strong> ₹${(p.annual_income || 150000).toLocaleString()}</p>
            <p><strong>Category:</strong> ${p.caste_category || 'General'}</p>
        </div>
        <div class="text-[11px] text-slate-400">
            <strong>Eligibility Status Flags:</strong><br>
            Farmer: ${p.farmer_status ? '✓' : '✗'} | Student: ${p.student_status ? '✓' : '✗'} | BPL: ${p.bpl_status ? '✓' : '✗'} | Disability: ${p.disability_status ? '✓' : '✗'}
        </div>
    `;
    modal.classList.remove("hidden");
}

function closeUserProfileModal() {
    document.getElementById("userProfileModal")?.classList.add("hidden");
}

// SCREEN 6: APPLICATION MANAGEMENT
let adminAppsList = [];

async function loadAdminApplications() {
    try {
        adminAppsList = await ApiService.getApplications();
        renderAdminApplicationsTable(adminAppsList);
    } catch (e) {
        console.error("Error loading admin apps:", e);
    }
}

function renderAdminApplicationsTable(apps) {
    const tbody = document.getElementById("adminApplicationsTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!apps || apps.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-slate-500 text-xs">No applications available.</td></tr>`;
        return;
    }

    apps.forEach(a => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800 hover:bg-slate-800/40 transition text-xs";
        tr.innerHTML = `
            <td class="p-3 font-bold text-cyan-400">${a.id}</td>
            <td class="p-3 font-semibold text-white">${a.user_name || a.user_id}<br><span class="text-[10px] text-slate-400">${a.user_email || ''}</span></td>
            <td class="p-3 font-semibold text-slate-200 max-w-xs leading-snug">${a.scheme_name}</td>
            <td class="p-3 text-slate-400">${a.applied_date}</td>
            <td class="p-3">
                <span class="px-2.5 py-1 rounded text-[10px] font-bold ${a.status === 'Approved' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : (a.status === 'Rejected' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30')}">${a.status}</span>
            </td>
            <td class="p-3">
                <select onchange="adminUpdateAppStatus('${a.id}', this.value)" class="p-1.5 rounded-lg border border-slate-700 text-xs font-semibold bg-slate-950 text-indigo-300 focus:outline-none cursor-pointer">
                    <option value="Applied" ${a.status === 'Applied' ? 'selected' : ''}>Applied</option>
                    <option value="Under Verification" ${a.status === 'Under Verification' ? 'selected' : ''}>Under Verification</option>
                    <option value="Approved" ${a.status === 'Approved' ? 'selected' : ''}>Approve</option>
                    <option value="Rejected" ${a.status === 'Rejected' ? 'selected' : ''}>Reject</option>
                </select>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterAppTable() {
    const st = document.getElementById("appStatusFilter")?.value || "All";
    const filtered = (st === "All") ? adminAppsList : adminAppsList.filter(a => a.status === st);
    renderAdminApplicationsTable(filtered);
}

// SCREEN 7: DOCUMENT VERIFICATION (ORGANIZED USER FOLDERS)
let adminUserDocFoldersList = [];

async function loadAdminDocVerificationQueue() {
    const container = document.getElementById("adminDocVerificationQueue");
    if (!container) return;

    try {
        const users = await ApiService.getAdminUsers() || [];
        const apps = await ApiService.getApplications() || [];

        // Build User Folder objects
        adminUserDocFoldersList = users.map(u => {
            const docsMap = {};

            // 1. Add from user_documents
            if (u.user_documents) {
                Object.keys(u.user_documents).forEach(dName => {
                    docsMap[dName] = u.user_documents[dName];
                });
            }

            // 2. Add from applications uploaded_documents
            apps.filter(a => a.user_id === u.id || a.user_email === u.email).forEach(a => {
                const appDocs = a.uploaded_documents || {};
                Object.keys(appDocs).forEach(dName => {
                    if (!docsMap[dName]) {
                        const url = appDocs[dName];
                        docsMap[dName] = {
                            document_name: dName,
                            file_name: `${dName.replace(/\s+/g, '_')}.jpg`,
                            file_url: url,
                            status: a.status === 'Approved' ? 'Verified' : (a.status === 'Rejected' ? 'Rejected' : 'Under Verification'),
                            upload_date: a.applied_date || 'Recent'
                        };
                    }
                });
            });

            return {
                user: u,
                documents: docsMap
            };
        });

        renderAdminUserDocFolders(adminUserDocFoldersList);
    } catch (e) {
        console.error("Doc verification load error:", e);
    }
}

function filterAdminUserDocFolders() {
    const search = (document.getElementById("adminDocUserSearch")?.value || "").toLowerCase().trim();
    if (!search) {
        renderAdminUserDocFolders(adminUserDocFoldersList);
        return;
    }

    const filtered = adminUserDocFoldersList.filter(item => {
        const name = (item.user.name || "").toLowerCase();
        const email = (item.user.email || "").toLowerCase();
        const id = (item.user.id || "").toLowerCase();
        return name.includes(search) || email.includes(search) || id.includes(search);
    });

    renderAdminUserDocFolders(filtered);
}

function renderAdminUserDocFolders(folders) {
    const container = document.getElementById("adminDocVerificationQueue");
    if (!container) return;

    container.innerHTML = "";

    if (!folders || folders.length === 0) {
        container.innerHTML = `<div class="text-center text-slate-500 py-12 bg-slate-900 rounded-2xl border border-slate-800"><p class="text-sm">No citizen document folders found.</p></div>`;
        return;
    }

    folders.forEach(item => {
        const u = item.user;
        const p = u.profile || {};
        const docs = item.documents;
        const docKeys = Object.keys(docs);

        const card = document.createElement("div");
        card.className = "bg-slate-900 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-4";

        const docBadges = docKeys.length > 0
            ? `<span class="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold flex items-center gap-1"><i data-lucide="folder-check" class="w-3.5 h-3.5"></i> ${docKeys.length} JPEG Document(s)</span>`
            : `<span class="px-3 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 text-xs font-semibold">No Documents Uploaded</span>`;

        card.innerHTML = `
            <!-- USER FOLDER HEADER -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div class="flex items-center gap-3.5">
                    <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white font-extrabold text-xl flex items-center justify-center shadow-md">
                        📁
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h3 class="text-base font-extrabold text-white">User Folder: ${u.name || 'Citizen'}</h3>
                            <span class="text-[10px] text-purple-300 font-mono bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/40">(${u.id})</span>
                        </div>
                        <p class="text-xs text-slate-400 mt-0.5">${u.email} | ${p.district || 'Varanasi'}, ${p.state || 'Uttar Pradesh'} (${p.occupation || 'Citizen'})</p>
                    </div>
                </div>
                ${docBadges}
            </div>

            <!-- DOCUMENTS GRID INSIDE USER FOLDER -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                ${docKeys.length > 0 ? docKeys.map(docName => {
                    const docMeta = docs[docName];
                    const fileUrl = docMeta.file_url || "./static/uploads/sample.jpg";

                    let statusBadgeClass = "bg-amber-500/20 text-amber-400 border-amber-500/30";
                    if (docMeta.status === "Verified" || docMeta.status === "Approved") statusBadgeClass = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
                    else if (docMeta.status === "Rejected") statusBadgeClass = "bg-rose-500/20 text-rose-400 border-rose-500/30";

                    return `
                        <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 text-xs flex flex-col justify-between">
                            <div>
                                <div class="flex items-center justify-between mb-2">
                                    <span class="font-bold text-white flex items-center gap-1.5"><i data-lucide="file-check" class="w-4 h-4 text-indigo-400"></i> ${docName}</span>
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadgeClass}">${docMeta.status || 'Uploaded'}</span>
                                </div>
                                <p class="text-[11px] text-slate-400 mb-2">Format: <strong>JPEG (.jpg)</strong> | Date: ${docMeta.upload_date || 'Recent'}</p>
                                
                                ${docMeta.remarks ? `<p class="text-[11px] text-amber-300 bg-amber-950/40 p-2 rounded-lg border border-amber-800/40 mb-2"><strong>Remarks:</strong> ${docMeta.remarks}</p>` : ''}
                            </div>

                            <div class="space-y-2 pt-2 border-t border-slate-800">
                                <button onclick="openDocPreviewModal('${u.id}', '${docName}', '${fileUrl}')" class="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition flex items-center justify-center gap-1.5 cursor-pointer">
                                    <i data-lucide="eye" class="w-3.5 h-3.5"></i> Inspect / Verify Document
                                </button>
                            </div>
                        </div>
                    `;
                }).join('') : `
                    <div class="col-span-3 py-6 text-center text-slate-500 text-xs italic">
                        No uploaded JPEG documents in this user folder yet.
                    </div>
                `}
            </div>
        `;
        container.appendChild(card);
    });

    initLucide();
}

function openDocPreviewModal(userId, docName, fileUrl) {
    currentAdminDocTarget = { userId, documentName: docName };
    document.getElementById("docPreviewTitle").textContent = `${docName} - Inspection Desk`;
    document.getElementById("docPreviewImage").src = fileUrl;
    document.getElementById("docPreviewRemarks").value = "";
    document.getElementById("docPreviewModal")?.classList.remove("hidden");
}

function closeDocPreviewModal() {
    document.getElementById("docPreviewModal")?.classList.add("hidden");
}

async function actionVerifyDocument(status) {
    if (!currentAdminDocTarget.userId || !currentAdminDocTarget.documentName) return;

    const remarks = document.getElementById("docPreviewRemarks").value || (status === 'Verified' ? 'Document verified and accepted by Admin' : 'Document rejected by Admin');

    try {
        await ApiService.verifyDocument(currentAdminDocTarget.userId, currentAdminDocTarget.documentName, status, remarks);
        showNotification("Success", `Document status set to ${status}`, "success");
        closeDocPreviewModal();
        await loadAdminDocVerificationQueue();
    } catch (err) {
        showNotification("Error", err.message, "error");
    }
}

// SCREEN 8: REPORTS & ANALYTICS
async function loadAdminReports() {
    try {
        const analytics = await ApiService.getAdminAnalytics();
        setElementText("reportApprovalRate", `${analytics.approval_rate || 0}%`);
        setElementText("reportTotalApps", analytics.total_applications || 0);
        setElementText("reportCategoryCount", Object.keys(analytics.scheme_category_distribution || {}).length || 0);
    } catch (e) {
        console.error("Reports load error:", e);
    }
}

function downloadCSVReport() {
    window.open(ApiService.getExportReportsUrl(), "_blank");
    showNotification("Downloading", "Generating application report CSV download...", "info");
}

// SCREEN 10: ADMIN PROFILE & SUPABASE MONITOR
async function loadAdminProfile() {
    if (state.currentUser) {
        setElementText("adminProfileName", state.currentUser.name || "System Administrator");
        setElementText("adminProfileEmail", state.currentUser.email || "admin@welfare.gov");
    }
    await checkSupabaseConnection();
}

async function checkSupabaseConnection() {
    const details = document.getElementById("supabaseMonitorDetails");
    const badge = document.getElementById("supabaseMonitorBadge");
    const sidebarBadge = document.getElementById("supabaseStatusText");
    if (!details) return;

    try {
        const res = await ApiService.getSupabaseStatus();
        if (res.connected) {
            badge.className = "px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold text-[10px] uppercase";
            badge.textContent = "Online";
            if (sidebarBadge) sidebarBadge.textContent = "Online";

            details.innerHTML = `
                <div><strong>Supabase Connection:</strong> Active</div>
                <div><strong>Project URL:</strong> ${res.url || 'Connected'}</div>
                <div class="pt-2 text-indigo-400">
                    <strong>Connected Database Table Rows:</strong><br>
                    • Users Table: ${res.tables?.users || 0} records<br>
                    • Schemes Table: ${res.tables?.schemes || 0} records<br>
                    • Applications Table: ${res.tables?.applications || 0} records<br>
                    • Notifications Table: ${res.tables?.notifications || 0} records
                </div>
            `;
        } else {
            badge.className = "px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold text-[10px] uppercase";
            badge.textContent = "Local Mode";
            if (sidebarBadge) sidebarBadge.textContent = "Local DB";

            details.innerHTML = `
                <div><strong>Supabase Mode:</strong> Local JSON Fallback Active</div>
                <div class="text-amber-400 mt-1">Status: ${res.reason || 'Ready for Supabase URL & ANON KEY'}</div>
                <div class="pt-2 text-slate-400">
                    <strong>Local Data Store Metrics:</strong><br>
                    • Users: ${res.tables?.users || 0} | Schemes: ${res.tables?.schemes || 0} | Apps: ${res.tables?.applications || 0}
                </div>
            `;
        }
    } catch (e) {
        details.innerHTML = `<div class="text-rose-400">Error connecting: ${e.message}</div>`;
    }
}

