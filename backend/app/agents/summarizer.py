from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class SummarizerAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_SUMMARIZER
        )
        
        self.template = """
        SYSTEM:
        You are a senior Media Strategist. Summarize the following extracted brief data.
        Your goal is to provide a "30-second read" for a busy Creative Director.
        
        FORMAT:
        - One sentence 'Big Idea'.
        - 3 Bullet points for execution.
        - 1 Critical deadline or constraint.

        EXTRACTED DATA:
        {extraction_data}

        EXECUTIVE SUMMARY:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["extraction_data"],
            template=self.template
        )

    def run(self, extraction_data: dict):
        try:
            logger.info("Agent: Summarizer condensing data...")
            # Convert dict to string for the LLM
            content_str = str(extraction_data)
            chain = self.prompt | self.llm
            return chain.invoke({"extraction_data": content_str})
        except Exception as e:
            logger.error(f"Summarizer Error: {e}")
            return "Summarization failed."