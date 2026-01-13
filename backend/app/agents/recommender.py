from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger


class RecommenderAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_RECOMMENDER,
            temperature=0.3,
        )

        self.template = """
        SYSTEM:
        You are a Senior Strategist. Given the brief or extracted information, provide concise, actionable recommendations.

        INSTRUCTIONS:
        - Provide 3 prioritized recommendations.
        - Each recommendation should include a short reason and an actionable next step.
        - Keep output as plain text or short JSON-like bullet points.

        INPUT_CONTENT:
        {content}
        """

        self.prompt = PromptTemplate(input_variables=["content"], template=self.template)

    def run(self, content: str):
        try:
            logger.info("Agent: Recommender generating recommendations...")
            chain = self.prompt | self.llm
            return chain.invoke({"content": str(content)})
        except Exception as e:
            logger.error(f"Recommender Error: {e}")
            return "Recommendation generation failed."
