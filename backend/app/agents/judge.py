from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from ..models.schemas.EvaluationOutput import EvaluationOutput
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution
from ..core.rate_limiter import ollama_gpu_limit
class JudgeAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_JUDGE,
            temperature=settings.TEMPERATURE_JUDGE,
            format="json" # Ensures Ollama returns valid JSON
        )
        
        self.parser = JsonOutputParser(pydantic_object=EvaluationOutput)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            SYSTEM:
            You are an AI Quality Judge. Your task is to evaluate the quality of AI-generated content for a specific agent type.
            Provide a score from 1-10 (10 being perfect) and brief reasoning.

            EVALUATION CRITERIA:
            - Relevance: How well it addresses the task
            - Accuracy: Factual correctness and coherence
            - Completeness: Coverage of required elements
            - Clarity: Clear and understandable
            - Quality: Overall professional quality

            CONSTRAINTS:
            - Output MUST be strictly valid JSON.
            - Do not include any conversational filler.
            - Score must be an integer from 1 to 10.

            {format_instructions}
            """),
            
            ("human", """
            AGENT TYPE: {agent_type}
            INPUT CONTEXT: {input_context}
            OUTPUT TO EVALUATE: {output}
            """)
        ]).partial(format_instructions=self.parser.get_format_instructions())

 
    @trace_agent_execution("judgement", settings.OLLAMA_MODEL_JUDGE)
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def evaluate(self, agent_type: str, input_context: str, output: str) -> dict:
        """
        Evaluate the output quality.
        Returns dict with score and reasoning.
        """
        async with ollama_gpu_limit:

            logger.info(f"Judge: Evaluating {agent_type} output...")

            chain = self.prompt | self.llm | self.parser

            result  = await chain.ainvoke({
                "agent_type": agent_type,
                "input_context": input_context,
                "output": str(output)
            })

            logger.info(f"Judge: {agent_type} scored {result['score']}/10")
            
            
            return {
                "score": result.get("score", 5),
                "reasoning": result.get("reasoning", ""),
                "agent_type": agent_type
            }