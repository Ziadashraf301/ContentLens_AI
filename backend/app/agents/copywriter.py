from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class CopywriterAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_COPYWRITER
        )

        self.template = """
        SYSTEM:
        You are a senior performance-focused marketing copywriter with experience in email and digital campaign optimization.

        TASK:
        Based on the provided content brief, generate multiple copy variants suitable for A/B testing.

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

        COPY VARIANTS:
        """

        self.prompt = PromptTemplate(
            input_variables=["brief"],
            template=self.template
        )

    def run(self, brief: str):
        try:
            logger.info("Agent: Copywriter creating variants...")
            chain = self.prompt | self.llm
            return chain.invoke({"brief": brief})
        except Exception as e:
            logger.error(f"Copywriter Error: {e}")
            return "Copy generation failed."