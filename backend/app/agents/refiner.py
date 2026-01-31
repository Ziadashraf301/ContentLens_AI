from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class RefinerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_REFINER,
            temperature=settings.TEMPERATURE_REFINER,
            num_predict=512,
            num_ctx=2072,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a Prompt Refinement AI. Your task is to refine and improve user requests based on extracted document information.
            Make the request more specific, actionable, and aligned with the document content.
            REFINEMENT GOALS:
            - Clarify ambiguous requests
            - Add context from the extracted information
            - Make the request more specific and actionable
            - Ensure the request aligns with available document data
            - Maintain the original intent while improving clarity
            """),
            ("human", "EXTRACTED INFORMATION:\n{extraction}\n\nORIGINAL USER REQUEST:\n{user_request}\n\nREFINED REQUEST:")
        ])

    @trace_agent_execution("refinement", settings.OLLAMA_MODEL_REFINER)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def run(self, extraction: dict, user_request: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Refiner starting work...")
            chain = self.prompt | self.llm
            response = await chain.ainvoke({
                "extraction": str(extraction),
                "user_request": user_request
            })
            
            return response