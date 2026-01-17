from app.agents.extractor import ExtractorAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.recommender import RecommenderAgent
from app.agents.ideation import IdeationAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.compliance import ComplianceAgent
from app.core.config import settings


def test_agents_can_instantiate():
    """Smoke test: agents should be instantiable and provide a run method."""
    ex = ExtractorAgent()
    an = AnalyzerAgent()
    rec = RecommenderAgent()
    ide = IdeationAgent()
    copy = CopywriterAgent()
    comp = ComplianceAgent()

    assert hasattr(ex, "run")
    assert hasattr(an, "run")
    assert hasattr(rec, "run")
    assert hasattr(ide, "run")
    assert hasattr(copy, "run")
    assert hasattr(comp, "run")


def test_compliance_agent_blocks_spam():
    ca = ComplianceAgent()
    res = ca.run("This campaign will spam users and sell personal data")
    assert isinstance(res, dict)
    assert res["status"] == "block"
    assert any(
    "spam" in i["match"] or "sell personal" in i["match"]
    for i in res["issues"]
    )


def test_config_defaults():
    """Ensure key config defaults are present and sensible."""
    assert settings.APP_NAME == "ContentLens_AI"
    assert isinstance(settings.MAX_FILE_SIZE_MB, int)
    assert settings.MAX_FILE_SIZE_MB >= 1
