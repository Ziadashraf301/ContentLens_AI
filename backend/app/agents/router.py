from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class RouterAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_ROUTER
        )
        
        self.template = """
        SYSTEM:
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
          * "Translate this" → translate
          * "Write email copy" → copywrite
          * "Generate campaign ideas" → ideation
          * "What are the recommendations?" → recommend
          * "Check compliance" → compliance
          * "Summarize and translate" → summarize,translate
          * "Analyze and give ideas" → analyze,recommend,ideate

        USER REQUEST: {user_request}

        AGENTS NEEDED (comma-separated list only, no explanations):
        """
        
        self.prompt = PromptTemplate(
            input_variables=["user_request"],
            template=self.template
        )

    @trace_agent_execution("router", settings.OLLAMA_MODEL_ROUTER)
    def decide(self, user_request: str) -> list:
        """
        Returns a list of tasks to execute in order.
        Example: ["translate", "analyze"]
        """
        try:
            logger.info(f"Router: Classifying intent for: '{user_request}'")
            chain = self.prompt | self.llm
            response = chain.invoke({"user_request": user_request}).strip().lower()
            
            # Parse comma-separated response
            tasks = [task.strip() for task in response.split(",")]
            
            # Validate and filter
            valid_steps = ["summarize", "translate", "analyze", "recommend", "ideate", "copywrite", "compliance"]
            filtered_tasks = []
            
            for task in tasks:
                for valid in valid_steps:
                    if valid in task and valid not in filtered_tasks:
                        filtered_tasks.append(valid)
                        break
            
            # Fallback logic based on keywords if LLM fails
            if not filtered_tasks:
                logger.warning("Router: LLM returned unclear response, using keyword fallback")
                filtered_tasks = self._keyword_fallback(user_request)
            
            logger.info(f"Router: Directed to -> {filtered_tasks}")
            return filtered_tasks
            
        except Exception as e:
            logger.error(f"Router Error: {e}, using keyword fallback")
            return self._keyword_fallback(user_request)
    
    def _keyword_fallback(self, user_request: str) -> list:
        """
        Keyword-based fallback if LLM fails
        """
        request_lower = user_request.lower()
        tasks = []
        
        # Check for translation request
        if any(word in request_lower for word in ["translate", "arabic", "عربي", "ترجم"]):
            tasks.append("translate")
        
        # Check for analysis request
        if any(word in request_lower for word in ["analyze", "analysis", "audit", "assess", "review", "brief"]):
            tasks.append("analyze")
        
        # Check for summary request
        if any(word in request_lower for word in ["summarize", "summary", "tldr", "brief overview", "short"]):
            if "summarize" not in tasks:
                tasks.insert(0, "summarize")
        
        # Check for recommendations
        if any(word in request_lower for word in ["recommend", "suggestion", "ideas", "what should", "next steps"]):
            tasks.append("recommend")

        # Marketing ideation
        if any(word in request_lower for word in ["idea", "ideas", "campaign", "headline", "tagline", "concept"]):
            tasks.append("ideate")

        # Copywriting hints
        if any(word in request_lower for word in ["email", "subject", "copy", "landing", "ad", "headline", "cta"]):
            tasks.append("copywrite")

        # Compliance checks
        if any(word in request_lower for word in ["gdpr", "can-spam", "privacy", "compliance", "opt-out", "unsubscribe"]):
            tasks.append("compliance")
        
        # Default to analyze if nothing matches
        if not tasks:
            tasks = ["analyze"]
        
        return tasks