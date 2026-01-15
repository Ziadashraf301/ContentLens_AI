from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class TranslatorAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_TRANSLATOR,
            temperature=settings.TEMPERATURE_TRANSLATOR
        )
        
        self.template = """
        SYSTEM:
        You are a professional Arabic Translator specializing in Media and Advertising.
        Your task is to translate the provided document analysis into Modern Standard Arabic.
        
        RULES:
        - Keep technical terms like "CTR", "Brief", and "Target Audience" in English if commonly used in the industry, or provide the Arabic equivalent in parentheses.
        - Ensure the tone is professional and suitable for an agency executive.
        - Translate the JSON values but KEEP the JSON keys in English.

        DOCUMENT CONTENT:
        {content}

        ARABIC TRANSLATION:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["content"],
            template=self.template
        )

    @trace_agent_execution("translation", settings.OLLAMA_MODEL_TRANSLATOR)
    def run(self, content: str, source_lang: str | None = None):
        if source_lang == "ar":
            return f"Note: Content is already in Arabic. Original: {content}"
        
        try:
            logger.info("Agent: Translator starting Arabic conversion...")
            chain = self.prompt | self.llm
            response = chain.invoke({"content": content})
            return response
        except Exception as e:
            logger.error(f"Translator Error: {e}")
            return f"Translation failed: {str(e)}"