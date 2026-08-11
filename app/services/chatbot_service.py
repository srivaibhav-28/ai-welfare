from typing import Dict, Any, List
from app.database.supabase_db import db
from app.services.eligibility_service import EligibilityEngine

CONVERSATIONAL_STEPS = [
    {
        "field": "occupation",
        "question_en": "Hello! I am your AI Welfare Assistant. I will help you discover eligible government schemes step-by-step.\n\nFirst, **what is your occupation?**",
        "question_hi": "नमस्ते! मैं आपका एआई कल्याण सहायक हूं। मैं आपको पात्र सरकारी योजनाओं को खोजने में मदद करूंगा।\n\nसबसे पहले, **आपका व्यवसाय क्या है?**",
        "question_te": "నమస్కారం! నేను మీ AI సంక్షేమ సహాయకుడిని. ప్రభుత్వ పథకాలను కనుగొనడంలో నేను మీకు సహాయం చేస్తాను.\n\nమొదట, **మీ వృత్తి ఏమిటి?**",
        "options": ["Student", "Farmer", "Self-Employed", "Daily Wager", "Private Employee", "Unemployed"]
    },
    {
        "field": "state",
        "question_en": "Great! **Which State or Union Territory do you reside in?**",
        "question_hi": "बहुत बढ़िया! **आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?**",
        "question_te": "గొప్పది! **మీరు ఏ రాష్ట్రంలో లేదా కేంద్ర పాలిత ప్రాంతంలో నివసిస్తున్నారు?**",
        "options": ["Uttar Pradesh", "Telangana", "Maharashtra", "Bihar", "Delhi", "Karnataka", "Other"]
    },
    {
        "field": "annual_income",
        "question_en": "Got it! **What is your estimated annual family income (in ₹)?**",
        "question_hi": "समझा! **आपकी अनुमानित वार्षिक पारिवारिक आय (₹ में) कितनी है?**",
        "question_te": "అర్థమైంది! **మీ కుటుంబ వార్షిక ఆదాయం ఎంత (₹ లలో)?**",
        "options": ["₹50,000", "₹1,000,000", "₹1,50,000", "₹2,50,000", "₹5,00,000+"]
    },
    {
        "field": "age",
        "question_en": "Thank you! **What is your current age?**",
        "question_hi": "धन्यवाद! **आपकी वर्तमान आयु क्या है?**",
        "question_te": "ధన్యవాదాలు! **మీ ప్రస్తుత వయస్సు ఎంత?**",
        "options": ["18", "25", "42", "60", "65"]
    },
    {
        "field": "gender",
        "question_en": "Understood. **What is your gender?**",
        "question_hi": "समझ गया। **आपका लिंग क्या है?**",
        "question_te": "అర్థమైంది. **మీ లింగం ఏమిటి?**",
        "options": ["Male", "Female", "Transgender"]
    },
    {
        "field": "caste_category",
        "question_en": "Which **social category / caste** do you belong to?",
        "question_hi": "आप किस **सामाजिक वर्ग / जाति** से संबंधित हैं?",
        "question_te": "మీరు ఏ **సామాజిక వర్గం / కులానికి** చెందినవారు?",
        "options": ["General", "OBC", "SC", "ST", "EWS"]
    },
    {
        "field": "bpl_status",
        "question_en": "Do you hold a **BPL Ration Card** or belong to Below Poverty Line?",
        "question_hi": "क्या आपके पास **बीपीएल राशन कार्ड** है?",
        "question_te": "మీకు **BPL రేషన్ కార్డ్** ఉందా?",
        "options": ["Yes (BPL Cardholder)", "No"]
    }
]

