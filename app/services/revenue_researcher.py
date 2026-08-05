import json
import re

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError

from app.core.config import Settings
from app.schemas.research import RevenueAnalysisResponse


class RevenueResearchError(Exception):
    """Custom exception raised when revenue research generation fails."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RevenueResearcherService:
    """Service handling LLM interaction via Hugging Face Inference API to analyze revenue streams."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def _get_client(self) -> InferenceClient:
        token = self.settings.hf_token if self.settings.hf_token else None
        return InferenceClient(token=token)

    def _clean_json_output(self, raw_text: str) -> str:
        """Strip markdown code fences and extraneous whitespace from raw LLM output."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def analyze_revenue_streams(
        self, company_name: str, model_id: str | None = None
    ) -> RevenueAnalysisResponse:
        effective_model = model_id or self.settings.default_hf_model
        client = self._get_client()

        system_prompt = (
            "You are an expert financial research analyst. Provide a structured analysis of "
            "the key revenue streams for the specified company.\n"
            "You MUST respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "company_name": "string",\n'
            '  "summary": "string - comprehensive business model summary",\n'
            '  "primary_currency": "string - e.g. USD",\n'
            '  "revenue_streams": [\n'
            "    {\n"
            '      "name": "string - segment or product line name",\n'
            '      "description": "string - how revenue is generated",\n'
            '      "revenue_type": "string - e.g. Product Sales, Subscription, Services",\n'
            '      "estimated_percentage": number_or_null\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Do NOT include explanations, introduction, markdown code blocks, or extra text outside the JSON."
        )

        user_prompt = f"Analyze the revenue streams for company: {company_name}"

        try:
            chat_response = client.chat.completions.create(
                model=effective_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1200,
                temperature=0.2,
                extra_body={"response_format":{"type": "json_object"}},
            )
        except HfHubHTTPError as exc:
            raise RevenueResearchError(
                f"Hugging Face API request failed: {exc!s}", status_code=502
            ) from exc
        except Exception as exc:
            raise RevenueResearchError(
                f"Failed to communicate with LLM provider: {exc!s}", status_code=500
            ) from exc

        if not chat_response.choices or not chat_response.choices[0].message:
            raise RevenueResearchError(
                "Received empty completion response from LLM provider.", status_code=502
            )

        raw_content = chat_response.choices[0].message.content or ""
        cleaned_json = self._clean_json_output(raw_content)

        try:
            data = json.loads(cleaned_json)
        except json.JSONDecodeError as exc:
            raise RevenueResearchError(
                f"LLM output could not be parsed as valid JSON: {cleaned_json}",
                status_code=502,
            ) from exc

        # Override/ensure company_name and model_used fields are populated accurately
        data["company_name"] = company_name
        data["model_used"] = effective_model

        try:
            return RevenueAnalysisResponse.model_validate(data)
        except Exception as exc:
            raise RevenueResearchError(
                f"LLM output JSON failed schema validation: {exc!s}", status_code=502
            ) from exc
