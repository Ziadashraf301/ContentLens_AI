from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class AnalyzerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ANALYZER,
            temperature=settings.TEMPERATURE_ANALYZER,
            num_predict=512,
            num_ctx=2072,
        )
        
        # Using ChatPromptTemplate to separate the Persona from the Data
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an elite Lead Strategic Consultant and Media Auditor. 
            Your expertise lies in identifying structural gaps in advertising briefs and mitigating execution risks before they reach the market.

            OUTPUT RULES:
            - Base your analysis strictly on the provided content.
            - Do not assume missing details; explicitly flag them.
            - Keep insights concise, practical, and decision-oriented.
            - Do not include any conversational filler or introductory phrases.

            FORMAT (STRICT):
            1. Missing or Unclear Information:
            - Bullet list of missing, vague, or ambiguous elements.

            2. Strategic Recommendations:
            - Exactly 3 recommendations, ordered by impact.
            - Each recommendation should be concise and actionable.
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

            3. Potential Risks:
            - Bullet list of key risks that could affect performance or delivery."""),
            
            ("human", "BRIEF DATA:\n{content}\n\nSTRATEGIC ANALYSIS:")
        ])

    @trace_agent_execution("analysis", settings.OLLAMA_MODEL_ANALYZER)
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, content: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Analyzer performing strategic review...")
                
            # Chain definition
            chain = self.prompt | self.llm
                
            # ChatOllama returns an AIMessage object
            response = await chain.ainvoke({"content": str(content)})
                
            # Return the AI message object directly
            return response