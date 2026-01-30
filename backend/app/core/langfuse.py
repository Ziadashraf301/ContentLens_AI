from langfuse import Langfuse, get_client, propagate_attributes
from langfuse.langchain import CallbackHandler
from app.core.config import settings
import time

_langfuse_callback = None

def init_langfuse():
    """Initialize Langfuse with credentials from settings."""
    global _langfuse_callback

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        # This creates a singleton that CallbackHandler() will use
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        
        # It automatically uses get_client() internally
        _langfuse_callback = CallbackHandler()


def get_langfuse_callback():
    """Get the LangChain callback handler."""
    return _langfuse_callback


def get_langfuse_client():
    """Get the Langfuse client for manual operations."""
    return get_client()


class LangfuseTracer:
    """Enhanced tracer for agent observability using Langfuse 3.x API."""

    def __init__(self):
        self.client = get_client()


def trace_agent_execution(agent_name: str, model_name: str):
    """Decorator for tracing agent executions."""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            tracer = get_langfuse_tracer()
            if not tracer.client:
                return await func(self, *args, **kwargs)

            # Use propagate_attributes for tags, then start observation
            with propagate_attributes(tags=[agent_name, "agent"]):
                with tracer.client.start_as_current_observation(
                    as_type="span",
                    name=f"agent_{agent_name}",
                    metadata={"agent": agent_name, "model": model_name}
                ) as trace_span:
                    
                    # Add execution span
                    with trace_span.start_as_current_observation(
                        as_type="span",
                        name=f"{agent_name}_execution",
                        input={"args": str(args), "kwargs": str(kwargs)},
                        metadata={"start_time": time.time()}
                    ) as exec_span:

                        try:
                            # Execute the agent
                            result = await func(self, *args, **kwargs)
                            
                            # Extract tokens (only if AIMessage)
                            usage = {}
                            if hasattr(result, "response_metadata"):
                                meta = result.response_metadata
                                usage = {
                                    "input": meta.get("prompt_eval_count", 0),
                                    "output": meta.get("eval_count", 0),
                                    "total": meta.get("prompt_eval_count", 0) + meta.get("eval_count", 0)
                                }

                            # Log the generation
                            output_text = result.content if hasattr(result, 'content') else str(result)

                            # Get input for generation log
                            gen_input = "Input unavailable"
                            if hasattr(self, 'prompt') and len(args) > 0:
                                try:
                                    gen_input = str(self.prompt.format(**{k: args[0] for k in self.prompt.input_variables}))
                                except:
                                    gen_input = str(args[0])

                            # Log generation
                            with trace_span.start_as_current_observation(
                                as_type="generation",
                                name=f"{agent_name}_llm_call",
                                model=model_name,
                                input=gen_input,
                                output=output_text,
                                metadata={**{"agent": agent_name}, **usage}
                            ):
                                pass

                            # Validate and score
                            from app.utils.output_validator import OutputValidator
                            is_valid = OutputValidator.validate_agent_output(agent_name, output_text)
                            
                            trace_span.score(
                                name=f"{agent_name}_validation",
                                value=1.0 if is_valid else 0.0,
                                comment="Output format validation",
                                data_type="NUMERIC"
                            )

                            # Update execution span with success
                            exec_span.update(
                                output={"result": output_text},
                                metadata={"end_time": time.time(), "success": True}
                            )

                            return result

                        except Exception as e:
                            # Update execution span with error
                            exec_span.update(
                                metadata={"error": str(e), "success": False, "end_time": time.time()}
                            )
                            raise

        return wrapper
    return decorator


# Global tracer instance
_tracer = None


def get_langfuse_tracer():
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer