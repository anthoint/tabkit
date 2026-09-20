import json

from openai import OpenAI

from backend import config 
from backend.context import Context
from backend.sufficiency.prompts import sufficiency_prompt
from backend.sufficiency.results import SufficiencyResult

class SufficiencyChecker:
    def __init__(self):
        api_key = config.require_openai_api_key()
        self.client = OpenAI(api_key=api_key)
        self.model = config.SUFFICIENCY_OPENAI_MODEL

    def check(self, context: Context, previous_user=None, previous_assistant=None):
        try:
            previous_user_message = previous_user if previous_user else "NONE"
            previous_assistant_message = previous_assistant if previous_assistant else "NONE"
            current_user_message = context.text
            page_title = (context.title or "").strip() or "NONE"

            user_content = (
                f"Current page title: {page_title}\n"
                f"Previous user message: {previous_user_message}\n"
                f"Current user message: {current_user_message}\n"
                f"Previous assistant message: {previous_assistant_message}\n"
            )

            message = [
                {"role": "system", "content": sufficiency_prompt()},
                {"role": "user", "content": user_content},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
            )
            raw_data = response.choices[0].message.content

            new_data = json.loads(raw_data)

            score = int(new_data.get("score", 0))
            if score < 1:
                score = 1
            if score > 10:
                score = 10
            related = bool(new_data.get("related", False))
            if "on_tab" in new_data:
                on_tab = bool(new_data.get("on_tab"))
            else:
                on_tab = True
            rewrite = str(new_data.get("rewrite", "")).strip()
            summary = str(new_data.get("summary", "") or new_data.get("Summary", "")).strip()
            if score >= config.SUFFICIENCY_THRESHOLD:
                rewrite = ""
            elif not rewrite:
                rewrite = current_user_message
            
            return SufficiencyResult(score, related, rewrite, summary, on_tab)
        
        except Exception:
            return SufficiencyResult(0, False, "", "", True)

    