from ..tools.file_loader import FileLoader
from ..graphs.document_graph import app_graph
from ..core.logging import logger
from ..tools.language import detect_language
from ..tools.validators import BriefValidator
from ..core.langfuse import get_langfuse_callback, get_langfuse_tracer
from langfuse import propagate_attributes
from typing import Any, Dict


def _extract_agent_output(value: Any) -> str:
    """
    Extract string output from potentially nested agent output structures.
    
    Handles both:
    - Direct string values (from nodes)
    - AgentOutput dict objects (from parallel execution)
    - None values
    """
    if value is None:
        return ""
    
    # If it's already a string, return as-is
    if isinstance(value, str):
        return value
    
    # If it's a dict (AgentOutput), extract the 'output' field
    if isinstance(value, dict):
        # Check if it's an AgentOutput dict with 'output' field
        if "output" in value:
            output = value["output"]
            # Recursively handle if nested
            return _extract_agent_output(output)
        # Otherwise return str representation
        return str(value)
    
    # For any other type, convert to string
    return str(value)


def _clean_response_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean the state to ensure all response fields are properly formatted strings.
    
    Extracts actual outputs from AgentOutput objects and ensures no nested
    dicts are returned for string fields.
    """
    cleaned = state.copy()
    
    # List of fields that should be strings in the response
    string_fields = [
        "summary", "analysis", "recommendation", "ideation", 
        "copywriting", "translation"
    ]
    
    for field in string_fields:
        if field in cleaned:
            cleaned[field] = _extract_agent_output(cleaned[field])
    
    # Handle compliance specially (it can be a dict)
    if "compliance" in cleaned:
        value = cleaned["compliance"]
        if isinstance(value, dict) and "output" in value:
            # It's an AgentOutput, extract output
            cleaned["compliance"] = value["output"]
    
    # Remove internal structures that shouldn't be in API response
    internal_fields = [
        "agent_outputs", "agent_metadata", "agent_errors", 
        "agent_evaluations", "pending_agents"
    ]
    for field in internal_fields:
        cleaned.pop(field, None)
    
    return cleaned


async def run_document_workflow(file_path: str, user_request: str):
    """
    Orchestrates the pre-processing and execution of the AI Graph.
    """
    tracer = get_langfuse_tracer()
    
    # Use propagate_attributes for tags, then start the trace
    with propagate_attributes(tags=["workflow", "document_processing", "production"]):
        with tracer.client.start_as_current_observation(
            as_type="span",
            name="document_processing_workflow",
            input={"file_path": file_path, "user_request": user_request},
            metadata={"file_path": file_path}
        ) as trace:

            try:
                # Load and Extract
                with trace.start_as_current_observation(
                    as_type="span",
                    name="file_loading",
                    input={"file_path": file_path}
                ) as load_span:
                    loader = FileLoader(file_path)
                    extracted_text = loader.load()
                    load_span.update(output={
                        "text_length": len(extracted_text) if extracted_text else 0,
                        "text": extracted_text if extracted_text else ""})
                
                if not extracted_text:
                    logger.error(f"Workflow failed: No text extracted from {file_path}")
                    trace.score(name="workflow_success", value=0.0, comment="No text extracted", data_type="NUMERIC")
                    # Set trace output even on error
                    trace.update_trace(output={"error": "No text could be extracted from the file."})
                    return {"error": "No text could be extracted from the file."}

                # Sanitize and Validate
                with trace.start_as_current_observation(
                    as_type="span",
                    name="validation",
                    input={"text_length": len(extracted_text)}
                ) as validate_span:
                    clean_text = BriefValidator.sanitize_text(extracted_text)

                    if not BriefValidator.is_valid_brief(clean_text):
                        logger.warning(f"Quality Check: File at {file_path} has low brief-keyword density.")
                        validate_span.update(
                            output={"clean_text_length": len(clean_text)},
                            metadata={"quality_check": "low_density"}
                        )
                    else:
                        validate_span.update(output={"clean_text_length": len(clean_text)},
                                             metadata={"quality_check": "high_density"})

                # Intelligence Gathering
                with trace.start_as_current_observation(
                    as_type="span",
                    name="language_detection",
                    input={"text_sample": clean_text}
                ) as lang_span:
                    source_lang = detect_language(clean_text)
                    lang_span.update(output={"detected_lang": source_lang})

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

                with trace.start_as_current_observation(
                    as_type="span",
                    name="graph_execution",
                    input={"initial_state_keys": list(initial_state.keys())}
                ) as graph_span:
                    final_state = await app_graph.ainvoke(initial_state, config=config)
                    graph_span.update(output={"final_state_keys": list(final_state.keys())})

                # Set trace-level output explicitly
                trace.update_trace(
                    output={
                        "raw_text": str(final_state.get("raw_text", "")),
                        "extraction": str(final_state.get("extraction", "")),
                        "summary": _extract_agent_output(final_state.get("summary", "")),
                        "analysis": _extract_agent_output(final_state.get("analysis", "")),
                        "recommendation": _extract_agent_output(final_state.get("recommendation", "")),
                        "ideation": _extract_agent_output(final_state.get("ideation", "")),
                        "copywriting": _extract_agent_output(final_state.get("copywriting", "")),
                        "compliance": _extract_agent_output(final_state.get("compliance", "")),
                        "translation": _extract_agent_output(final_state.get("translation", "")),
                        "completed_steps": final_state.get("next_steps", []),
                        "status": "success"
                    }
                )

                trace.score(name="workflow_success", value=1.0, comment="Completed successfully", data_type="NUMERIC")
                
                # Get trace ID from the span
                trace_id = trace.trace_id if hasattr(trace, 'trace_id') else None
                final_state["trace_id"] = trace_id
                
                # Clean up response to ensure all fields are properly serialized
                final_state = _clean_response_state(final_state)
                
                return final_state

            except Exception as e:
                logger.error(f"Workflow Critical Error: {str(e)}")
                trace.score(name="workflow_success", value=0.0, comment=f"Error: {str(e)}", data_type="NUMERIC")
                # Set trace output on error
                trace.update_trace(output={"error": str(e), "status": "failed"})
                return {"error": str(e)}