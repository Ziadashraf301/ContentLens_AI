from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class RouterAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ROUTER
        )
        
        self.template = """
        SYSTEM:
        You are an Intent Classifier for a Media AI system. 
        Your job is to read a User Request and decide which agent should handle it next.

        OPTIONS:
        1. 'summarize': Use if the user wants a shorter version, a summary, or a "TL;DR".
        2. 'translate': Use if the user mentions Arabic or another language.
        3. 'analyze': Use if the user wants a deep dive, strategic audit, or risk assessment.
        4. 'recommend': Use if the user wants ideas, suggestions, or next steps.

        USER REQUEST: {user_request}

        DECISION (Return only the word):
        """
        
        self.prompt = PromptTemplate(
            input_variables=["user_request"],
            template=self.template
        )

    def decide(self, user_request: str) -> str:
        try:
            logger.info(f"Router: Classifying intent for: '{user_request}'")
            chain = self.prompt | self.llm
            decision = chain.invoke({"user_request": user_request}).strip().lower()
            
            # Validation logic to ensure the graph doesn't break
            valid_steps = ["summarize", "translate", "analyze", "recommend"]
            for step in valid_steps:
                if step in decision:
                    logger.info(f"Router: Directed to -> {step}")
                    return step
            
            logger.warning("Router: No clear intent found, defaulting to 'summarize'")
            return "summarize"
        except Exception as e:
            logger.error(f"Router Error: {e}")
            return "summarize"