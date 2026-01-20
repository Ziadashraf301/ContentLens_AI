from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class RefinerAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_REFINER,
            temperature=settings.TEMPERATURE_REFINER
        )

        self.template = """
        SYSTEM:
        You are a Prompt Refinement AI. Your task is to refine and improve user requests based on extracted document information.
        Make the request more specific, actionable, and aligned with the document content.

        REFINEMENT GOALS:
        - Clarify ambiguous requests
        - Add context from the extracted information
        - Make the request more specific and actionable
        - Ensure the request aligns with available document data
        - Maintain the original intent while improving clarity

        EXTRACTED INFORMATION:
        {extraction}

        ORIGINAL USER REQUEST:
        {user_request}

        REFINED REQUEST:
        """

        self.prompt = PromptTemplate(
            input_variables=["extraction", "user_request"],
            template=self.template
        )

    @trace_agent_execution("refinement", settings.OLLAMA_MODEL_REFINER)
    def run(self, extraction: dict, user_request: str) -> str:
        """
        Refine the user request based on extraction data.
        """
        try:
            logger.info("Agent: Refiner starting work...")

            chain = self.prompt | self.llm

            response = chain.invoke({
                "extraction": str(extraction),
                "user_request": user_request
            })

            refined_request = response.strip()
            logger.info("Agent: Refinement completed successfully.")
            return refined_request

        except Exception as e:
            logger.error(f"Agent: Refiner failed with error: {str(e)}")
            # Return original request if refinement fails
            return user_request