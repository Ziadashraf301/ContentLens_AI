from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
import structlog
logger = structlog.get_logger(__name__)
from ..core.langfuse import trace_agent_execution

class SummarizerAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_SUMMARIZER,
            temperature=settings.TEMPERATURE_SUMMARIZER,
            num_predict=512,
            num_ctx=2072,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a senior Media Strategist with strong experience translating marketing briefs into executive-ready insights.
            TASK:
            Summarize the extracted brief data into a sharp, high-impact executive summary.
            Your audience is a very busy Creative Director who needs to grasp the idea in under 30 seconds.
            OUTPUT RULES:
            - Be concise, strategic, and insight-driven.
            - Avoid fluff, repetition, or generic marketing language.
            - Do NOT invent information that is not present in the extracted data.
            - If information is missing, infer cautiously or state it as a constraint.
            - Use clear, confident language suitable for leadership.
            FORMAT (STRICT):
            1. **Big Idea**: One compelling sentence that captures the core strategic idea.
            2. **Execution**:
            - Bullet 1: Primary creative direction
            - Bullet 2: Key channel(s) and content approach
            - Bullet 3: Core CTA or performance driver
            3. **Critical Deadline / Constraint**: One sentence covering the most important timing, budget, or limitation.
            """),
            ("human", "EXTRACTED DATA:\n{extraction_data}\n\nEXECUTIVE SUMMARY:")
        ])

    @trace_agent_execution("summary", settings.OLLAMA_MODEL_SUMMARIZER)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, extraction_data: dict):
        async with ollama_gpu_limit:
            logger.info("Agent: Summarizer condensing data...")
            content_str = str(extraction_data)
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"extraction_data": content_str})
            return response