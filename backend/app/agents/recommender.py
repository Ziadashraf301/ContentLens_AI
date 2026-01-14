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
        You are a Senior Media & Growth Strategist advising creative and marketing teams.

        TASK:
        Based on the provided brief or extracted information, generate clear, high-impact recommendations that can be executed immediately.

        OUTPUT RULES:
        - Provide exactly 3 recommendations, ordered by priority (1 = highest impact).
        - Each recommendation must include:
        - Recommendation: one concise action
        - Rationale: one short reason tied to the brief
        - Next Step: one concrete, executable action
        - Be specific and practical; avoid generic advice.
        - Do NOT invent facts not present in the input.
        - If key information is missing, state an assumption briefly.

        FORMAT (STRICT):
        1. Recommendation:
        - Rationale:
        - Next Step:
        2. Recommendation:
        - Rationale:
        - Next Step:
        3. Recommendation:
        - Rationale:
        - Next Step:

        INPUT_CONTENT:
        {content}

        RECOMMENDATIONS:
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
