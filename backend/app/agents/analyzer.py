from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class AnalyzerAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ANALYZER
        )
        
        self.template = """
        SYSTEM:
        You are a Senior Media Planner. Analyze the following advertising brief.
        
        YOUR GOALS:
        1. Identify missing information (Budget? Timeline? Target Audience?).
        2. Suggest 3 strategic recommendations for this campaign.
        3. Identify potential risks (e.g., tight deadline, vague KPIs).

        BRIEF DATA:
        {content}

        STRATEGIC ANALYSIS:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["content"],
            template=self.template
        )

    def run(self, content: str):
        try:
            logger.info("Agent: Analyzer performing strategic review...")
            chain = self.prompt | self.llm
            return chain.invoke({"content": str(content)})
        except Exception as e:
            logger.error(f"Analyzer Error: {e}")
            return "Strategic analysis failed."