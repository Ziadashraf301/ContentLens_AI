from langchain_ollama import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_cohere import ChatCohere
from ..core.config import settings
from ..core.logging import logger
from ..core.langfuse import trace_agent_execution
from ..core.rate_limiter import ollama_gpu_limit

class ExtractorAgent:
    def __init__(self):
        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_EXTRACTOR,
            temperature=settings.TEMPERATURE_EXTRACTOR,
            num_predict=2048,
            num_ctx=8192,
            format="json"
        )
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a specialized Media Analysis AI. Your task is to extract structured information from raw text briefs provided by advertising agencies.
            GOAL:
            Parse the text and identify the core message and actionable data points.
            EXTRACT THESE FIELDS WHERE PRESENT:
            - CampaignName: The name of the campaign
            - Brand: The brand name
            - TargetAudience: Description of the target audience
            - CoreMessage: The main message or tagline
            - ActionableDataPoints: Object with LaunchDate, PrimaryChannel, Budget, Goal, CreativeRequirements
            - CallToAction: The CTA text
            - AdvertiserContact: Object with name, email, phone
            CONSTRAINTS:
            - Output MUST be strictly valid JSON.
            - Do not include any conversational filler or "Here is the JSON".
            - If a field is missing in the text, set it to null.
            - Use the specific language found in the text.
            {format_instructions}
            """),
            ("human", "USER TEXT TO ANALYZE:\n{text}")
        ]).partial(format_instructions=self.parser.get_format_instructions())

    @trace_agent_execution("extraction", settings.OLLAMA_MODEL_EXTRACTOR)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def run(self, text: str):
        async with ollama_gpu_limit:
            logger.info("Agent: Extractor parsing document...")
            try:
                chain = self.prompt | self.llm
                response = await chain.ainvoke({"text": str(text)})
                metadata = response.response_metadata
                input_tokens = metadata.get('prompt_eval_count', 0)
                output_tokens = metadata.get('eval_count', 0)
                logger.info(f"Extractor tokens: input={input_tokens}, output={output_tokens}")
                try:
                    return self.parser.parse(response.content)
                except Exception as parse_error:
                    logger.warning(f"Failed to parse JSON: {parse_error}")
                    return response.content
            except Exception as e:
                logger.warning(f"Ollama failed permanently. Attempting Cohere fallback... Error: {e}")
                try:
                    fallback_llm = ChatCohere(
                        cohere_api_key=settings.COHERE_API_KEY,
                        model="command-r-plus"
                    )
                    fallback_chain = self.prompt | fallback_llm
                    rescue_response = await fallback_chain.ainvoke({"text": str(text)})
                    return self.parser.parse(rescue_response.content)
                except Exception as cohere_error:
                    logger.error(f"Critical: Both Ollama and Cohere failed. {cohere_error}")
                    return {
                        "title": "Error",
                        "summary": "Extraction failed",
                        "key_points": [],
                        "error_details": f"Ollama error: {e}, Cohere error: {cohere_error}"
                    }