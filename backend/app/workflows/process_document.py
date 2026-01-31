from ..tools.file_loader import FileLoader
from ..graphs.document_graph import app_graph
from ..core.logging import logger
from ..tools.language import detect_language
from ..tools.validators import BriefValidator
from ..core.langfuse import get_langfuse_callback, get_langfuse_tracer
from langfuse import propagate_attributes
from ..core.rate_limiter import request_limit

async def run_document_workflow(file_path: str, user_request: str, tracer=None):
    """
    Orchestrates the pre-processing and execution of the AI Graph.
    """
    async with request_limit:
        # Use the passed tracer (from API) or create a new one as fallback
        if tracer is None:
            tracer = get_langfuse_tracer()
            logger.warning("Tracer not provided to workflow, creating new one")
        
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
                        "errors": [],  
                        "evaluations": []
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
                    # Create a safe getter
                    compliance_data = final_state.get("compliance") or {}
                    evaluations = final_state.get("evaluations", [])
                    valid_evaluations = [e for e in evaluations if e and isinstance(e, dict)]  # Filter out None values
                    average_score = (
                        sum(e.get("score", 0) for e in valid_evaluations) / len(valid_evaluations)
                        if valid_evaluations else 0
                    )

                    trace.update_trace(
                        output={
                            "raw_text": str(final_state.get("raw_text", "")),  
                            "extraction": str(final_state.get("extraction", "")),
                            "summary": str(final_state.get("summary", "")),
                            "analysis": str(final_state.get("analysis", "")),
                            "recommendation": str(final_state.get("recommendation", "")),
                            "ideation": str(final_state.get("ideation", "")),
                            "copywriting": str(final_state.get("copywriting", "")),
                            "translation": str(final_state.get("translation", "")),
                            
                            # Handle compliance report structure
                            "compliance_status": compliance_data.get("status", "unknown"),
                            "compliance_risk_score": compliance_data.get("overall_risk_score", 0),
                            "compliance_issues_count": compliance_data.get("issue_count", 0),
                            
                            # Include evaluation scores from all agents
                            "evaluations": valid_evaluations,
                            "evaluation_count": len(valid_evaluations),
                            "average_score": average_score,
                            
                            # Include errors from parallel agents
                            "errors": final_state.get("errors", []),
                            "error_count": len(final_state.get("errors", [])),
                            
                            "completed_steps": final_state.get("next_steps", []),
                            "status": "success"
                        }
                    )

                    trace.score(name="workflow_success", value=1.0, comment="Completed successfully", data_type="NUMERIC")
                    
                    # Get trace ID from the span
                    trace_id = trace.trace_id if hasattr(trace, 'trace_id') else None
                    final_state["trace_id"] = trace_id
                    
                    return final_state

                except Exception as e:
                    logger.error(f"Workflow Critical Error: {str(e)}")
                    trace.score(name="workflow_success", value=0.0, comment=f"Error: {str(e)}", data_type="NUMERIC")
                    trace.update_trace(output={"error": str(e), "status": "failed"})
                    return {"error": str(e)}