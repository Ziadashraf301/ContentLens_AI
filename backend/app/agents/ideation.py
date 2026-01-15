from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class IdeationAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_IDEATION,
            temperature=settings.TEMPERATURE_IDEATION
        )

        self.template = """
        SYSTEM:
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

        BRIEF / SOURCE:
        {content}

        CAMPAIGN IDEAS:
        """

        self.prompt = PromptTemplate(
            input_variables=["content"],
            template=self.template
        )

    @trace_agent_execution("ideation", settings.OLLAMA_MODEL_IDEATION)
    def run(self, content: str):
        try:
            logger.info("Agent: Ideation generating campaign ideas...")
            chain = self.prompt | self.llm
            return chain.invoke({"content": content})
        except Exception as e:
            logger.error(f"Ideation Error: {e}")
            return "Ideation failed."