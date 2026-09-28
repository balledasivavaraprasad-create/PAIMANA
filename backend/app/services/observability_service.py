import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.config.logging import logger

class MockLangfuseSpan:
    def __init__(self, name: str, input_data: Optional[Dict[str, Any]] = None):
        self.name = name
        self.input = input_data
        self.output = None
        self.status = "success"
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def end(self, output: Any = None, status: str = "success"):
        self.output = output
        self.status = status
        return self

    def update(self, output: Any = None, status: str = "success"):
        self.output = output
        self.status = status
        return self

class MockLangfuseGeneration:
    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.output = kwargs.get("completion") or kwargs.get("output_text") or None
        self.status = "success"

    def end(self, output: Any = None, status: str = "success"):
        self.output = output
        self.status = status
        return self

    def update(self, output: Any = None, status: str = "success"):
        self.output = output
        self.status = status
        return self

class MockLangfuseTrace:
    def __init__(self, trace_id: str, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.trace_id = trace_id
        self.name = name
        self.metadata = metadata or {}
        self.spans = []
        self.generations = []
        self.status = "success"
        self.output = None

    def span(self, name: str, input_data: Optional[Dict[str, Any]] = None, **kwargs):
        s = MockLangfuseSpan(name=name, input_data=input_data)
        self.spans.append(s)
        return s

    def generation(self, name: str, *args, **kwargs):
        g = MockLangfuseGeneration(name=name, *args, **kwargs)
        self.generations.append(g)
        return g

    def update(self, output: Any = None, status: str = "success"):
        self.status = status
        self.output = output

class ObservabilityService:
    def __init__(self):
        self.enabled = False
        self.client = None
        self.init_client()

    def init_client(self):
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
        if public_key and secret_key:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(public_key=public_key, secret_key=secret_key)
                self.enabled = True
                logger.info("Langfuse Observability initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Langfuse client: {e}. Falling back to mock trace.")
                self.enabled = False

    def start_trace(self, name: str, project_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        Creates a new trace. If Langfuse is offline or missing, creates a MockLangfuseTrace.
        Guarantees: An observability outage NEVER crashes agent execution or project monitoring.
        """
        trace_id = f"trace-{int(datetime.now(timezone.utc).timestamp()*1000)}"
        meta = metadata or {}
        if project_id:
            meta["project_id"] = project_id

        if self.enabled and self.client:
            try:
                return self.client.trace(id=trace_id, name=name, metadata=meta)
            except Exception as e:
                logger.warning(f"Langfuse start_trace failed: {e}. Graceful fallback.")
                return MockLangfuseTrace(trace_id=trace_id, name=name, metadata=meta)

        return MockLangfuseTrace(trace_id=trace_id, name=name, metadata=meta)

    def trace_tool_execution(self, trace: Any, tool_name: str, input_args: Any, output_res: Any, error: Optional[str] = None):
        """Records a tool invocation safely."""
        try:
            if hasattr(trace, "span"):
                span = trace.span(name=f"tool:{tool_name}", input_data={"args": input_args})
                if error and isinstance(span, dict):
                    span["status"] = "error"
                    span["error"] = error
        except Exception as e:
            logger.warning(f"Observability trace_tool error: {e}")

observability = ObservabilityService()
