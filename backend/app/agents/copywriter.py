from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class CopywriterAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_COPYWRITER,
            temperature=settings.TEMPERATURE_COPYWRITER
        )

        self.template = """
        SYSTEM:
        You are a senior performance-focused marketing copywriter with experience in email and digital campaign optimization.

        TASK:
        Based on the provided content brief and user request, generate multiple copy variants suitable for A/B testing.

        OUTPUT RULES:
        - Provide exactly 3 copy variants.
        - Each variant must include:
        1) Subject line (email)
        2) Body copy (1–2 concise sentences)
        3) CTA (2–4 words max)
        - Variants should differ meaningfully in angle, not just wording.
        - Match the requested tone and audience from the brief.
        - Avoid clichés and generic marketing language.
        - Do not invent offers, deadlines, or claims not present in the brief.

        FORMAT (STRICT):
        Variant 1:
        - Subject:
        - Body:
        - CTA:

        Variant 2:
        - Subject:
        - Body:
        - CTA:

        Variant 3:
        - Subject:
        - Body:
        - CTA:

        BRIEF:
        {brief}

        USER REQUEST:
        {user_request}

        COPY VARIANTS:
        """

        self.prompt = PromptTemplate(
            input_variables=["brief", "user_request"],
            template=self.template
        )

    
    @trace_agent_execution("copywriter", settings.OLLAMA_MODEL_COPYWRITER)
    def run(self, brief: str, user_request: str):
        try:
            logger.info("Agent: Copywriter creating variants...")
            chain = self.prompt | self.llm
            result = chain.invoke({"brief": brief, "user_request": user_request})
            return result
        except Exception as e:
            logger.error(f"Copywriter Error: {e}")
            return "Copy generation failed."