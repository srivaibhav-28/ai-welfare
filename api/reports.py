import io
import csv
import datetime
from typing import Dict, Any
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.services.auth_service import require_admin_user

app = FastAPI(title="AI Welfare Reports API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/admin/reports/export")
async def admin_export_reports(admin: Dict[str, Any] = Depends(require_admin_user)):
    apps = db.get_applications()
    users = db.get_users()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Application ID", "Applicant Name", "Applicant Email", "Scheme Name", "Applied Date", "Status", "Remarks"])

    user_map = {u["id"]: u for u in users}
    for a in apps:
        u_info = user_map.get(a.get("user_id"), {})
        writer.writerow([
            a.get("id", ""),
            a.get("user_name", u_info.get("name", "N/A")),
            a.get("user_email", u_info.get("email", "N/A")),
            a.get("scheme_name", ""),
            a.get("applied_date", ""),
            a.get("status", ""),
            a.get("remarks", "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=welfare_applications_report_{datetime.date.today().isoformat()}.csv"}
    )
