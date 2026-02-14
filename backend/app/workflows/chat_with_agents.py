
from ..core.rate_limiter import request_limit
from ..core.langfuse import get_langfuse_callback, get_langfuse_tracer
from ..core.logging import logger
from langfuse import propagate_attributes
import asyncio

async def run_chat_workflow(user_request: str, file_path: str, message_type: str, tracer=None):
    """
    Orchestrates the execution of the AI Graph for chat interactions.
    """
    async with request_limit:
        # Use the passed tracer (from API) or create a new one as fallback
        if tracer is None:
            tracer = get_langfuse_tracer()
            logger.warning("Tracer not provided to workflow, creating new one")
        
        # Use propagate_attributes for tags, then start the trace
        with propagate_attributes(tags=["workflow", "chat_with_agents", "production"]):
            with tracer.client.start_as_current_observation(
                as_type="span",
                name="chat_with_agents_workflow",
                input={"user_request": user_request, "file_path": file_path, "message_type": message_type},
                metadata={"message_type": message_type}
            ) as trace:

                try:
                    # Here you would implement the actual logic to process the chat message
                    # For example, you might load the file, extract information, and generate a response
                    # This is a placeholder for demonstration purposes

                    # Simulate processing time
                    await asyncio.sleep(1)

                    ai_response = f"Processed message: '{user_request}' with file '{file_path}' and type '{message_type}'"
                    
                    trace.update(output={"ai_response": ai_response})
                    trace.score(name="workflow_success", value=1.0, comment="Workflow completed successfully", data_type="NUMERIC")

                    return {"response": ai_response}

                except Exception as e:
                    logger.error(f"Workflow failed: {e}")
                    trace.score(name="workflow_success", value=0.0, comment=str(e), data_type="NUMERIC")
                    trace.update_trace(output={"error": str(e)})
                    return {"error": str(e)}
