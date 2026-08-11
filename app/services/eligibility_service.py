import re
from datetime import datetime
from typing import Dict, List, Any

class EligibilityEngine:
    @staticmethod
    def _calculate_days_remaining(last_date_str: str) -> str:
        if not last_date_str or "open" in last_date_str.lower() or "ongoing" in last_date_str.lower():
            return "Open Round the Year"
        try:
            # Parse DD-MM-YYYY
            parts = last_date_str.split("-")
            if len(parts) == 3:
                target = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                today = datetime.now()
                delta = (target - today).days
                if delta > 0:
                    return f"{delta} Days Remaining"
                elif delta == 0:
                    return "Closes Today!"
                else:
                    return "Closed for Applications"
        except Exception:
            pass
        return last_date_str

    @staticmethod
    def evaluate_scheme(profile: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
        criteria = scheme.get("criteria", {})
        reasons_eligible = []
        reasons_ineligible = []
        score_weight = 0
        total_weight = 0

        # Age evaluation
        age = profile.get("age", 25)
        min_age = criteria.get("min_age")
        max_age = criteria.get("max_age")
        
        if min_age is not None:
            total_weight += 20
            if age >= min_age:
                score_weight += 20
                reasons_eligible.append(f"Age ({age} yrs) satisfies minimum threshold of {min_age}+ years.")
            else:
                reasons_ineligible.append(f"Age ({age} yrs) is below required minimum of {min_age}+ years.")

        if max_age is not None:
            total_weight += 20
            if age <= max_age:
                score_weight += 20
                reasons_eligible.append(f"Age ({age} yrs) is within upper ceiling of {max_age} years.")
            else:
                reasons_ineligible.append(f"Age ({age} yrs) exceeds maximum age limit of {max_age} years.")

        # Income evaluation
        annual_income = profile.get("annual_income", 150000)
        max_income = criteria.get("max_income")
        if max_income is not None:
            total_weight += 25
            if annual_income <= max_income:
                score_weight += 25
                reasons_eligible.append(f"Annual Income (₹{annual_income:,.0f}) is below eligibility ceiling of ₹{max_income:,.0f}.")
            else:
                reasons_ineligible.append(f"Annual Income (₹{annual_income:,.0f}) exceeds ceiling limit of ₹{max_income:,.0f}.")

        # BPL Status
        if criteria.get("bpl_status"):
            total_weight += 25
            if profile.get("bpl_status") or annual_income <= 150000:
                score_weight += 25
                reasons_eligible.append("BPL / Economically Weaker Section (EWS) profile verified.")
            else:
                reasons_ineligible.append("Requires BPL Ration Card or annual family income under ₹1,50,000.")

        # Farmer Status
        if criteria.get("farmer_status"):
            total_weight += 30
            if profile.get("farmer_status") or profile.get("occupation", "").lower() in ["farmer", "agriculture"]:
                score_weight += 30
                reasons_eligible.append("Registered Agricultural Landholder / Farmer status confirmed.")
            else:
                reasons_ineligible.append("Requires Agricultural Land Certificate or Farmer registration.")

        # Student Status
        if criteria.get("student_status"):
            total_weight += 25
            if profile.get("student_status") or profile.get("occupation", "").lower() in ["student", "scholar"]:
                score_weight += 25
                reasons_eligible.append("Active Enrolled Student status verified.")
            else:
                reasons_ineligible.append("Scheme is reserved for enrolled students.")

        # Gender matching
        req_gender = criteria.get("gender")
        if req_gender:
            total_weight += 20
            profile_gender = profile.get("gender", "Male")
            if profile_gender.lower() == req_gender.lower():
                score_weight += 20
                reasons_eligible.append(f"Gender ({profile_gender}) matches target demographic.")
            else:
                reasons_ineligible.append(f"Scheme is designated exclusively for {req_gender} citizens.")

        # Widow status
        if criteria.get("widow_status"):
            total_weight += 30
            if profile.get("widow_status"):
                score_weight += 30
                reasons_eligible.append("Widow pension eligibility status verified.")
            else:
                reasons_ineligible.append("Requires Death Certificate of spouse / Widow status.")

        # Disability status
        if criteria.get("disability_status"):
            total_weight += 30
            if profile.get("disability_status"):
                score_weight += 30
                reasons_eligible.append("Benchmark Disability Certificate (40%+) verified.")
            else:
                reasons_ineligible.append("Requires Medical Board Disability Certificate (40%+ benchmark).")

        # Occupation match list
        req_occupations = criteria.get("occupation_in")
        if req_occupations:
            total_weight += 20
            prof_occ = profile.get("occupation", "")
            if prof_occ in req_occupations or any(occ.lower() in prof_occ.lower() for occ in req_occupations):
                score_weight += 20
                reasons_eligible.append(f"Occupation ({prof_occ}) matches eligible category.")
            else:
                reasons_ineligible.append(f"Occupation ({prof_occ}) is not listed under eligible vendor/labor categories.")

        # State restriction
        state_restriction = scheme.get("state_restriction", "All")
        if state_restriction and state_restriction != "All":
            total_weight += 20
            user_state = profile.get("state", "Uttar Pradesh")
            if user_state.lower() == state_restriction.lower():
                score_weight += 20
                reasons_eligible.append(f"State Residency ({user_state}) matches scheme location requirement.")
            else:
                reasons_ineligible.append(f"Scheme is restricted to residents of {state_restriction}.")

        if total_weight == 0:
            total_weight = 100
            score_weight = 85
            reasons_eligible.append("General public welfare scheme open to all eligible citizens.")

        is_eligible = (len(reasons_ineligible) == 0)
        match_score = int((score_weight / total_weight) * 100) if total_weight > 0 else 85
        if is_eligible and match_score < 75:
            match_score = 85

        if match_score >= 85:
            confidence_level = "High Confidence"
        elif match_score >= 70:
            confidence_level = "Medium Confidence"
        else:
            confidence_level = "Low Confidence"

        if is_eligible and not reasons_eligible:
            reasons_eligible.append("Meets all baseline demographic and socio-economic criteria.")

        # Generate "Why Recommended" personalized narrative (Module 2)
        occ = profile.get("occupation", "Citizen")
        state_name = profile.get("state", "India")
        why_recommended = f"Recommended based on your profile as a {occ} residing in {state_name} with family income ₹{annual_income:,.0f}."

        # Format Why Eligible items with checkmarks
        formatted_why_eligible = [f"✔ {r}" for r in reasons_eligible]

        days_remaining = EligibilityEngine._calculate_days_remaining(scheme.get("last_date", ""))

        return {
            "scheme_id": scheme["id"],
            "scheme_name": scheme["name"],
            "category": scheme["category"],
            "department": f"{scheme['category']} Department, Govt of India",
            "match_score": match_score,
            "confidence_level": confidence_level,
            "is_eligible": is_eligible,
            "reasons_why_eligible": reasons_eligible,
            "formatted_why_eligible": formatted_why_eligible,
            "reasons_why_ineligible": reasons_ineligible,
            "why_recommended": why_recommended,
            "required_documents": scheme.get("required_documents", []),
            "benefits": scheme.get("benefits", ""),
            "official_link": scheme.get("official_link", "#"),
            "last_date": scheme.get("last_date", "N/A"),
            "days_remaining": days_remaining,
            "scheme_details": scheme
        }

    @classmethod
    def analyze_all(cls, profile: Dict[str, Any], schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
        evaluations = []
        eligible_count = 0
        all_documents = set()
        missed_benefits = []

        for s in schemes:
            res = cls.evaluate_scheme(profile, s)
            evaluations.append(res)
            if res["is_eligible"]:
                eligible_count += 1
                for doc in res["required_documents"]:
                    all_documents.add(doc)
            else:
                # Missed Benefits Detector (Module 3)
                # If citizen scores >= 40% or has <= 2 missing criteria, flag as missed opportunity
                if res["match_score"] >= 40 or len(res["reasons_why_ineligible"]) <= 2:
                    missing_items = res["reasons_why_ineligible"]
                    missed_benefits.append({
                        "scheme_id": res["scheme_id"],
                        "scheme_name": res["scheme_name"],
                        "category": res["category"],
                        "benefits": res["benefits"],
                        "match_score": res["match_score"],
                        "missing_requirements": missing_items,
                        "action_guidance": f"Complete or obtain: {'; '.join(missing_items)} to unlock this benefit."
                    })

        base_docs = {"Aadhaar Card", "Income Certificate", "Residence Certificate", "Active Bank Passbook"}
        all_documents.update(base_docs)

        evaluations.sort(key=lambda x: x["match_score"], reverse=True)
        missed_benefits.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "total_schemes_analyzed": len(schemes),
            "eligible_schemes_count": eligible_count,
            "missed_benefits_count": len(missed_benefits),
            "recommendations": evaluations,
            "missed_benefits": missed_benefits,
            "smart_document_checklist": list(all_documents)
        }
