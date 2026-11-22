"""
Gemini AI Service Wrapper.
Integrates with Google GenAI SDK to provide:
1. Structured Lead Intelligence Extraction (Summary, Intent, Requirements, Objections, Next Action, Suggested Response)
2. Grounded Sales Copilot Q&A (Supporting English & Conversational Hinglish)
3. Follow-Up Assistant Copy Generator (WhatsApp / SMS)
4. Follow-Up Hub Pipeline Assistant Chat
With multi-model resilient fallback across gemini-3.8-flash, gemini-3.5-flash, gemini-3.1-flash-lite, etc.
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("GeminiService")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Common Hinglish detector
def is_hinglish(text: str) -> bool:
    if not text:
        return False
    if re.search(r'[\u0900-\u097F]', text):
        return True
    hinglish_tokens = [
        r'\bke\b', r'\bki\b', r'\bka\b', r'\bko\b', r'\bmein\b', r'\bse\b', r'\bpe\b', r'\bpar\b',
        r'\bmai\b', r'\bmain\b', r'\bmujhe\b', r'\bmera\b', r'\bmeri\b', r'\bmere\b', r'\bhum\b', r'\bhamara\b',
        r'\bbatao\b', r'\bbataiye\b', r'\bbata\b', r'\bbtao\b',
        r'\bkya\b', r'\bky\b', r'\bkyaa\b', r'\bkyun\b', r'\bkyu\b', r'\bhai\b', r'\bhain\b', r'\btha\b', r'\bthe\b', r'\bthi\b',
        r'\bkaise\b', r'\bkese\b', r'\bkab\b', r'\bkaha\b', r'\bkahan\b',
        r'\bkaro\b', r'\bkare\b', r'\bkarein\b', r'\bkarna\b', r'\bkaru\b', r'\bkaroon\b', r'\bchahiye\b',
        r'\bye\b', r'\byeh\b', r'\bwo\b', r'\bwoh\b',
        r'\biska\b', r'\biski\b', r'\biske\b', r'\bunka\b', r'\bunki\b', r'\bunke\b', r'\binke\b', r'\binka\b',
        r'\busko\b', r'\bisko\b', r'\bunko\b',
        r'\bbolo\b', r'\bbolna\b', r'\bbolu\b', r'\bbole\b', r'\bboliye\b', r'\babolu\b',
        r'\bbhej\b', r'\bbhejo\b', r'\bkitna\b', r'\bkitne\b', r'\bkitni\b',
        r'\baccha\b', r'\bachha\b', r'\btheek\b', r'\bsamjhao\b', r'\bkuch\b', r'\bkaisa\b', r'\bkaisi\b',
        r'\bnahi\b', r'\bnhi\b', r'\bhaan\b', r'\bdikkat\b', r'\bpaise\b', r'\brupaye\b', r'\bbaat\b',
        r'\btoh\b', r'\bbhi\b', r'\bhoga\b', r'\bhogi\b', r'\bhoge\b'
    ]
    pattern = '|'.join(hinglish_tokens)
    return bool(re.search(pattern, text, re.IGNORECASE))

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self.candidate_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]
        self.active_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini Service initialized. Preferred model: {self.active_model}")
            except Exception as e:
                logger.warning(f"Warning initializing Gemini client: {e}")
                self.client = None
        else:
            logger.info("Notice: GEMINI_API_KEY not set. Running in deterministic heuristic fallback mode.")

    def is_connected(self) -> bool:
        return self.client is not None

    def _call_gemini(self, prompt: str, is_json: bool = False) -> Optional[str]:
        """Tries candidate models in order to handle temporary spikes or version shifts."""
        if not self.client:
            return None

        models_to_try = [self.active_model] + [m for m in self.candidate_models if m != self.active_model]
        for m in models_to_try:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(response_mime_type="application/json") if is_json else None
                resp = self.client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config
                )
                if resp and resp.text:
                    self.active_model = m
                    return resp.text.strip()
            except Exception as e:
                logger.debug(f"Model {m} failed: {e}. Trying next candidate...")
                continue
        return None

    def extract_lead_intelligence(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses Gemini to extract structured JSON intelligence from inquiry message.
        """
        name = lead_dict.get("name", "Customer")
        loc = lead_dict.get("location", "Bangalore")
        req = lead_dict.get("property_requirement", "2BHK / 3BHK")
        budget = lead_dict.get("budget", "Unspecified")
        timeline = lead_dict.get("timeline", "Not decided")
        msg = lead_dict.get("message", "")

        prompt = f"""
You are an expert Real Estate Sales AI for Bangalore properties.
Analyze this inbound lead:
Customer: {name}
Location: {loc}
Requirement: {req}
Budget: INR {budget}
Timeline: {timeline}
Inquiry Message: "{msg}"

Return a strict JSON object with these exact keys:
{{
  "summary": "1-2 sentence executive summary of customer profile and intent",
  "intent": "analysis of buyer urgency and emotional/commercial drivers",
  "requirements": "concise extracted property specifications",
  "objections": ["list", "of", "potential", "risks", "or", "blockers"],
  "next_action": "specific immediate recommended operational action for sales agent",
  "suggested_response": "concise 2-sentence professional WhatsApp/Email reply addressing their exact requirements"
}}
"""
        raw_json = self._call_gemini(prompt, is_json=True)
        if raw_json:
            try:
                parsed = json.loads(raw_json)
                return parsed
            except Exception as e:
                logger.warning(f"Error parsing Gemini JSON: {e}")

        # Heuristic fallback if Gemini API is offline or quota exceeded
        is_urgent = any(k in str(timeline).lower() or k in str(msg).lower() for k in ["1 month", "urgent", "relocat", "immediate", "ready to move"])
        first_name = name.split()[0]
        return {
            "summary": f"{name} is inquiring for a {req} in {loc} with a budget of ₹{budget}.",
            "intent": "Extremely high buying intent driven by immediate timeline." if is_urgent else "Exploratory property search and price discovery.",
            "requirements": f"{req}, {loc}, Budget: ₹{budget}, Timeline: {timeline}.",
            "objections": ["Needs verified RERA & OC status before committing"] if is_urgent else ["Needs detailed cost sheet with registration charges breakdown"],
            "next_action": f"Call within 15 minutes to confirm weekend site visit" if is_urgent else f"Send digital brochure and schedule consultative call in 48 hours",
            "suggested_response": f"Hi {first_name}, welcome to our verified projects in {loc}! We have units matching your exact {req} criteria within your ₹{budget} budget. Can we schedule a brief walkthrough this Saturday at 11 AM?"
        }

    def regenerate_suggested_reply(self, lead_dict: Dict[str, Any], current_reply: str = "", tone: str = "", variation: int = 1) -> str:
        """
        Regenerate a distinct, high-converting alternative suggested reply for customer WhatsApp / Email.
        Adapts to English or Hinglish based on the lead's inquiry message.
        """
        name = lead_dict.get("name", "Customer")
        first_name = name.split()[0]
        loc = lead_dict.get("location", "Bangalore")
        req = lead_dict.get("property_requirement", "property")
        budget = lead_dict.get("budget", "your budget")
        timeline = lead_dict.get("timeline", "soon")
        msg = lead_dict.get("message", "")
        lead_is_hinglish = is_hinglish(msg) or is_hinglish(current_reply)

        angles = [
            "Direct site visit / walkthrough confirmation with immediate scheduled time",
            "Value & verified inventory focus (exclusive units matching budget, clear RERA/OC)",
            "Subtle qualification & consultative check on unit preferences or down payment readiness",
            "Urgency & high-demand momentum (ready-to-move units moving quickly before weekend)",
            "Concise, relationship-building personal welcome with soft call to action"
        ]
        chosen_angle = angles[(variation - 1) % len(angles)]

        lang_instruction = "Respond ENTIRELY in natural, conversational Hinglish (Latin script)." if lead_is_hinglish else "Respond ENTIRELY in professional, concise English."

        prompt = f"""
You are an expert Real Estate Sales AI for premium properties in Bangalore.
The sales agent was not satisfied with the previous suggested reply and requested a REGENERATED, FRESH alternative.

Lead Information:
- Customer Name: {name}
- Location: {loc}
- Property Requirement: {req}
- Stated Budget: ₹{budget}
- Timeline: {timeline}
- Inbound Inquiry: "{msg}"

Previous rejected response:
"{current_reply}"

Target Approach: {chosen_angle}
{lang_instruction}

Requirements:
1. Write a 2 to 3 sentence natural, highly persuasive WhatsApp/Email message.
2. Address the customer by first name ({first_name}).
3. Reference their exact requirement ({req}) and location ({loc}).
4. Do NOT use identical phrasing to the previous rejected response.
5. Keep it concise, professional, and easy to read. Output ONLY the message text without quotes, headings, or meta comments.
"""
        reply = self._call_gemini(prompt)
        if reply:
            return reply.strip().strip('"').strip("'")

        return self._fallback_regenerated_reply(lead_dict, variation, lead_is_hinglish, current_reply)

    def _fallback_regenerated_reply(self, lead_dict: Dict[str, Any], variation: int, is_hinglish_lead: bool, current_reply: str = "") -> str:
        first_name = lead_dict.get("name", "Customer").split()[0]
        loc = lead_dict.get("location", "Bangalore")
        req = lead_dict.get("property_requirement", "property")
        budget = lead_dict.get("budget", "your budget")
        timeline = lead_dict.get("timeline", "soon")

        if is_hinglish_lead:
            options = [
                f"Hi {first_name}, {loc} mein aapki requirement ke mutabiq {req} ki prime ready units shortlist ki hain. Kya hum iss Saturday 11:30 AM site visit plan karein? Main convenience ke hisaab se timing fix kar deta hoon.",
                f"Hi {first_name}! {budget} ke budget mein {loc} ke 2 best verified ready-to-move projects available hain jinka OC aur clear title ready hai. Aapko detailed cost sheet aur floor plans WhatsApp kar doon?",
                f"Hi {first_name}, thank you for reaching out! {req} mein specific facing ya floor preference hai? Aaj evening 5 baje 5-minute quick call par connect karein taaki exact inventory options share kar sakun?",
                f"Hi {first_name}, {loc} mein iss budget aur configuration ki premium units tezi se book ho rahi hain. Weekend ke pehle shortlist lock kar lete hain—kal afternoon aapke paas 10 minute ka waqt hoga baat karne ke liye?",
                f"Hi {first_name}, Bangalore property search mein swagat hai! {req} ke verified options ready hain jo aapke {timeline} timeline se perfectly align hote hain. Batayein kab call schedule karein?"
            ]
        else:
            options = [
                f"Hi {first_name}, I have identified 2 ready-to-move {req} options in {loc} that match your exact criteria. Could we schedule a walkthrough this Saturday morning to view the actual units?",
                f"Hi {first_name}, thank you for reaching out! We have premium RERA-verified units in {loc} that fit comfortably within your ₹{budget} budget with complete OC ready. May I share the verified cost sheets and floor plans over WhatsApp?",
                f"Hi {first_name}, to ensure we only share the most relevant {req} units in {loc}, do you have specific preferences regarding floor or facing? Let me know a convenient 5-minute window today to align.",
                f"Hi {first_name}, verified inventory for {req} in {loc} is moving rapidly this month. I would like to block the top 2 units for you before the weekend rush—would a brief 10-minute call today at 4 PM work?",
                f"Hi {first_name}, welcome to our verified property network in {loc}! I have handpicked options tailored to your {timeline} move-in plan and ₹{budget} budget. Let me know when you would like to connect."
            ]

        candidates = [opt for opt in options if opt.strip() != current_reply.strip()]
        return candidates[(variation - 1) % len(candidates)] if candidates else options[0]

    def chat_with_copilot(self, lead_dict: Dict[str, Any], query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Grounded sales Q&A assistant for a specific lead.
        Seamlessly handles both English and conversational Hinglish.
        """
        user_is_hinglish = is_hinglish(query)
        lead_name = lead_dict.get("name", "Customer")
        loc = lead_dict.get("location", "Bangalore")
        req = lead_dict.get("property_requirement", "Property")
        budget = lead_dict.get("budget", "Open")
        timeline = lead_dict.get("timeline", "Not decided")
        score = lead_dict.get("score", 70)
        priority = lead_dict.get("priority", "Warm")
        ai_info = lead_dict.get("ai_analysis", {})

        if user_is_hinglish:
            lang_and_style_rules = """
MANDATORY LANGUAGE ENFORCEMENT:
The user asked their question in Hinglish (Hindi written in Roman English alphabet).
YOU MUST RESPOND 100% ENTIRELY IN NATURAL ROMAN HINGLISH.
DO NOT MIX LANGUAGES UNNECESSARILY. MAINTAIN HINGLISH THROUGHOUT THE ENTIRE RESPONSE.
- Every single heading, bullet point, explanation, advice, and customer dialogue/pitch MUST be in Roman Hinglish.
- ABSOLUTELY ZERO English sentences, quotes, or explanations. Do NOT switch to English for explanations or bullet points.
  DO NOT write: "* **Legal Transparency:** Assure him that all units are OC-verified."
  INSTEAD write: "• **Legal Documents:** Unko confirm karein ki OC aur RERA papers bilkul clear hain."
- If providing a script or pitch: Provide ONLY ONE concise script (1-2 sentences max) in natural Roman Hinglish.
- Use 2-3 short, clean bullet points in Hinglish for key talking points.
- Keep response ultra-short, crisp, and professional (under 65 words total).
- NO lengthy paragraphs, NO filler introductions (do NOT say "Aman ek hot lead hai...", "Yeh message bhejo:", etc.).
"""
        else:
            lang_and_style_rules = """
MANDATORY LANGUAGE ENFORCEMENT:
The user asked their question in English.
YOU MUST RESPOND 100% ENTIRELY IN PROFESSIONAL ENGLISH.
DO NOT MIX LANGUAGES UNNECESSARILY. MAINTAIN ENGLISH THROUGHOUT THE ENTIRE RESPONSE.
- Every single heading, bullet point, explanation, advice, and customer dialogue/pitch MUST be in English.
- ABSOLUTELY ZERO Hindi or Hinglish words.
- If providing a script or pitch: Provide ONLY ONE concise script (1-2 sentences max) in English.
- Use 2-3 short, clean bullet points in English for key talking points.
- Keep response ultra-short, crisp, and professional (under 65 words total).
- NO lengthy paragraphs, NO unnecessary explanations or filler introductions.
"""

        prompt = f"""
You are the Lead Manager Real Estate Sales Copilot advising a sales agent:
Lead: {lead_name} ({priority} · {score}/100)
Need: {req} in {loc} | Budget: INR {budget} | Timeline: {timeline}
Inquiry: "{lead_dict.get('message', '')}"
Key Objection: {ai_info.get('objections', ['None'])[0] if ai_info.get('objections') else 'None'}
Next Action: {ai_info.get('next_action', 'Contact lead')}

User Question: "{query}"

{lang_and_style_rules}
"""
        response_text = self._call_gemini(prompt)
        if response_text:
            return response_text

        # Grounded Heuristic Response (Offline / Fallback)
        q = query.lower()
        first_name = lead_name.split()[0]
        if user_is_hinglish:
            if any(k in q for k in ["pitch", "call", "baat", "bol", "emphasize", "kya", "abolu", "bolu"]):
                return f"🗣️ **Call Script:**\n" \
                       f"\"Namaste {first_name} ji! {loc} mein aapke ₹{budget} budget ke mutabiq verified {req} ready units shortlist kiye hain. Kya hum Saturday ko site visit confirm karein?\"\n\n" \
                       f"📋 **Key Points:**\n" \
                       f"• **Inventory Fit**: {loc} mein matched {req} units highlight karein.\n" \
                       f"• **Budget**: ₹{budget} transparent pricing confirm karein.\n" \
                       f"• **Goal**: Weekend site visit slot lock karein."
            if any(k in q for k in ["objection", "dikkat", "problem", "concern"]):
                objs = ai_info.get("objections", ["Verified documentation"])
                return f"**{lead_name}** ke main concerns:\n• **{' • '.join(objs)}**\n\nCall par pehle verified RERA/OC proof share karein."
            if any(k in q for k in ["budget", "paise", "price"]):
                return f"• **Budget**: ₹{budget}\n• **Status**: {loc} mein {req} ke sath budget matched hai."
            return f"**{lead_name}** ({priority} Lead · {score}/100):\n" \
                   f"• **Need**: {loc} mein {req}\n" \
                   f"• **Budget**: ₹{budget} | **Timeline**: {timeline}\n" \
                   f"• **Next Action**: {ai_info.get('next_action', 'Call and confirm site visit')}"
        else:
            if any(k in q for k in ["call", "pitch", "emphasize", "say", "speak"]):
                return f"🗣️ **Call Script:**\n" \
                       f"\"Hi {first_name}, I've shortlisted verified ready-to-move {req} units in {loc} matching your ₹{budget} budget. Can we confirm a walkthrough this Saturday?\"\n\n" \
                       f"📋 **Key Points:**\n" \
                       f"• Highlight verified {req} inventory in {loc}.\n" \
                       f"• Confirm ₹{budget} budget alignment.\n" \
                       f"• Secure Saturday site visit commitment."
            if any(k in q for k in ["objection", "concern"]):
                objs = ai_info.get("objections", ["Price and possession timeline"])
                return f"Active concerns:\n• **{' • '.join(objs)}**\n\nStrategy: Present verified OC & RERA documents early on the call."
            return f"**{lead_name}** ({priority} · {score}/100):\n" \
                   f"• **Need**: {req} in {loc}\n" \
                   f"• **Budget**: ₹{budget} | **Timeline**: {timeline}\n" \
                   f"• **Action**: {ai_info.get('next_action', 'Contact immediately')}"

    def generate_followup_copy(self, lead_dict: Dict[str, Any], channel: str = "whatsapp") -> str:
        """
        Generates personalized follow-up message copy.
        """
        first_name = lead_dict.get("name", "Customer").split()[0]
        loc = lead_dict.get("location", "Bangalore")
        req = lead_dict.get("property_requirement", "property")
        budget = lead_dict.get("budget", "your budget")

        prompt = f"Draft a concise, 2-sentence WhatsApp follow-up for real estate lead {lead_dict.get('name')} looking for {req} in {loc} under INR {budget}. Professional, natural, non-pushy."
        resp = self._call_gemini(prompt)
        if resp:
            return resp.replace('"', '').strip()

        return f"Hi {first_name}, following up on your inquiry for {req} in {loc}. We have verified units matching your ₹{budget} budget with clear OC ready. Would you be free for a 15-min walkthrough this Saturday?"

    def chat_with_followup_hub(self, query: str, due_leads: List[Dict[str, Any]]) -> str:
        """
        AI assistant for the Follow-Up Hub pipeline.
        """
        user_is_hinglish = is_hinglish(query)
        if user_is_hinglish:
            lang_style = """
MANDATORY LANGUAGE ENFORCEMENT:
The user asked in Hinglish.
YOU MUST RESPOND 100% ENTIRELY IN NATURAL ROMAN HINGLISH.
DO NOT MIX LANGUAGES.
- Every heading, bullet point, and explanation MUST be in Roman Hinglish.
- ABSOLUTELY ZERO English sentences or explanations.
- Keep response ultra-short, clear, and professional (under 65 words).
- Use 2-3 concise bullet points in Hinglish.
"""
        else:
            lang_style = """
MANDATORY LANGUAGE ENFORCEMENT:
The user asked in English.
YOU MUST RESPOND 100% ENTIRELY IN PROFESSIONAL ENGLISH.
DO NOT MIX LANGUAGES.
- Every heading, bullet point, and explanation MUST be in English.
- ABSOLUTELY ZERO Hindi or Hinglish words.
- Keep response ultra-short, clear, and professional (under 65 words).
- Use 2-3 concise bullet points in English.
"""

        prompt = f"""
You are the Real Estate Follow-Up Hub Assistant.
Active Due Leads ({len(due_leads)} total):
{json.dumps([{'name': l.get('name'), 'priority': l.get('priority'), 'goal': l.get('followup', {}).get('goal')} for l in due_leads[:6]], indent=2)}

Agent's Question: "{query}"

{lang_style}
"""
        resp = self._call_gemini(prompt)
        if resp:
            return resp

        count = len(due_leads)
        list_str = "\n".join([f"• **{l.get('name')}** ({l.get('priority')}): {l.get('followup', {}).get('goal', 'Follow-up')}" for l in due_leads[:4]])
        if user_is_hinglish:
            return f"Aaj total **{count} leads** ke follow-ups due hain:\n\n{list_str}\n\n• **Immediate Action**: Hot leads ko pehle call karein."
        else:
            return f"**{count} follow-up actions due today**:\n\n{list_str}\n\n• **Action**: Prioritize Hot leads within 24h."

gemini_service = GeminiService()
