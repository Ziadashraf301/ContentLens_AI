from app.agents.extractor import ExtractorAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.recommender import RecommenderAgent
from app.core.config import settings


def test_agents_can_instantiate():
    """Smoke test: agents should be instantiable and provide a run method."""
    ex = ExtractorAgent()
    an = AnalyzerAgent()
    rec = RecommenderAgent()
    assert hasattr(ex, "run")
    assert hasattr(an, "run")
    assert hasattr(rec, "run")


def test_config_defaults():
    """Ensure key config defaults are present and sensible."""
    assert settings.APP_NAME == "ContentLens_AI"
    assert isinstance(settings.MAX_FILE_SIZE_MB, int)
    assert settings.MAX_FILE_SIZE_MB >= 1
