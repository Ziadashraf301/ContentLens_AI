from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from app.core.config import settings
import time
from typing import Optional, Dict, Any

_langfuse_callback = None


def init_langfuse():
    """Initialize Langfuse with credentials from settings."""
    global _langfuse_callback

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        # CRITICAL: In Langfuse 3.x, you MUST initialize the client first
        # This creates a singleton that CallbackHandler() will use
        Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        
        # CRITICAL: CallbackHandler() takes NO arguments in Langfuse 3.x
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

    def start_trace(self, name: str, user_id: Optional[str] = None,
                   session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   tags: Optional[list] = None):
        """
        Start a new trace using context manager pattern.
        Returns a span object that can be used with 'with' statement.
        """
        if not self.client:
            return None

        # Build trace context attributes
        trace_attrs = {}
        if user_id:
            trace_attrs['user_id'] = user_id
        if session_id:
            trace_attrs['session_id'] = session_id
        if metadata:
            trace_attrs['metadata'] = metadata
        if tags:
            trace_attrs['tags'] = tags

        # In Langfuse 3.x, use start_as_current_observation with context manager
        return self.client.start_as_current_observation(
            as_type="span",
            name=name,
            **trace_attrs
        )

    def log_generation(self, parent_span, name: str, model: str, prompt: str,
                      completion: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a generation (LLM call) with prompt and completion."""
        if not parent_span:
            return None

        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(completion) // 4
        total_tokens = prompt_tokens + completion_tokens

        # Estimate cost (very rough, adjust based on your model pricing)
        estimated_cost = total_tokens * 0.000001  # Example rate

        generation_metadata = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
            **(metadata or {})
        }

        # Create generation as child of parent span
        generation = parent_span.start_as_current_observation(
            as_type="generation",
            name=name,
            model=model,
            input=prompt,
            output=completion,
            metadata=generation_metadata,
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": total_tokens
            }
        )
        
        return generation

    def add_score(self, span_or_generation, name: str, value: float,
                 comment: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a score to a span or generation."""
        if not span_or_generation:
            return

        span_or_generation.score(
            name=name,
            value=value,
            comment=comment,
            data_type="NUMERIC"
        )

    def add_span(self, parent_span, name: str, input_data: Optional[Dict[str, Any]] = None,
                output_data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a child span for agent operations."""
        if not parent_span:
            return None

        # Create child span
        child_span = parent_span.start_as_current_observation(
            as_type="span",
            name=name,
            input=input_data or {},
            metadata=metadata or {}
        )
        
        # If output_data is provided, update the span
        if output_data and child_span:
            child_span.update(output=output_data)
        
        return child_span

    def update_span(self, span, output_data: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """Update a span with output or metadata."""
        if not span:
            return
        
        update_dict = {}
        if output_data:
            update_dict['output'] = output_data
        if metadata:
            update_dict['metadata'] = metadata
            
        if update_dict:
            span.update(**update_dict)

    def end_trace(self, span):
        """
        End the trace/span and flush data to Langfuse.
        In Langfuse 3.x with context managers, this is usually handled automatically,
        but we can explicitly flush here for short-lived apps.
        """
        if span and self.client:
            self.client.flush()


def trace_agent_execution(agent_name: str, model_name: str):
    """Decorator for tracing agent executions."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            tracer = get_langfuse_tracer()
            if not tracer.client:
                return func(self, *args, **kwargs)

            # Start trace as a span
            with tracer.client.start_as_current_observation(
                as_type="span",
                name=f"agent_{agent_name}",
                metadata={"agent": agent_name, "model": model_name},
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
                        result = func(self, *args, **kwargs)

                        # Log the generation
                        prompt = getattr(self, 'template', 'No template available')
                        if hasattr(self, 'prompt') and hasattr(self.prompt, 'template'):
                            prompt = self.prompt.template

                        with trace_span.start_as_current_observation(
                            as_type="generation",
                            name=f"{agent_name}_llm_call",
                            model=model_name,
                            input=prompt,
                            output=str(result),
                            metadata={"agent": agent_name}
                        ):
                            pass  # Generation is automatically recorded

                        # Validate and score
                        from app.utils.output_validator import OutputValidator
                        is_valid = OutputValidator.validate_agent_output(agent_name, result)
                        
                        trace_span.score(
                            name=f"{agent_name}_validation",
                            value=1.0 if is_valid else 0.0,
                            comment="Output format validation",
                            data_type="NUMERIC"
                        )

                        # Update execution span with success
                        exec_span.update(
                            output={"result": str(result)[:500]},
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