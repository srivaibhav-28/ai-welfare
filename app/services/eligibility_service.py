from typing import Dict, List, Any

class EligibilityEngine:
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
                reasons_eligible.append(f"Age is {age} years (Meets minimum age requirement of {min_age}+).")
            else:
                reasons_ineligible.append(f"Age is {age} years (Minimum age required is {min_age}+).")

        if max_age is not None:
            total_weight += 20
            if age <= max_age:
                score_weight += 20
                reasons_eligible.append(f"Age is {age} years (Within target age limit of up to {max_age} years).")
            else:
                reasons_ineligible.append(f"Age is {age} years (Exceeds maximum age limit of {max_age} years).")

        # Income evaluation
        annual_income = profile.get("annual_income", 0)
        max_income = criteria.get("max_income")
        if max_income is not None:
            total_weight += 25
            if annual_income <= max_income:
                score_weight += 25
                reasons_eligible.append(f"Annual income of ₹{annual_income:,.0f} is within the threshold limit of ₹{max_income:,.0f}.")
            else:
                reasons_ineligible.append(f"Annual income of ₹{annual_income:,.0f} exceeds the eligibility limit of ₹{max_income:,.0f}.")

        # BPL Status
        if criteria.get("bpl_status"):
            total_weight += 25
            if profile.get("bpl_status") or profile.get("annual_income", 0) <= 150000:
                score_weight += 25
                reasons_eligible.append("BPL / Economically Weaker Section status confirmed.")
            else:
                reasons_ineligible.append("Requires BPL Ration Card or income below ₹1,50,000.")

        # Farmer Status
        if criteria.get("farmer_status"):
            total_weight += 30
            if profile.get("farmer_status") or profile.get("occupation", "").lower() in ["farmer", "agriculture"]:
                score_weight += 30
                reasons_eligible.append("Registered agricultural farmer profile matched.")
            else:
                reasons_ineligible.append("Scheme is reserved for registered farmer households.")

        # Student Status
        if criteria.get("student_status"):
            total_weight += 25
            if profile.get("student_status") or profile.get("occupation", "").lower() in ["student", "scholar"]:
                score_weight += 25
                reasons_eligible.append("Currently enrolled active student profile verified.")
            else:
                reasons_ineligible.append("Scheme is designated for enrolled students.")

        # Gender matching
        req_gender = criteria.get("gender")
        if req_gender:
            total_weight += 20
            profile_gender = profile.get("gender", "Male")
            if profile_gender.lower() == req_gender.lower():
                score_weight += 20
                reasons_eligible.append(f"Gender ({profile_gender}) matches scheme target group.")
            else:
                reasons_ineligible.append(f"Scheme is specifically designated for {req_gender} citizens.")

        # Widow status
        if criteria.get("widow_status"):
            total_weight += 30
            if profile.get("widow_status"):
                score_weight += 30
                reasons_eligible.append("Widow status verified for social pension eligibility.")
            else:
                reasons_ineligible.append("Scheme is intended for widowed citizens.")

        # Disability status
        if criteria.get("disability_status"):
            total_weight += 30
            if profile.get("disability_status"):
                score_weight += 30
                reasons_eligible.append("Benchmark disability status verified for special assistance.")
            else:
                reasons_ineligible.append("Scheme is reserved for Persons with Benchmark Disabilities.")

        # Occupation match list
        req_occupations = criteria.get("occupation_in")
        if req_occupations:
            total_weight += 20
            prof_occ = profile.get("occupation", "")
            if prof_occ in req_occupations or any(occ.lower() in prof_occ.lower() for occ in req_occupations):
                score_weight += 20
                reasons_eligible.append(f"Occupation ({prof_occ}) matches eligible category.")
            else:
                reasons_ineligible.append(f"Occupation ({prof_occ}) is not in eligible vendor/worker list.")

        # Aadhaar availability check
        if criteria.get("requires_aadhaar", True) and not profile.get("aadhaar_available", True):
            reasons_ineligible.append("Valid Aadhaar card is required for this scheme.")
        elif profile.get("aadhaar_available", True):
            reasons_eligible.append("Aadhaar Card availability verified.")

        # Bank account availability check
        if criteria.get("requires_bank_account", True) and not profile.get("bank_account_available", True):
            reasons_ineligible.append("Active Bank Account is required for direct benefit transfer (DBT).")
        elif profile.get("bank_account_available", True):
            reasons_eligible.append("Active Bank Account verified for Direct Benefit Transfer.")

        # Senior Citizen check
        if criteria.get("senior_citizen_status"):
            total_weight += 25
            if profile.get("senior_citizen_status") or age >= 60:
                score_weight += 25
                reasons_eligible.append(f"Senior Citizen criteria met (Age {age} years).")
            else:
                reasons_ineligible.append(f"Scheme requires senior citizen status (60+ years). Current age is {age}.")

        # Caste / Social Category check
        req_castes = criteria.get("caste_in")
        if req_castes:
            total_weight += 20
            user_caste = profile.get("caste_category", "General")
            if user_caste in req_castes:
                score_weight += 20
                reasons_eligible.append(f"Social Category ({user_caste}) matches scheme target group.")
            else:
                reasons_ineligible.append(f"Social Category ({user_caste}) is not in eligible categories ({', '.join(req_castes)}).")

        # Marital Status check
        req_marital = criteria.get("marital_status_in")
        if req_marital:
            total_weight += 25
            user_marital = profile.get("marital_status", "Single")
            if user_marital in req_marital:
                score_weight += 25
                reasons_eligible.append(f"Marital Status ({user_marital}) satisfies scheme requirements.")
            else:
                reasons_ineligible.append(f"Marital Status ({user_marital}) does not match scheme requirements.")

        # Default fallback weight if scheme has minimal rules
        if total_weight == 0:
            total_weight = 100
            score_weight = 85
            reasons_eligible.append("General public welfare scheme open to eligible citizens.")

        # Calculate final percentage
        is_eligible = (len(reasons_ineligible) == 0)
        match_score = int((score_weight / total_weight) * 100) if total_weight > 0 else 85
        if is_eligible and match_score < 75:
            match_score = 85

        # Base generic reasons if high match
        if is_eligible and not reasons_eligible:
            reasons_eligible.append("Meets all baseline demographic and socio-economic criteria.")

        return {
            "scheme_id": scheme["id"],
            "scheme_name": scheme["name"],
            "category": scheme["category"],
            "match_score": match_score,
            "is_eligible": is_eligible,
            "reasons_why_eligible": reasons_eligible,
            "reasons_why_ineligible": reasons_ineligible,
            "required_documents": scheme.get("required_documents", []),
            "benefits": scheme.get("benefits", ""),
            "official_link": scheme.get("official_link", "#"),
            "last_date": scheme.get("last_date", "N/A"),
            "scheme_details": scheme
        }

    @classmethod
    def analyze_all(cls, profile: Dict[str, Any], schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
        evaluations = []
        eligible_count = 0
        all_documents = set()

        for s in schemes:
            res = cls.evaluate_scheme(profile, s)
            evaluations.append(res)
            if res["is_eligible"]:
                eligible_count += 1
                for doc in res["required_documents"]:
                    all_documents.add(doc)

        # Always include baseline documents
        base_docs = {"Aadhaar Card", "Income Certificate", "Residence Certificate", "Active Bank Passbook"}
        all_documents.update(base_docs)

        # Sort evaluations by match_score descending
        evaluations.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "total_schemes_analyzed": len(schemes),
            "eligible_schemes_count": eligible_count,
            "recommendations": evaluations,
            "smart_document_checklist": list(all_documents)
        }
