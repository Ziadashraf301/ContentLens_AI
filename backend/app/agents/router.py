import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from ..core.rate_limiter import ollama_gpu_limit
from ..core.config import settings
import structlog
logger = structlog.get_logger(__name__)
from ..core.langfuse import trace_agent_execution

class RouterAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ROUTER,
            num_predict=512,
            num_ctx=2072,
            temperature=0, # Router should be deterministic (not creative)
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an Intent Classifier for a Media AI system. 
            Your job is to read a User Request and decide which agents should handle it.
            You can select MULTIPLE agents if the request requires it.
            
            AVAILABLE AGENTS:
            1. 'summarize': For shorter version, summary, or TL;DR
            2. 'translate': For translation to Arabic or other languages
            3. 'analyze': For deep dive, strategic audit, or risk assessment
            4. 'recommend': For ideas, suggestions, or next steps
            5. 'ideate': For marketing campaign ideas and themes
            6. 'copywrite': For drafting marketing copy (emails, ads, landing pages)
            7. 'compliance': For checking content against privacy and marketing regulations
            
            RULES:
            - Return a comma-separated list of agents needed
            - Order matters: run them in the order you list
            - Examples:
              * "Analyze this brief" → analyze
              * "Translate to Arabic and analyze" → translate,analyze
              * "Give me a full report" → summarize,analyze,recommend
              * "Generate campaign ideas" → ideate
            """),
            ("human", "USER REQUEST: {user_request}\n\nAGENTS NEEDED (comma-separated list only):")
        ])

    @trace_agent_execution("router", settings.OLLAMA_MODEL_ROUTER)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def decide(self, user_request: str) -> list:
        async with ollama_gpu_limit:
            logger.info(f"Router: Classifying intent for: '{user_request}'")
            chain = self.prompt | self.llm
            response = await chain.ainvoke({"user_request": user_request})
            
            response_text = response.content.strip().lower()
            # Clean up potential LLM conversational noise
            tasks = [task.strip() for task in response_text.replace(".", "").split(",")]
            
            valid_steps = ["summarize", "translate", "analyze", "recommend", "ideate", "copywrite", "compliance"]
            filtered_tasks = []
            
            for task in tasks:
                for valid in valid_steps:
                    # check if 'ideate' is in 'ideation' or vice versa
                    if valid in task and valid not in filtered_tasks:
                        filtered_tasks.append(valid)
                        break
            
            if not filtered_tasks:
                logger.warning("Router: LLM returned unclear response, using keyword fallback")
                filtered_tasks = self._keyword_fallback(user_request)
            
            logger.info(f"Router: Directed to -> {filtered_tasks}")
            return filtered_tasks

    def _keyword_fallback(self, user_request: str) -> list:
        request_lower = user_request.lower()
        tasks = []
        
        if any(word in request_lower for word in ["translate", "arabic", "عربي", "ترجم"]):
            tasks.append("translate")
        if any(word in request_lower for word in ["analyze", "audit", "assess", "review", "brief"]):
            tasks.append("analyze")
        if any(word in request_lower for word in ["summarize", "summary", "tldr", "short"]):
            tasks.append("summarize")
        if any(word in request_lower for word in ["recommend", "suggestion", "next steps"]):
            tasks.append("recommend")
        if any(word in request_lower for word in ["idea", "campaign", "concept"]):
            tasks.append("ideate")
        if any(word in request_lower for word in ["email", "copy", "ad", "headline"]):
            tasks.append("copywrite")
        if any(word in request_lower for word in ["privacy", "compliance", "gdpr"]):
            tasks.append("compliance")
        
        return tasks if tasks else ["analyze"]