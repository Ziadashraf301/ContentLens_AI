from ..tools.file_loader import FileLoader
from ..graphs.document_graph import app_graph
from ..core.logging import logger
from ..tools.language import detect_language
from ..tools.validators import BriefValidator
from ..core.langfuse import get_langfuse_callback, get_langfuse_tracer


async def run_document_workflow(file_path: str, user_request: str):
    """
    Orchestrates the pre-processing and execution of the AI Graph.
    """
    tracer = get_langfuse_tracer()
    trace = tracer.start_trace(
        name="document_processing_workflow",
        metadata={"file_path": file_path, "user_request": user_request},
        tags=["workflow", "document_processing", "production"]
    )

    try:
    try:
        # Load and Extract
        load_span = tracer.add_span(trace, "file_loading", input_data={"file_path": file_path})
        loader = FileLoader(file_path)
        extracted_text = loader.load()
        load_span.output_data = {"text_length": len(extracted_text) if extracted_text else 0}
        
        if not extracted_text:
            logger.error(f"Workflow failed: No text extracted from {file_path}")
            tracer.add_score(trace, "workflow_success", 0.0, "No text extracted")
            tracer.end_trace(trace)
            return {"error": "No text could be extracted from the file."}

        # Sanitize and Validate
        validate_span = tracer.add_span(trace, "validation", input_data={"text_length": len(extracted_text)})
        clean_text = BriefValidator.sanitize_text(extracted_text)

        if not BriefValidator.is_valid_brief(clean_text):
            logger.warning(f"Quality Check: File at {file_path} has low brief-keyword density.")
            validate_span.metadata = {"quality_check": "low_density"}

        # Intelligence Gathering
        lang_span = tracer.add_span(trace, "language_detection", input_data={"text_sample": clean_text[:100]})
        source_lang = detect_language(clean_text)
        lang_span.output_data = {"detected_lang": source_lang}

        # Prepare the Initial State for LangGraph
        initial_state = {
            "raw_text": clean_text,
            "user_request": user_request,
            "source_lang": source_lang,
            "errors": []
        }

        # Execute the Brain (LangGraph)
        logger.info("Workflow: Handing off to LangGraph...")
        langfuse_handler = get_langfuse_callback()

        config = {}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        graph_span = tracer.add_span(trace, "graph_execution", input_data={"initial_state_keys": list(initial_state.keys())})
        final_state = await app_graph.ainvoke(initial_state, config=config)
        graph_span.output_data = {"final_state_keys": list(final_state.keys())}

        tracer.add_score(trace, "workflow_success", 1.0, "Completed successfully")
        tracer.end_trace(trace)
        
        # Return trace ID for scoring
        result["trace_id"] = trace.id if trace else None
        return final_state

    except Exception as e:
        logger.error(f"Workflow Critical Error: {str(e)}")
        tracer.add_score(trace, "workflow_success", 0.0, f"Error: {str(e)}")
        tracer.end_trace(trace)
        return {"error": str(e)}