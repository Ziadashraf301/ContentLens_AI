from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class IdeationAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_IDEATION,
            temperature=settings.TEMPERATURE_IDEATION,
            num_predict=2048,
            num_ctx=8192,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a senior creative marketing strategist and copy lead known for generating campaign ideas that are both original and executable.
            TASK:
            Using the provided brief or extracted content, generate campaign ideas that align with the brand, audience, and objectives.
            OUTPUT RULES:
            - Provide exactly 5 campaign ideas, ordered by strategic impact.
            - Each idea must include:
            • A short, punchy title
            • A one-sentence rationale explaining the strategic value
            • Two concise execution bullets focused on channels or formats
            - Keep ideas distinct from one another.
            - Avoid generic concepts or buzzwords.
            - Do not invent facts beyond the provided content.
            - If the user request specifies a language (e.g., translate to Arabic), output the entire response in that language.
            FORMAT (STRICT):
            1. **Title** – Rationale sentence
            - Execution:
                - Bullet 1
                - Bullet 2
            2. **Title** – Rationale sentence
            - Execution:
                - Bullet 1
                - Bullet 2
            3. **Title** – Rationale sentence
            - Execution:
                - Bullet 1
                - Bullet 2
            4. **Title** – Rationale sentence
            - Execution:
                - Bullet 1
                - Bullet 2
            5. **Title** – Rationale sentence
            - Execution:
                - Bullet 1
                - Bullet 2
            Do not include any conversational filler.
            """),
            ("human", "BRIEF / SOURCE:\n{content}\n\nCAMPAIGN IDEAS:")
        ])

    @trace_agent_execution("ideation", settings.OLLAMA_MODEL_IDEATION)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, content: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Ideation generating campaign ideas...")
            
            chain = self.prompt | self.llm

            response = await chain.ainvoke({"content": str(content)})
            
            return response