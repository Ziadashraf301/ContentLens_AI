from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from app.core.config import settings
import time
from typing import Optional, Dict, Any

_langfuse_client = None
_langfuse_callback = None


def init_langfuse():
    global _langfuse_client, _langfuse_callback

    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )

        # Create ONE callback instance
        _langfuse_callback = CallbackHandler(
        )


def get_langfuse_callback():
    return _langfuse_callback


def get_langfuse_client():
    """Get the Langfuse client for manual operations."""
    return _langfuse_client


class LangfuseTracer:
    """Enhanced tracer for agent observability."""

    def __init__(self):
        self.client = get_langfuse_client()
        self.callback = get_langfuse_callback()

    def start_trace(self, name: str, user_id: Optional[str] = None,
                   session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   tags: Optional[list] = None):
        """Start a new trace with metadata."""
        if not self.client:
            return None

        return self.client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            tags=tags or []
        )

    def log_generation(self, trace, name: str, model: str, prompt: str,
                      completion: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a generation (LLM call) with prompt and completion."""
        if not trace:
            return

        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(completion) // 4
        total_tokens = prompt_tokens + completion_tokens

        # Estimate cost (very rough, adjust based on your model pricing)
        # For Ollama models, cost is 0, but we can log estimated equivalent
        estimated_cost = total_tokens * 0.000001  # Example rate

        generation_metadata = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
            **(metadata or {})
        }

        generation = trace.generation(
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

    def add_score(self, trace_or_generation, name: str, value: float,
                 comment: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a score to a trace or generation."""
        if not trace_or_generation:
            return

        trace_or_generation.score(
            name=name,
            value=value,
            comment=comment,
            metadata=metadata or {}
        )

    def add_span(self, trace, name: str, input_data: Optional[Dict[str, Any]] = None,
                output_data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a span for agent operations."""
        if not trace:
            return

        span = trace.span(
            name=name,
            input=input_data or {},
            output=output_data or {},
            metadata=metadata or {}
        )
        return span

    def end_trace(self, trace):
        """End the trace."""
        if trace:
            trace.end()


def trace_agent_execution(agent_name: str, model_name: str):
    """Decorator for tracing agent executions."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            tracer = get_langfuse_tracer()
            if not tracer.client:
                return func(self, *args, **kwargs)

            # Start span for agent
            trace = tracer.start_trace(
                name=f"agent_{agent_name}",
                metadata={"agent": agent_name, "model": model_name},
                tags=[agent_name, "agent"]
            )

            if trace:
                span = tracer.add_span(
                    trace,
                    name=f"{agent_name}_execution",
                    input_data={"args": str(args), "kwargs": str(kwargs)},
                    metadata={"start_time": time.time()}
                )

            try:
                # Execute the agent
                result = func(self, *args, **kwargs)

                # Log the generation with prompt and completion
                prompt = getattr(self, 'template', 'No template available')
                if hasattr(self, 'prompt') and hasattr(self.prompt, 'template'):
                    prompt = self.prompt.template

                tracer.log_generation(
                    trace,
                    name=f"{agent_name}_llm_call",
                    model=model_name,
                    prompt=prompt,
                    completion=str(result),
                    metadata={"agent": agent_name}
                )

                # Validate and score
                from app.utils.output_validator import OutputValidator
                is_valid = OutputValidator.validate_agent_output(agent_name, result)
                tracer.add_score(
                    trace,
                    name=f"{agent_name}_validation",
                    value=1.0 if is_valid else 0.0,
                    comment="Output format validation"
                )

                # Update span
                if span:
                    span.metadata = {**span.metadata, "end_time": time.time(), "success": True}

                tracer.end_trace(trace)
                return result

            except Exception as e:
                # Log error
                if span:
                    span.metadata = {**span.metadata, "error": str(e), "success": False}
                tracer.end_trace(trace)
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
