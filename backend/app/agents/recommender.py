
from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class RecommenderAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_RECOMMENDER,
            temperature=settings.TEMPERATURE_RECOMMENDER,
            num_predict=2048,
            num_ctx=8192,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a Senior Media & Growth Strategist advising creative and marketing teams.
            TASK:
            Based on the provided brief or extracted information and user request, generate clear, high-impact recommendations that can be executed immediately.
            OUTPUT RULES:
            - Provide exactly 3 recommendations, ordered by priority (1 = highest impact).
            - Each recommendation must include:
            - Recommendation: one concise action
            - Rationale: one short reason tied to the brief
            - Next Step: one concrete, executable action
            - Be specific and practical; avoid generic advice.
            - Do NOT invent facts not present in the input.
            - If key information is missing, state an assumption briefly.
            - If the user request specifies a language (e.g., translate to Arabic), output the entire response in that language.
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
            """),
            ("human", "INPUT_CONTENT:\n{content}\n\nUSER REQUEST:\n{user_request}\n\nRECOMMENDATIONS:")
        ])

    @trace_agent_execution("recommendation", settings.OLLAMA_MODEL_RECOMMENDER)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, content: str, user_request: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Recommender generating recommendations...")
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"content": str(content), "user_request": user_request})
            return response
