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
            switchView("recommendations");
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
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("hidden"));
    const target = document.getElementById(`view-${viewId}`);
    if (target) {
        target.classList.remove("hidden");
    }

    const heroSection = document.getElementById("heroSection");
    const mainNavMenu = document.getElementById("mainNavMenu");
    const chatBtn = document.getElementById("btnToggleChat");
    const chatDrawer = document.getElementById("chatDrawer");

    if (viewId === "auth-landing" || !state.currentUser) {
        if (heroSection) heroSection.classList.add("hidden");
        if (mainNavMenu) mainNavMenu.classList.add("hidden");
        if (chatBtn) chatBtn.classList.add("hidden");
        if (chatDrawer) chatDrawer.classList.add("hidden");
    } else if (viewId === "admin") {
        if (heroSection) heroSection.classList.add("hidden");
        if (mainNavMenu) mainNavMenu.classList.add("hidden");
        if (chatBtn) chatBtn.classList.add("hidden");
        if (chatDrawer) chatDrawer.classList.add("hidden");
    } else {
        if (heroSection) heroSection.classList.remove("hidden");
        if (mainNavMenu) mainNavMenu.classList.remove("hidden");
        if (chatBtn) chatBtn.classList.remove("hidden");
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
    } else if (viewId === "admin") {
        loadAdminView();
        switchAdminTab("analytics");
    }

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
        document.getElementById("authLandingTitle").textContent = "Citizen Welfare Portal";
        document.getElementById("authLandingSubtitle").textContent = "Log in to view personalized scheme recommendations and track applications.";
        document.getElementById("btnLandingAuthSubmit").innerHTML = '<i data-lucide="log-in" class="w-4 h-4"></i> Login to Portal';
    }
    initLucide();
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
                showNotification("Error", "Please provide your Name and Mobile Number for registration.", "error");
                return;
            }
            await ApiService.register(name, email, mobile, password, "citizen");
            showNotification("Registration Successful", "Account created successfully! Please login with your email & password.", "success");
            
            // Clear password and switch back to Login view
            document.getElementById("landingAuthPassword").value = "";
            toggleLandingAuthMode("login");
            return;
        }

        // Login flow
        const authData = await ApiService.login(email, password);
        state.currentUser = authData;
        updateAuthUI();
        showNotification("Welcome", `Logged in as ${authData.name}`, "success");
        await loadUserData();

        if (state.currentUser.role === "admin") {
            switchView("admin");
        } else {
            switchView("recommendations");
            // Open Questionnaire wizard if profile is default/blank
            if (!state.currentProfile || !state.currentProfile.age) {
                openWizardModal();
            }
        }
    } catch (err) {
        showNotification("Authentication Failed", err.message || "Invalid credentials", "error");
    }
}

async function quickDemoLogin(role) {
    try {
        let authData;
        if (role === "citizen") {
            authData = await ApiService.login("citizen@welfare.gov", "password123");
        } else {
            authData = await ApiService.login("admin@welfare.gov", "admin123");
        }
        state.currentUser = authData;
        updateAuthUI();
        showNotification("Demo Account Loaded", `Logged in as ${authData.name} (${authData.role})`, "success");
        await loadUserData();

        if (state.currentUser.role === "admin") {
            switchView("admin");
        } else {
            switchView("recommendations");
        }
    } catch (e) {
        showNotification("Demo Login Error", e.message || "Demo account unavailable", "error");
    }
}

