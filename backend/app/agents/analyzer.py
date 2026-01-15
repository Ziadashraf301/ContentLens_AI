from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class AnalyzerAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ANALYZER,
            temperature=settings.TEMPERATURE_ANALYZER
        )
        
        self.template = """
        SYSTEM:
        You are a Senior Media Planner with strong experience reviewing briefs for strategic readiness and execution risk.

        TASK:
        Analyze the provided advertising brief and assess its completeness, strategic soundness, and potential risks.

        OUTPUT RULES:
        - Base your analysis strictly on the provided content.
        - Do not assume missing details; explicitly flag them.
        - Keep insights concise, practical, and decision-oriented.

        FORMAT (STRICT):
        1. Missing or Unclear Information:
        - Bullet list of missing, vague, or ambiguous elements.

        2. Strategic Recommendations:
        - Exactly 3 recommendations, ordered by impact.
        - Each recommendation should be concise and actionable.

        3. Potential Risks:
        - Bullet list of key risks that could affect performance or delivery.

        BRIEF DATA:
        {content}

        STRATEGIC ANALYSIS:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["content"],
            template=self.template
        )

    @trace_agent_execution("analysis", settings.OLLAMA_MODEL_ANALYZER)
    def run(self, content: str):
        try:
            logger.info("Agent: Analyzer performing strategic review...")
            chain = self.prompt | self.llm
            return chain.invoke({"content": str(content)})
        except Exception as e:
            logger.error(f"Analyzer Error: {e}")
            return "Strategic analysis failed."