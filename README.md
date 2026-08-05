# AI Government Welfare Eligibility Assistant

An intelligent welfare scheme discovery, AI recommendation engine, document checklist, and application tracking system built for seamless deployment on Vercel with Supabase backend.

## 🚀 Features

- **AI Welfare Recommendation Engine**: Analyzes citizen demographic profiles (income, occupation, age, state, caste, BPL status) to evaluate scheme eligibility matching.
- **Vercel Serverless Functions**: Independent modular Python Serverless endpoints under `api/`.
- **Supabase Integration**: Full Supabase Database, Authentication, and Storage for document verification.
- **Smart Document Portal**: Strict JPEG file validation and automated checklist generator.
- **Admin Dashboard**: Scheme management, rule editor, application tracking, user management, notifications broadcast, and analytics CSV reports.
- **Conversational AI Assistant**: Multi-lingual assistant (English, Hindi, Telugu) providing real-time welfare advice.

## 📁 Project Structure

```
ai-welfare/
├── api/                   # Vercel Serverless Functions
│   ├── auth.py            # /api/auth/register, /api/auth/login, /api/auth/me
│   ├── users.py           # /api/profile, /api/users
│   ├── schemes.py         # /api/schemes, /api/schemes/{id}
│   ├── eligibility.py     # /api/evaluate, /api/chat
│   ├── applications.py    # /api/applications, /api/applications/apply
│   ├── documents.py       # /api/upload, /api/documents
│   ├── admin.py           # /api/admin/* (schemes, users, rules, notifications)
│   └── reports.py         # /api/admin/reports/export
├── app/                   # Core Business Logic Layer
│   ├── database/          # Supabase REST Database Layer
│   ├── models/            # Pydantic Schemas
│   ├── services/          # Auth, Eligibility, Chatbot, Storage Services
│   ├── utils/             # JPEG Validation and Helper utilities
│   └── config.py          # Central Environment Configuration
├── static/                # Frontend Assets
│   ├── css/styles.css     # Styling
│   ├── js/                # Client JavaScript (api.js, app.js, i18n.js)
│   ├── images/            # Static Images
│   └── assets/            # Static Assets
├── index.html             # Single Page Application Frontend
├── vercel.json            # Vercel Routing & Deployment Configuration
├── requirements.txt       # Python Runtime Dependencies
├── .env.example           # Environment Variables Template
└── README.md              # Project Documentation
```

## 🛠️ Local Development & Deployment

### 1. Environment Setup
Copy `.env.example` to `.env` and fill in your Supabase project credentials:
```bash
cp .env.example .env
```

### 2. Deploy directly to Vercel
Deploy to Vercel with a single command using the Vercel CLI:
```bash
vercel
```
Or connect your GitHub repository directly to Vercel. Set the environment variables (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`) in the Vercel Project Settings.