class AIChatbot:
    @staticmethod
    def process_conversational_interview(step: int, user_answer: str, current_session_data: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        Module 1: AI Welfare Assistant Conversational Questionnaire Step Handler
        """
        session = dict(current_session_data or {})
        
        if step < len(CONVERSATIONAL_STEPS):
            curr_q = CONVERSATIONAL_STEPS[step]
            field_name = curr_q["field"]

            # Parse answer into field
            ans_clean = user_answer.strip()
            if field_name == "annual_income":
                nums = [int(s) for s in ans_clean.replace(",", "").split() if s.isdigit()]
                if "50,000" in ans_clean or "50000" in ans_clean:
                    session["annual_income"] = 50000
                elif "1,00,000" in ans_clean or "100000" in ans_clean or "1 Lakh" in ans_clean:
                    session["annual_income"] = 100000
                elif "1,50,000" in ans_clean or "150000" in ans_clean:
                    session["annual_income"] = 150000
                elif "2,50,000" in ans_clean or "250000" in ans_clean:
                    session["annual_income"] = 250000
                elif nums:
                    session["annual_income"] = nums[0]
                else:
                    session["annual_income"] = 150000

            elif field_name == "age":
                nums = [int(s) for s in ans_clean.split() if s.isdigit()]
                session["age"] = nums[0] if nums else 25

            elif field_name == "bpl_status":
                session["bpl_status"] = "yes" in ans_clean.lower() or "bpl" in ans_clean.lower()

            elif field_name == "occupation":
                session["occupation"] = ans_clean
                if "farmer" in ans_clean.lower() or "agriculture" in ans_clean.lower():
                    session["farmer_status"] = True
                if "student" in ans_clean.lower():
                    session["student_status"] = True

            else:
                session[field_name] = ans_clean

            # Advance to next question
            next_step = step + 1
            if next_step < len(CONVERSATIONAL_STEPS):
                nq = CONVERSATIONAL_STEPS[next_step]
                q_text = nq.get(f"question_{language}", nq["question_en"])
                return {
                    "is_interview": True,
                    "completed": False,
                    "next_step": next_step,
                    "response": q_text,
                    "suggested_actions": nq["options"],
                    "session_data": session
                }
            else:
                # Completed questionnaire! Save profile & evaluate schemes
                schemes = db.get_schemes()
                eval_res = EligibilityEngine.analyze_all(session, schemes)

                completion_msg_en = f"🎉 **Evaluation Complete!**\n\nI have saved your profile and analyzed {eval_res['total_schemes_analyzed']} welfare schemes. You qualify for **{eval_res['eligible_schemes_count']} eligible schemes**!\n\nYour personalized recommendations are ready."
                completion_msg_hi = f"🎉 **मूल्यांकन पूरा हुआ!**\n\nमैंने आपकी प्रोफ़ाइल सहेज ली है। आप **{eval_res['eligible_schemes_count']} योजनाओं** के लिए पात्र हैं!"
                completion_msg_te = f"🎉 **మూల్యాంకనం పూర్తయింది!**\n\nమీరు **{eval_res['eligible_schemes_count']} పథకాలకు** అర్హులు!"

                final_msg = completion_msg_en
                if language == "hi":
                    final_msg = completion_msg_hi
                elif language == "te":
                    final_msg = completion_msg_te

                return {
                    "is_interview": True,
                    "completed": True,
                    "response": final_msg,
                    "evaluation_result": eval_res,
                    "session_data": session,
                    "suggested_actions": ["View Matched Schemes", "Check Missed Benefits", "Upload Documents"]
                }

        # Fallback start interview
        first_q = CONVERSATIONAL_STEPS[0]
        return {
            "is_interview": True,
            "completed": False,
            "next_step": 0,
            "response": first_q.get(f"question_{language}", first_q["question_en"]),
            "suggested_actions": first_q["options"],
            "session_data": {}
        }

    @staticmethod
    def generate_response(user_message: str, language: str = "en", profile_data: Dict[str, Any] = None) -> Dict[str, Any]:
        msg_lower = user_message.lower()
        schemes = db.get_schemes()

        if "start interview" in msg_lower or "questionnaire" in msg_lower or "find schemes" in msg_lower:
            return AIChatbot.process_conversational_interview(0, "", {}, language)

        profile_context = ""
        if profile_data:
            eval_res = EligibilityEngine.analyze_all(profile_data, schemes)
            eligible_names = [r["scheme_name"] for r in eval_res["recommendations"] if r["is_eligible"]]
            profile_context = f"Based on your profile ({profile_data.get('occupation')}, Income ₹{profile_data.get('annual_income', 0):,.0f}), you qualify for {len(eligible_names)} schemes!"

        if "hello" in msg_lower or "hi" in msg_lower or "namaste" in msg_lower:
            reply_en = f"Namaste! I am your AI Government Welfare Eligibility Assistant. {profile_context} How can I assist you with scheme eligibility, required documents, or application tracking today?"
            reply_hi = f"नमस्ते! मैं आपका एआई सरकारी कल्याण पात्रता सहायक हूं। {profile_context}"
            reply_te = f"నమస్కారం! నేను మీ AI ప్రభుత్వ సంక్షేమ అర్హత అసిస్టెంట్‌ని. {profile_context}"
            actions = ["Start AI Conversational Assistant", "Check My Schemes", "Required Documents", "Track Applications"]
        elif "kisan" in msg_lower or "farmer" in msg_lower:
            reply_en = "🌾 **PM-Kisan Samman Nidhi Scheme**:\n- **Benefit**: ₹6,000 per year in 3 equal installments directly to landholding farmers.\n- **Eligibility**: Landholding farmers with annual income under ₹3 Lakh."
            reply_hi = "🌾 **पीएम-किसान सम्मान निधि योजना**:\n- **लाभ**: ₹6,000 प्रति वर्ष 3 किस्तों में।"
            reply_te = "🌾 **PM-కిసాన్ సమ్మాన్ నిధి పథకం**:\n- **ప్రయోజనం**: సంవత్సరానికి ₹6,000."
            actions = ["Apply PM-Kisan", "Check Document Checklist"]
        else:
            reply_en = f"I am your AI Welfare Assistant. I can help analyze your eligibility for {len(schemes)}+ national welfare schemes. Click 'Start AI Conversational Assistant' to discover schemes step-by-step!"
            reply_hi = f"मैं आपका AI कल्याण सहायक हूं। 1-क्लिक में अपनी पात्रता की जांच करने के लिए 'बातचीत शुरू करें' पर क्लिक करें!"
            reply_te = f"నేను మీ AI సంక్షేమ సహాయకుడిని."
            actions = ["Start AI Conversational Assistant", "View Eligible Schemes", "Upload Documents"]

        final_text = reply_en
        if language == "hi":
            final_text = reply_hi
        elif language == "te":
            final_text = reply_te

        return {
            "response": final_text,
            "suggested_actions": actions,
            "language": language
        }

    @staticmethod
    def generate_scheme_content(name: str, category: str) -> Dict[str, Any]:
        """
        Module 8: AI Content Generation for Admins
        Auto-generates scheme description, benefits, and FAQs.
        """
        return {
            "description": f"Official government welfare initiative under the {category} category aimed at providing targeted financial assistance, social security, and empowerment for eligible beneficiaries.",
            "benefits": f"Direct Benefit Transfer (DBT) cash transfer and official subsidies for verified {category} applicants.",
            "faqs": [
                {"question": f"Who is eligible for {name}?", "answer": f"Citizens satisfying {category} baseline demographic and income criteria."},
                {"question": "How are benefits delivered?", "answer": "Transferred directly into Aadhaar-linked bank accounts via DBT."}
            ]
        }
