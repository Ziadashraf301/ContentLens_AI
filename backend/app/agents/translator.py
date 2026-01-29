from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class TranslatorAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_TRANSLATOR,
            temperature=settings.TEMPERATURE_TRANSLATOR,
            num_predict=2048,
            num_ctx=8192,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a professional Arabic Translator specializing in Media and Advertising.
            Your task is to translate the provided document analysis into Modern Standard Arabic.
            RULES:
            - Keep technical terms like 'CTR', 'Brief', and 'Target Audience' in English if commonly used in the industry, or provide the Arabic equivalent in parentheses.
            - Ensure the tone is professional and suitable for an agency executive.
            - Translate the JSON values but KEEP the JSON keys in English.
            """),
            ("human", "DOCUMENT CONTENT:\n{content}\n\nARABIC TRANSLATION:")
        ])

    @trace_agent_execution("translation", settings.OLLAMA_MODEL_TRANSLATOR)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, content: str, source_lang: str | None = None):
        if source_lang == "ar":
            return f"Note: Content is already in Arabic. Original: {content}"
        async with ollama_gpu_limit:
            logger.info("Agent: Translator starting Arabic conversion...")
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"content": content})
            return response