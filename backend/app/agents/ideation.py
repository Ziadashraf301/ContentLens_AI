from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class IdeationAgent:
    def __init__(self):
        # Use the summarizer model as a general creative model by default
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=getattr(settings, "OLLAMA_MODEL_IDEATION", settings.OLLAMA_MODEL_SUMMARIZER)
        )

        self.template = """
        SYSTEM:
        You are a creative marketing strategist and copy lead. Given a brief or extracted document, produce a prioritized list of campaign ideas and short execution notes.

        FORMAT:
        - 5 campaign ideas (short title + 1-sentence rationale) in a numbered list.
        - For each idea include 2 quick execution bullets.

        BRIEF / SOURCE:
        {content}

        IDEAS:
        """

        self.prompt = PromptTemplate(
            input_variables=["content"],
            template=self.template
        )

    def run(self, content: str):
        try:
            logger.info("Agent: Ideation generating campaign ideas...")
            chain = self.prompt | self.llm
            return chain.invoke({"content": content})
        except Exception as e:
            logger.error(f"Ideation Error: {e}")
            return "Ideation failed."