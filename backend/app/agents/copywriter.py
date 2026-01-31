from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class CopywriterAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_COPYWRITER,
            temperature=settings.TEMPERATURE_COPYWRITER,
            num_predict=1024,
            num_ctx=3072,
        )
        
        # Using ChatPromptTemplate to separate the Persona from the Data
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior performance-focused marketing copywriter with experience in email and digital campaign optimization.

            TASK:
            Based on the provided content brief and user request, generate multiple copy variants suitable for A/B testing.

            OUTPUT RULES:
            - Provide exactly 3 copy variants.
            - Each variant must include:
            1) Subject line (email)
            2) Body copy (1–2 concise sentences)
            3) CTA (2–4 words max)
            - Variants should differ meaningfully in angle, not just wording.
            - Match the requested tone and audience from the brief.
            - Avoid clichés and generic marketing language.
            - Do not invent offers, deadlines, or claims not present in the brief.
            - If the user request specifies a language (e.g., translate to Arabic), output the entire response in that language.
            - Keep it professional and actionable.

            FORMAT (STRICT):
            Variant 1:
            - Subject:
            - Body:
            - CTA:

            Variant 2:
            - Subject:
            - Body:
            - CTA:

            Variant 3:
            - Subject:
            - Body:
            - CTA:

            Do not include any conversational filler or "Here is the content"."""),
            
            ("human", "BRIEF:\n{brief}\n\nUSER REQUEST:\n\nCOPY VARIANTS:")
        ])

    @trace_agent_execution("copywriter", settings.OLLAMA_MODEL_COPYWRITER)
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=False
    )
    async def run(self, brief: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Copywriter creating variants...")
                
            # Chain definition
            chain = self.prompt | self.llm
                
            # ChatOllama returns an AIMessage object
            response = await chain.ainvoke({"brief": str(brief)})
                
            return response