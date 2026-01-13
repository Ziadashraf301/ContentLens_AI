from backend.app.agents.extractor import ExtractorAgent
from backend.app.agents.analyzer import AnalyzerAgent
from backend.app.core.config import settings


def test_agents_can_instantiate():
    """Smoke test: agents should be instantiable and provide a run method."""
    ex = ExtractorAgent()
    an = AnalyzerAgent()
    assert hasattr(ex, "run")
    assert hasattr(an, "run")


def test_config_defaults():
    """Ensure key config defaults are present and sensible."""
    assert settings.APP_NAME == "ContentLens_AI"
    assert isinstance(settings.MAX_FILE_SIZE_MB, int)
    assert settings.MAX_FILE_SIZE_MB >= 1
