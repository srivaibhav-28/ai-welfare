const getApiBase = () => {
    return "";
};
const API_BASE = getApiBase();

class ApiService {
    static getAuthToken() {
        let token = localStorage.getItem("welfare_token");
        if (!token) {
            const userStr = localStorage.getItem("welfare_user");
            if (userStr) {
                try {
                    const u = JSON.parse(userStr);
                    token = u.access_token || u.id;
                } catch(e) {}
            }
        }
        return token || null;
    }

    static setAuthToken(token) {
        if (token) {
            localStorage.setItem("welfare_token", token);
        } else {
            localStorage.removeItem("welfare_token");
        }
    }

    static getHeaders() {
        const headers = {
            "Content-Type": "application/json"
        };
        const token = this.getAuthToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    }

    static async request(endpoint, options = {}) {
        options.headers = {
            ...this.getHeaders(),
            ...(options.headers || {})
        };
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, options);
            if (!res.ok) {
                let errorMsg = `Server error (${res.status})`;
                try {
                    const errData = await res.json();
                    if (typeof errData.detail === "string") {
                        errorMsg = errData.detail;
                    } else if (Array.isArray(errData.detail)) {
                        errorMsg = errData.detail.map(e => e.msg || JSON.stringify(e)).join("; ");
                    } else if (errData.message) {
                        errorMsg = errData.message;
                    } else {
                        errorMsg = JSON.stringify(errData);
                    }
                } catch (e) {
                    const text = await res.text().catch(() => "");
                    if (text) errorMsg = text;
                }
                throw new Error(errorMsg);
            }
            return await res.json();
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            if (error instanceof TypeError && (error.message.includes("fetch") || error.message.includes("NetworkError"))) {
                const customErr = new Error("Server Unreachable: Cannot connect to backend server.");
                customErr.isNetworkError = true;
                throw customErr;
            }
            throw error;
        }
    }

    // Auth
    static async login(email, password) {
        try {
            const data = await this.request("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
            this.setAuthToken(data.access_token);
            localStorage.setItem("welfare_user", JSON.stringify(data));
            return data;
        } catch (err) {
            if (err.isNetworkError || (err.message && err.message.includes("fetch"))) {
                try {
                    const offlineUsers = JSON.parse(localStorage.getItem("welfare_offline_users") || "[]");
                    const found = offlineUsers.find(u => u.email.toLowerCase() === email.toLowerCase() && u.password === password);
                    if (found) {
                        this.setAuthToken(found.access_token);
                        localStorage.setItem("welfare_user", JSON.stringify(found));
                        return found;
                    }
                } catch (e) {}

                if (email === "citizen@welfare.gov" || email === "admin@welfare.gov") {
                    const demoUser = {
                        access_token: "demo-token-" + Date.now(),
                        token_type: "bearer",
                        user_id: email.startsWith("admin") ? "usr-admin-demo" : "usr-citizen-demo",
                        name: email.startsWith("admin") ? "System Admin" : "Demo Citizen",
                        email: email,
                        mobile_number: "9876543210",
                        role: email.startsWith("admin") ? "admin" : "citizen"
                    };
                    this.setAuthToken(demoUser.access_token);
                    localStorage.setItem("welfare_user", JSON.stringify(demoUser));
                    return demoUser;
                }
            }
            throw err;
        }
    }

    static async register(name, email, mobile_number, password, confirm_password = null, role = "citizen") {
        try {
            const cleanPassword = (password || "").trim();
            const cleanConfirmPassword = (confirm_password || password || "").trim();

            const payload = {
                name: (name || "").trim(),
                email: (email || "").trim(),
                mobile_number: (mobile_number || "").trim(),
                password: cleanPassword,
                confirm_password: cleanConfirmPassword,
                role: role
            };

            console.log("[API REGISTRATION PAYLOAD]");
            if (console.table) console.table(payload);
            console.log(JSON.stringify(payload, null, 2));

            const data = await this.request("/api/auth/register", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            if (data && data.access_token) {
                this.setAuthToken(data.access_token);
                localStorage.setItem("welfare_user", JSON.stringify(data));
            }
            return data;
        } catch (err) {
            if (err.isNetworkError || (err.message && err.message.includes("fetch"))) {
                console.warn("Backend server unreachable. Creating local offline account.");
                const offlineUser = {
                    access_token: "offline-token-" + Date.now(),
                    token_type: "bearer",
                    user_id: "usr-off-" + Math.random().toString(36).substring(2, 9),
                    name: name,
                    email: email,
                    mobile_number: mobile_number,
                    role: role
                };
                this.setAuthToken(offlineUser.access_token);
                localStorage.setItem("welfare_user", JSON.stringify(offlineUser));
                
                try {
                    const offlineUsers = JSON.parse(localStorage.getItem("welfare_offline_users") || "[]");
                    offlineUsers.push({ ...offlineUser, password: password });
                    localStorage.setItem("welfare_offline_users", JSON.stringify(offlineUsers));
                } catch (e) {}

                return offlineUser;
            }
            throw err;
        }
    }

    static async verifyOtp(email, otp) {
        const data = await this.request("/api/auth/verify-otp", {
            method: "POST",
            body: JSON.stringify({ email, otp })
        });
        if (data && data.access_token) {
            this.setAuthToken(data.access_token);
            localStorage.setItem("welfare_user", JSON.stringify(data));
        }
        return data;
    }

    static async adminLogin(email, password) {
        const data = await this.request("/api/admin/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });
        if (data && data.access_token) {
            this.setAuthToken(data.access_token);
            localStorage.setItem("welfare_user", JSON.stringify(data));
        }
        return data;
    }

    static async sendOtp(email) {
        return await this.request("/api/auth/send-otp", {
            method: "POST",
            body: JSON.stringify({ email })
        });
    }

    static async resendOtp(email) {
        return await this.request("/api/auth/resend-otp", {
            method: "POST",
            body: JSON.stringify({ email })
        });
    }

    static async googleLogin(email, name, role = "citizen", picture = null) {
        const data = await this.request("/api/auth/google", {
            method: "POST",
            body: JSON.stringify({ email, name, role, picture })
        });
        if (data && data.access_token) {
            this.setAuthToken(data.access_token);
            localStorage.setItem("welfare_user", JSON.stringify(data));
        }
        return data;
    }

    static async changePassword(oldPassword, newPassword) {
        return await this.request("/api/auth/change-password", {
            method: "POST",
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
        });
    }

    static async getCurrentUser() {
        return await this.request("/api/auth/me");
    }

    // Profile
    static async getProfile() {
        return await this.request("/api/profile");
    }

    static async updateProfile(profileData) {
        return await this.request("/api/profile", {
            method: "POST",
            body: JSON.stringify(profileData)
        });
    }

    // Schemes & Evaluation
    static async getSchemes() {
        return await this.request("/api/schemes");
    }

    static async searchSchemes(query) {
        return await this.request(`/api/schemes/search?q=${encodeURIComponent(query)}`);
    }

    static async evaluateProfile(profileData) {
        return await this.request("/api/evaluate", {
            method: "POST",
            body: JSON.stringify(profileData)
        });
    }

    // Documents & File Upload
    static async uploadDocumentFile(file, documentName) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("document_name", documentName);

        const token = this.getAuthToken();
        const headers = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(`${API_BASE}/api/upload`, {
            method: "POST",
            headers,
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Upload failed" }));
            throw new Error(err.detail || "File upload failed");
        }

        return await res.json();
    }

    static async getDocuments() {
        return await this.request("/api/documents");
    }

    static async updateDocumentStatus(documentName, status, fileName = null) {
        return await this.request("/api/documents/status", {
            method: "POST",
            body: JSON.stringify({ document_name: documentName, status, file_name: fileName })
        });
    }

    // Applications
    static async getApplications() {
        return await this.request("/api/applications");
    }

    static async initiateAppOtp(schemeId, uploadedDocuments = {}) {
        return await this.request("/api/applications/initiate-otp", {
            method: "POST",
            body: JSON.stringify({ scheme_id: schemeId, uploaded_documents: uploadedDocuments })
        });
    }

    static async verifyAndSubmitAppOtp(schemeId, otp, uploadedDocuments = {}) {
        return await this.request("/api/applications/verify-submit-otp", {
            method: "POST",
            body: JSON.stringify({ scheme_id: schemeId, otp, uploaded_documents: uploadedDocuments })
        });
    }

    static async resendAppOtp(schemeId) {
        return await this.request("/api/applications/resend-app-otp", {
            method: "POST",
            body: JSON.stringify({ scheme_id: schemeId })
        });
    }

    static async applyForScheme(schemeId, uploadedDocuments = {}) {
        return await this.initiateAppOtp(schemeId, uploadedDocuments);
    }

    static async directApply(schemeId, uploadedDocuments = {}) {
        return await this.request("/api/applications/direct-apply", {
            method: "POST",
            body: JSON.stringify({ scheme_id: schemeId, uploaded_documents: uploadedDocuments })
        });
    }

    static async updateApplicationStatus(appId, status, remarks = "") {
        return await this.request(`/api/applications/${appId}/status`, {
            method: "PUT",
            body: JSON.stringify({ status, remarks })
        });
    }

    // Chatbot
    static async sendChatMessage(message, language = "en", profileData = null) {
        return await this.request("/api/chat", {
            method: "POST",
            body: JSON.stringify({ message, language, profile_data: profileData })
        });
    }

    // Admin
    static async createScheme(schemeData) {
        return await this.request("/api/admin/schemes", {
            method: "POST",
            body: JSON.stringify(schemeData)
        });
    }

    static async updateScheme(schemeId, schemeData) {
        return await this.request(`/api/admin/schemes/${schemeId}`, {
            method: "PUT",
            body: JSON.stringify(schemeData)
        });
    }

    static async deleteScheme(schemeId) {
        return await this.request(`/api/admin/schemes/${schemeId}`, {
            method: "DELETE"
        });
    }

    static async getAdminUsers() {
        return await this.request("/api/admin/users");
    }

    static async getAdminAnalytics() {
        return await this.request("/api/admin/analytics");
    }

    static async updateSchemeRules(schemeId, criteria, requiredDocuments = null) {
        return await this.request(`/api/admin/schemes/${schemeId}/rules`, {
            method: "PUT",
            body: JSON.stringify({ criteria, required_documents: requiredDocuments })
        });
    }

    static async updateUserStatus(userId, isBlocked) {
        return await this.request(`/api/admin/users/${userId}/status`, {
            method: "PUT",
            body: JSON.stringify({ is_blocked: isBlocked })
        });
    }

    static async deleteUser(userId) {
        return await this.request(`/api/admin/users/${userId}`, {
            method: "DELETE"
        });
    }

    static async verifyDocument(userId, documentName, status, remarks = "") {
        return await this.request("/api/admin/documents/verify", {
            method: "POST",
            body: JSON.stringify({ user_id: userId, document_name: documentName, status, remarks })
        });
    }

    static async getAdminNotifications() {
        return await this.request("/api/admin/notifications");
    }

    static async sendAdminNotification(title, message, targetUserId = null, type = "info") {
        return await this.request("/api/admin/notifications", {
            method: "POST",
            body: JSON.stringify({ title, message, target_user_id: targetUserId, type })
        });
    }

    static async getUserNotifications() {
        return await this.request("/api/notifications");
    }

    static async getSupabaseStatus() {
        return await this.request("/api/admin/supabase-status");
    }

    static getExportReportsUrl() {
        const token = this.getAuthToken();
        return `${API_BASE}/api/admin/reports/export?token=${encodeURIComponent(token)}`;
    }
}
