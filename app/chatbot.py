from typing import Dict, Any, List
from app.database import db
from app.engine import EligibilityEngine

class AIChatbot:
    @staticmethod
    def generate_response(user_message: str, language: str = "en", profile_data: Dict[str, Any] = None) -> Dict[str, Any]:
        msg_lower = user_message.lower()
        schemes = db.get_schemes()
        
        # Check profile context
        profile_context = ""
        if profile_data:
            eval_res = EligibilityEngine.analyze_all(profile_data, schemes)
            eligible_names = [r["scheme_name"] for r in eval_res["recommendations"] if r["is_eligible"]]
            profile_context = f"Based on your profile ({profile_data.get('occupation')}, Income ₹{profile_data.get('annual_income', 0):,.0f}), you qualify for {len(eligible_names)} schemes!"

        # Multi-intent parsing
        reply_en = ""
        reply_hi = ""
        reply_te = ""
        suggested_actions = []

        if "hello" in msg_lower or "hi" in msg_lower or "namaste" in msg_lower:
            reply_en = f"Namaste! I am your AI Government Welfare Eligibility Assistant. {profile_context} How can I assist you with scheme eligibility, required documents, or application tracking today?"
            reply_hi = f"नमस्ते! मैं आपका एआई सरकारी कल्याण पात्रता सहायक हूं। {profile_context} आज मैं योजनाओं की पात्रता, आवश्यक दस्तावेजों या आवेदन स्थिति में आपकी कैसे सहायता कर सकता हूं?"
            reply_te = f"నమస్కారం! నేను మీ AI ప్రభుత్వ సంక్షేమ అర్హత అసిస్టెంట్‌ని. {profile_context} ఈ రోజు పథకం అర్హత, అవసరమైన పత్రాలు లేదా దరఖాస్తు ట్రాకింగ్‌లో నేను మీకు ఎలా సహాయం చేయగలను?"
            suggested_actions = ["Check My Schemes", "Required Documents", "PM-Kisan Scheme Details", "Track Application Status"]

        elif "kisan" in msg_lower or "farmer" in msg_lower or "agriculture" in msg_lower:
            reply_en = "🌾 **PM-Kisan Samman Nidhi Scheme**:\n- **Benefit**: ₹6,000 per year in 3 installments of ₹2,000 directly to landholding farmers.\n- **Eligibility**: Farmers with annual income under ₹3 Lakh.\n- **Documents Required**: Aadhaar Card, Land Record (Khatauni), Bank Passbook, Residence Certificate."
            reply_hi = "🌾 **पीएम-किसान सम्मान निधि योजना**:\n- **लाभ**: ₹6,000 प्रति वर्ष 3 किस्तों में किसानों के बैंक खाते में direct.\n- **पात्रता**: ₹3 लाख से कम वार्षिक आय वाले किसान।\n- **आवश्यक दस्तावेज**: आधार कार्ड, भूमि रिकॉर्ड (खतौनी), बैंक पासबुक, निवास प्रमाण पत्र।"
            reply_te = "🌾 **PM-కిసాన్ సమ్మాన్ నిధి పథకం**:\n- **ప్రయోజనం**: రైతుల బ్యాంక్ ఖాతాలకు నేరుగా సంవత్సరానికి ₹6,000 (3 వాయిదాలలో).\n- **అర్హత**: సంవత్సరానికి ₹3 లక్షల లోపు ఆదాయం ఉన్న రైతులు.\n- **అవసరమైన పత్రాలు**: ఆధార్ కార్డ్, భూమి రికార్డు, బ్యాంక్ పాస్‌బుక్, నివాస ధృవీకరణ పత్రం."
            suggested_actions = ["Apply for PM-Kisan", "View Document Checklist", "Check Other Farmer Schemes"]

        elif "document" in msg_lower or "doc" in msg_lower or "aadhaar" in msg_lower or "income cert" in msg_lower:
            reply_en = "📄 **Standard Document Checklist for Government Schemes**:\n1. Aadhaar Card (ID Proof)\n2. Income Certificate (Issued by Revenue Dept / Tehsildar)\n3. Residence / Domicile Certificate\n4. Active Bank Account Passbook linked with Aadhaar\n5. Caste Certificate (if applicable)\n6. BPL Ration Card (for low-income schemes)"
            reply_hi = "📄 **सरकारी योजनाओं के लिए मानक दस्तावेज चेकलिस्ट**:\n1. आधार कार्ड\n2. आय प्रमाण पत्र (तहसीलदार द्वारा जारी)\n3. निवास / मूल निवासी प्रमाण पत्र\n4. आधार से लिंक बैंक पासबुक\n5. जाति प्रमाण पत्र (यदि लागू हो)\n6. बीपीएल राशन कार्ड"
            reply_te = "📄 **ప్రభుత్వ పథకాలకు ప్రామాణిక పత్రాల జాబితా**:\n1. ఆధార్ కార్డ్\n2. రాబడి/ఆదాయ ధృవీకరణ పత్రం\n3. నివాస ధృవీకరణ పత్రం\n4. ఆధార్‌తో లింక్ చేయబడిన బ్యాంక్ పాస్‌బుక్\n5. కుల ధృవీకరణ పత్రం\n6. BPL రేషన్ కార్డ్"
            suggested_actions = ["View My Document Portal", "Upload Documents", "Check Verification Status"]

        elif "health" in msg_lower or "ayushman" in msg_lower or "hospital" in msg_lower:
            reply_en = "🏥 **Ayushman Bharat (PM-JAY)**:\n- **Benefit**: Cashless treatment up to ₹5,000,000 per family per year in empanelled hospitals.\n- **Eligibility**: BPL households & low-income families (income under ₹2.5 Lakh).\n- **Documents Needed**: Aadhaar Card, BPL Ration Card, Income Certificate."
            reply_hi = "🏥 **आयुष्मान भारत (PM-JAY)**:\n- **लाभ**: संबद्ध अस्पतालों में प्रति वर्ष प्रति परिवार ₹5,00,000 तक का मुफ्त इलाज।\n- **पात्रता**: बीपीएल परिवार और कम आय वाले परिवार।\n- **आवश्यक दस्तावेज**: आधार कार्ड, राशन कार्ड, आय प्रमाण पत्र।"
            reply_te = "🏥 **ఆయుష్మాన్ భారత్ (PM-JAY)**:\n- **ప్రయోజనం**: రూ. 5,00,000 వరకు ఉచిత ఆసుపత్రి చికిత్స.\n- **అర్హత**: BPL మరియు తక్కువ ఆదాయ కుటుంబాలు.\n- **పత్రాలు**: ఆధార్ కార్డ్, BPL రేషన్ కార్డ్, ఆదాయ ధృవీకరణ పత్రం."
            suggested_actions = ["Apply Ayushman Bharat", "Check Eligibility"]

        elif "housing" in msg_lower or "awas" in msg_lower or "house" in msg_lower:
            reply_en = "🏠 **Pradhan Mantri Awas Yojana (PMAY)**:\n- **Benefit**: Financial grant up to ₹1,30,000 for home construction + interest subsidy on home loans.\n- **Eligibility**: Families without a pucca house with annual income under ₹3 Lakh.\n- **Documents**: Aadhaar, Land Property Papers, Bank Passbook, Photo."
            reply_hi = "🏠 **प्रधानमंत्री आवास योजना (PMAY)**:\n- **लाभ**: मकान निर्माण हेतु ₹1,30,000 तक की वित्तीय सहायता।\n- **पात्रता**: बिना पक्के मकान वाले परिवार, आय ₹3 लाख से कम।"
            reply_te = "🏠 **ప్రధాన మంత్రి ఆవాస్ యోజన (PMAY)**:\n- **ప్రయోజనం**: ఇల్లు కట్టుకోవడానికి రూ. 1,30,000 వరకు ఆర్థిక సాయం.\n- **అర్హత**: పక్కా ఇల్లు లేని కుటుంబాలు."
            suggested_actions = ["Check PMAY Status", "Required Documents"]

        elif "track" in msg_lower or "status" in msg_lower or "application" in msg_lower:
            reply_en = "📊 **Application Tracker**:\nYou can track all your submitted welfare scheme applications live in the **Application Tracker** tab! Current statuses include:\n- *Applied* ➔ *Under Verification* ➔ *Approved* ➔ *Benefits Received*."
            reply_hi = "📊 **आवेदन ट्रैकर**:\nआप अपने सभी जमा किए गए आवेदनों को **एप्लिकेशन ट्रैकर** टैब में लाइव ट्रैक कर सकते हैं!"
            reply_te = "📊 **దరఖాస్తు ట్రాకర్**:\nమీరు సబ్‌మిట్ చేసిన అప్లికేషన్‌ల స్థితిని **అప్లికేషన్ ట్రాకర్** ద్వారా లైవ్‌లో ట్రాక్ చేయవచ్చు!"
            suggested_actions = ["Go to Application Tracker", "Check My Schemes"]

        else:
            reply_en = f"I am your AI Welfare Assistant. I can help analyze your eligibility for {len(schemes)}+ national & state welfare schemes, guide document submission, and explain eligibility requirements. Try asking: 'Am I eligible for PM Kisan?' or 'What documents are required for health insurance?'"
            reply_hi = f"मैं आपका AI कल्याण सहायक हूं। मैं {len(schemes)}+ राष्ट्रीय योजनाओं के लिए आपकी पात्रता का विश्लेषण करने में सहायता कर सकता हूं।"
            reply_te = f"నేను మీ AI సంక్షేమ సహాయకుడిని. {len(schemes)}+ ప్రభుత్వ పథకాలలో మీ అర్హతను విశ్లేషించడంలో నేను సహాయపడగలను."
            suggested_actions = ["Evaluate My Eligibility", "View All Schemes", "Contact Support"]

        # Return correct language version
        final_text = reply_en
        if language == "hi":
            final_text = reply_hi
        elif language == "te":
            final_text = reply_te

        return {
            "response": final_text,
            "suggested_actions": suggested_actions,
            "language": language
        }
