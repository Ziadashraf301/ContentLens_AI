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
        You are a senior marketing copywriter. Given a content brief produce multiple copy variants in the requested tone.

        FORMAT:
        - Provide 3 subject line variants (for email).
        - Provide 3 short body variants (1-2 sentences) for testing.
        - Provide one CTA (short) for each variant.

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