function logout() {
    ApiService.setAuthToken(null);
    localStorage.removeItem("welfare_user");
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
    const userContainer = document.getElementById("navUserContainer");
    const authBtnContainer = document.getElementById("navAuthBtnContainer");

    if (state.currentUser) {
        if (userContainer) {
            userContainer.style.display = "flex";
            document.getElementById("userNameLabel").textContent = state.currentUser.name;
            document.getElementById("userRoleBadge").textContent = state.currentUser.role;
        }
        if (authBtnContainer) authBtnContainer.style.display = "none";
        
        const welcomeHeading = document.getElementById("welcomeUserHeading");
        if (welcomeHeading) {
            welcomeHeading.textContent = `Welcome, ${state.currentUser.name}`;
        }

        const adminTab = document.getElementById("navAdminTab");
        if (adminTab) {
            adminTab.style.display = state.currentUser.role === "admin" ? "block" : "none";
        }
    } else {
        if (userContainer) userContainer.style.display = "none";
        if (authBtnContainer) authBtnContainer.style.display = "flex";
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
function openApplyModal(schemeId) {
    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }

    const rec = state.recommendations.find(r => r.scheme_id === schemeId);
    const scheme = rec ? rec.scheme_details : state.schemes.find(s => s.id === schemeId);
    if (!scheme) return;

    state.activeApplyScheme = scheme;
    state.uploadedApplyDocs = {}; // Clear uploaded state

    document.getElementById("applyModalSchemeTitle").textContent = `Apply for ${scheme.name}`;
    
    const container = document.getElementById("applyDocumentsContainer");
    container.innerHTML = "";

    const reqDocs = scheme.required_documents || ["Aadhaar Card", "Income Certificate", "Residence Certificate", "Bank Passbook"];

    reqDocs.forEach(docName => {
        state.uploadedApplyDocs[docName] = { status: "Missing", file_name: null, file_url: null };

        const row = document.createElement("div");
        row.className = "p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3";
        row.id = `docRow_${docName.replace(/\s+/g, '_')}`;

        row.innerHTML = `
            <div>
                <div class="flex items-center gap-2">
                    <i data-lucide="file-check" class="w-4 h-4 text-indigo-600"></i>
                    <h4 class="text-xs font-bold text-slate-900">${docName}</h4>
                </div>
                <div class="text-[11px] text-slate-400 mt-0.5">JPEG format (.jpg / .jpeg) required</div>
            </div>

            <div class="flex items-center gap-2">
                <span id="docBadge_${docName.replace(/\s+/g, '_')}" class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200">
                    Missing
                </span>
                <label class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs cursor-pointer transition shadow-sm flex items-center gap-1">
                    <i data-lucide="upload-cloud" class="w-3.5 h-3.5"></i> Upload JPEG
                    <input type="file" accept=".jpg,.jpeg,image/jpeg" onchange="handleJPEGFileSelect(event, '${docName}')" class="hidden">
                </label>
            </div>
        `;
        container.appendChild(row);
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

async function handleJPEGFileSelect(event, docName) {
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

    const badgeEl = document.getElementById(`docBadge_${docName.replace(/\s+/g, '_')}`);
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

// MY APPLICATIONS VIEW
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
        renderApplicationsList(state.applications);
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
                <h3 class="text-base font-bold text-slate-800">No applications submitted yet</h3>
                <p class="text-slate-500 text-xs mt-1 mb-4">Explore your eligible schemes and click "Apply Now" to submit applications.</p>
                <button onclick="switchView('recommendations')" class="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-xs shadow-md">View Matched Schemes</button>
            </div>
        `;
        initLucide();
        return;
    }

    apps.forEach(app => {
        const card = document.createElement("div");
        card.className = "bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm";

        let statusBadgeClass = "bg-indigo-50 text-indigo-700 border-indigo-200";
        if (app.status === "Approved") statusBadgeClass = "bg-emerald-50 text-emerald-700 border-emerald-200";
        else if (app.status === "Under Verification") statusBadgeClass = "bg-amber-50 text-amber-700 border-amber-200";
        else if (app.status === "Rejected") statusBadgeClass = "bg-rose-50 text-rose-700 border-rose-200";

        card.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4 mb-4">
                <div>
                    <span class="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md mb-1 inline-block">App ID: ${app.id}</span>
                    <h3 class="text-base font-extrabold text-slate-900">${app.scheme_name}</h3>
                    <span class="text-xs text-slate-400">Applied Date: ${app.applied_date}</span>
                </div>
                <span class="px-3.5 py-1.5 rounded-full text-xs font-extrabold border ${statusBadgeClass} flex items-center gap-1.5 self-start sm:self-center">
                    <i data-lucide="clock" class="w-3.5 h-3.5"></i> ${app.status}
                </span>
            </div>

            ${app.remarks ? `
                <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-600 flex items-start gap-2 mb-4">
                    <i data-lucide="info" class="w-4 h-4 text-indigo-600 shrink-0 mt-0.5"></i>
                    <span><strong>Remarks:</strong> ${app.remarks}</span>
                </div>
            ` : ''}

            <div class="flex items-center justify-between text-xs text-slate-500 pt-2">
                <span>Verified JPEG Documents Attached</span>
                <button onclick="showAppDetailAlert('${app.scheme_name}', '${app.id}', '${app.status}')" class="text-indigo-600 font-bold hover:underline flex items-center gap-1">
                    <i data-lucide="eye" class="w-3.5 h-3.5"></i> View Details
                </button>
            </div>
        `;
        trackerContainer.appendChild(card);
    });

    initLucide();
}

function showAppDetailAlert(schemeName, appId, status) {
    alert(`Application Details:\n\nScheme: ${schemeName}\nApplication ID: ${appId}\nStatus: ${status}\n\nDocuments uploaded in JPEG format and verified.`);
}

// CITIZEN PROFILE VIEW & CHANGE PASSWORD
async function loadProfileView() {
    if (!state.currentUser) {
        switchView("auth-landing");
        return;
    }

    const p = state.currentProfile || {};
    const u = state.currentUser;

    const el = (id, txt) => {
        const item = document.getElementById(id);
        if (item) item.textContent = txt;
    };

    el("profDisplayName", p.name || u.name || "Citizen");
    el("profDisplayEmail", u.email || "");
    el("profDisplayRole", `${u.role || 'citizen'} account`);
    el("profileInitials", (p.name || u.name || "C").charAt(0).toUpperCase());

    el("profValMobile", p.mobile_number || u.mobile_number || "Not provided");
    el("profValAgeGender", `${p.age || 25} Yrs, ${p.gender || 'Male'}`);
    el("profValMarital", p.marital_status || "Single");
    el("profValLocation", `${p.district || 'Varanasi'}, ${p.state || 'Uttar Pradesh'} (${p.rural_urban || 'Rural'})`);
    el("profValOccIncome", `${p.occupation || 'Farmer'} (₹${(p.annual_income || 150000).toLocaleString()}/yr)`);
    el("profValCategory", p.caste_category || "General");

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

// ADMIN DASHBOARD
async function loadAdminView() {
    if (!state.currentUser || state.currentUser.role !== "admin") {
        showNotification("Access Denied", "Admin privileges required.", "error");
        switchView("recommendations");
        return;
    }

    try {
        const analytics = await ApiService.getAdminAnalytics();
        renderAdminAnalytics(analytics);
        const schemes = await ApiService.getSchemes();
        renderAdminSchemes(schemes);
        const apps = await ApiService.getApplications();
        renderAdminApplications(apps);
    } catch (e) {
        console.error("Admin load error:", e);
    }
}

function switchAdminTab(tabName) {
    document.querySelectorAll(".admin-panel-section").forEach(panel => panel.classList.add("hidden"));
    const activePanel = document.getElementById(`adminPanel-${tabName}`);
    if (activePanel) {
        activePanel.classList.remove("hidden");
    }

    document.querySelectorAll(".admin-tab-btn").forEach(btn => {
        if (btn.id === `adminTabBtn-${tabName}`) {
            btn.className = "admin-tab-btn w-full p-3 flex items-center justify-between text-xs font-bold bg-purple-600 text-white rounded-xl shadow-sm cursor-pointer";
        } else {
            btn.className = "admin-tab-btn w-full p-3 flex items-center justify-between text-xs text-slate-300 hover:text-white rounded-xl cursor-pointer";
        }
    });
    initLucide();
}

function renderAdminAnalytics(analytics) {
    document.getElementById("adminStatUsers").textContent = analytics.total_users || "0";
    document.getElementById("adminStatSchemes").textContent = analytics.total_schemes || "0";
    document.getElementById("adminStatApps").textContent = analytics.total_applications || "0";
}

function renderAdminSchemes(schemes) {
    const tbody = document.getElementById("adminSchemesTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    schemes.forEach(s => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800 text-xs hover:bg-slate-800/40 transition";
        tr.innerHTML = `
            <td class="p-3.5 font-bold text-white max-w-xs leading-snug">${s.name}</td>
            <td class="p-3.5"><span class="px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-semibold">${s.category}</span></td>
            <td class="p-3.5 text-emerald-400 font-semibold truncate max-w-xs">${s.benefits}</td>
            <td class="p-3.5 flex items-center gap-2">
                <button onclick="adminDeleteScheme('${s.id}')" title="Delete Scheme" class="p-2 rounded-xl bg-rose-950/60 text-rose-400 hover:bg-rose-900 border border-rose-800/50 transition cursor-pointer"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    initLucide();
}

function renderAdminApplications(apps) {
    const tbody = document.getElementById("adminApplicationsTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (apps.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500 text-xs">No applications submitted yet.</td></tr>`;
        return;
    }

    apps.forEach(a => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800 text-xs hover:bg-slate-800/40 transition";
        tr.innerHTML = `
            <td class="p-3.5 font-bold text-purple-400">${a.id}</td>
            <td class="p-3.5 font-semibold text-white">${a.scheme_name}</td>
            <td class="p-3.5 text-slate-300">${a.user_name || a.user_id}</td>
            <td class="p-3.5 text-slate-400">${a.applied_date}</td>
            <td class="p-3.5">
                <select onchange="adminUpdateAppStatus('${a.id}', this.value)" class="p-2 rounded-xl border border-slate-700 text-xs font-semibold bg-slate-950 text-emerald-400 focus:outline-none cursor-pointer">
                    <option value="Applied" ${a.status === 'Applied' ? 'selected' : ''} class="bg-slate-900 text-white">Applied</option>
                    <option value="Under Verification" ${a.status === 'Under Verification' ? 'selected' : ''} class="bg-slate-900 text-white">Under Verification</option>
                    <option value="Approved" ${a.status === 'Approved' ? 'selected' : ''} class="bg-slate-900 text-white">Approved</option>
                    <option value="Rejected" ${a.status === 'Rejected' ? 'selected' : ''} class="bg-slate-900 text-white">Rejected</option>
                </select>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function adminUpdateAppStatus(appId, newStatus) {
    try {
        await ApiService.updateApplicationStatus(appId, newStatus, `Status updated by Admin to ${newStatus}`);
        showNotification("Status Updated", `Application ${appId} status updated to ${newStatus}`, "success");
    } catch (e) {
        showNotification("Error", e.message, "error");
    }
}

async function adminDeleteScheme(schemeId) {
    if (confirm("Are you sure you want to delete this scheme?")) {
        try {
            await ApiService.deleteScheme(schemeId);
            showNotification("Deleted", "Scheme removed from catalog.", "success");
            await loadAdminView();
        } catch (e) {
            showNotification("Error", e.message, "error");
        }
    }
}

function openAddSchemeModal() {
    document.getElementById("addSchemeModal")?.classList.remove("hidden");
}

function closeAddSchemeModal() {
    document.getElementById("addSchemeModal")?.classList.add("hidden");
}

function showNotification(title, message, type = "info") {
    const toast = document.createElement("div");
    let bg = "bg-slate-900 text-white";
    if (type === "success") bg = "bg-emerald-600 text-white";
    if (type === "error") bg = "bg-rose-600 text-white";

    toast.className = `${bg} px-4 py-3 rounded-xl shadow-2xl fixed bottom-6 left-6 z-50 flex items-center gap-3 transition-all duration-300 text-xs font-semibold max-w-sm`;
    toast.innerHTML = `<span><strong>${title}:</strong> ${message}</span>`;

    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
