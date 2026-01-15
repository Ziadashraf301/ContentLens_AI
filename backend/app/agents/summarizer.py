from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger

class SummarizerAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_SUMMARIZER,
            temperature=settings.TEMPERATURE_SUMMARIZER
        )
        
        self.template = """
        SYSTEM:
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