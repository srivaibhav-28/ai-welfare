const API_BASE = (window.location.port === "8000") ? "" : "http://127.0.0.1:8000";

class ApiService {
    static getAuthToken() {
        return localStorage.getItem("welfare_token") || "";
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
                const err = await res.json().catch(() => ({ detail: "API Error" }));
                throw new Error(err.detail || "Server error occurred");
            }
            return await res.json();
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    }

    // Auth
    static async login(email, password) {
        const data = await this.request("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });
        this.setAuthToken(data.access_token);
        localStorage.setItem("welfare_user", JSON.stringify(data));
        return data;
    }

    static async register(name, email, mobile_number, password, role = "citizen") {
        const data = await this.request("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({ name, email, mobile_number, password, role })
        });
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

    static async applyForScheme(schemeId, uploadedDocuments = {}) {
        return await this.request("/api/applications/apply", {
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
}
