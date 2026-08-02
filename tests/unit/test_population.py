from population import CandidateArchive, LineageGraph, ParetoSelector
from providers import CandidateProposal


def candidate(candidate_id: str, **metrics: float) -> CandidateProposal:
    return CandidateProposal(
        candidate_id=candidate_id,
        provider="mock",
        configuration="config",
        skill={"name": "skill"},
        capabilities=["package.propose:ffmpeg"],
        metrics=metrics,
    )


def test_pareto_selector_preserves_tradeoffs() -> None:
    secure = candidate("secure", success=0.8, security=1.0, novelty=0.3, cost=0.2)
    capable = candidate("capable", success=1.0, security=0.8, novelty=0.5, cost=0.3)
    dominated = candidate("dominated", success=0.5, security=0.5, novelty=0.1, cost=0.9)
    assert {
        item.candidate_id for item in ParetoSelector.frontier([secure, capable, dominated])
    } == {
        "secure",
        "capable",
    }
    assert ParetoSelector.select([secure, capable, dominated]).candidate_id == "secure"


def test_archive_and_lineage_are_queryable() -> None:
    parent = candidate("parent", success=0.8)
    child = parent.model_copy(update={"candidate_id": "child", "parent_id": "parent"})
    archive = CandidateArchive()
    archive.add(parent)
    archive.add(child)
    graph = LineageGraph()
    graph.add(parent)
    graph.add(child)
    assert archive.get("child") == child
    assert graph.ancestors("child") == ["parent"]
