from ..tools.file_loader import FileLoader
from ..graphs.document_graph import app_graph
from ..core.logging import logger
from ..tools.language import detect_language
from ..tools.validators import BriefValidator
from ..core.langfuse import get_langfuse_callback


async def run_document_workflow(file_path: str, user_request: str):
    """
    Orchestrates the pre-processing and execution of the AI Graph.
    """
    try:
        # Load and Extract
        loader = FileLoader(file_path)
        extracted_text = loader.load()
        
        if not extracted_text:
            logger.error(f"Workflow failed: No text extracted from {file_path}")
            return {"error": "No text could be extracted from the file."}

        # Sanitize and Validate
        # We use the validator to clean up extra whitespace/junk
        clean_text = BriefValidator.sanitize_text(extracted_text)

        print(clean_text)

        if not BriefValidator.is_valid_brief(clean_text):
            # We don't stop the flow, but we log a warning for the audit trail
            logger.warning(f"Quality Check: File at {file_path} has low brief-keyword density.")

        # Intelligence Gathering
        # Detecting language helps the Router or Translator make better decisions later
        source_lang = detect_language(clean_text)
        logger.info(f"Workflow: File processing started. Language: {source_lang}")

        # Prepare the Initial State for LangGraph
        # We pass 'clean_text' as the primary source to save LLM tokens/noise
        initial_state = {
            "raw_text": clean_text,
            "user_request": user_request,
            "source_lang": source_lang, # Pass the detected language to the graph!
            "errors": []
        }

        # Execute the Brain (LangGraph)
        logger.info("Workflow: Handing off to LangGraph...")
        langfuse_handler = get_langfuse_callback()

        # Initialize the observer
        config = {}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        # ainvoke is used for asynchronous execution
        final_state = await app_graph.ainvoke(initial_state, config=config)
        
        return final_state

    except Exception as e:
        logger.error(f"Workflow Critical Error: {str(e)}")
        return {"error": str(e)}