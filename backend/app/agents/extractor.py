from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from ..core.config import settings
from ..core.logging import logger

class ExtractorAgent:
    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL_EXTRACTOR,
            temperature=settings.TEMPERATURE_EXTRACTOR 
        )
        
        # Define the Expected Output Structure
        self.parser = JsonOutputParser()
        
        # Build a Robust Prompt (The "System Instructions")
        template = """
        SYSTEM:
        You are a specialized Media Analysis AI. Your task is to extract structured information 
        from raw text briefs provided by advertising agencies.
        
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

        USER TEXT TO ANALYZE:
        {text}
        """

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

    def run(self, text: str):
        """
        The execution logic.
        """
        try:
            logger.info("Agent: Extractor starting work...")
            
            chain = self.prompt | self.llm | self.parser
            
            response = chain.invoke({"text": text})
            logger.info("Agent: Extraction completed successfully.")
            return response
            
        except Exception as e:
            logger.error(f"Agent: Extractor failed with error: {str(e)}")
            # Return a structured error so the Graph knows how to handle it
            return {
                "title": "Error",
                "summary": "Extraction failed",
                "key_points": [],
                "error_details": str(e)
            }