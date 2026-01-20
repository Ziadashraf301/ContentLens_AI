from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution

class JudgeAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_JUDGE,
            temperature=settings.TEMPERATURE_JUDGE
        )

        self.template = """
        SYSTEM:
        You are an AI Quality Judge. Your task is to evaluate the quality of AI-generated content for a specific agent type.
        Provide a score from 1-10 (10 being perfect) and brief reasoning.

        EVALUATION CRITERIA:
        - Relevance: How well it addresses the task
        - Accuracy: Factual correctness and coherence
        - Completeness: Coverage of required elements
        - Clarity: Clear and understandable
        - Quality: Overall professional quality

        AGENT TYPE: {agent_type}
        INPUT CONTEXT: {input_context}
        OUTPUT TO EVALUATE: {output}

        Provide your evaluation in this format:
        SCORE: [1-10]
        REASONING: [brief explanation]
        """

        self.prompt = PromptTemplate(
            input_variables=["agent_type", "input_context", "output"],
            template=self.template
        )

    @trace_agent_execution("judgement", settings.OLLAMA_MODEL_JUDGE)
    def evaluate(self, agent_type: str, input_context: str, output: str) -> dict:
        """
        Evaluate the output quality.
        Returns dict with score and reasoning.
        """
        try:
            logger.info(f"Judge: Evaluating {agent_type} output...")

            chain = self.prompt | self.llm

            response = chain.invoke({
                "agent_type": agent_type,
                "input_context": input_context,
                "output": str(output)
            })

            # Parse the response
            response_text = response.strip()
            lines = response_text.split('\n')

            score = 5  # default
            reasoning = "Evaluation failed to parse"

            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score = int(line.split(':', 1)[1].strip())
                        score = max(1, min(10, score))  # clamp to 1-10
                    except:
                        pass
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()

            logger.info(f"Judge: {agent_type} scored {score}/10")
            return {
                "score": score,
                "reasoning": reasoning,
                "agent_type": agent_type
            }

        except Exception as e:
            logger.error(f"Judge: Evaluation failed with error: {str(e)}")
            return {
                "score": 1,
                "reasoning": f"Evaluation error: {str(e)}",
                "agent_type": agent_type
            }