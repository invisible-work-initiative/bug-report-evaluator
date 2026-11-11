"""The whole Integration flow, in memory, for one report."""
from typing import Optional, Protocol

from . import assemble, intake, route
from .models import IEResult, MaintainerOutput, RawReport, StructuredReport
from .route import ClaimInvestigator
from ..stubs.claim_investigation_stub import StubClaimInvestigator
from ..stubs.input_evaluation_stub import StubInputEvaluator


class InputEvaluator(Protocol):
    """Interface Input Evaluation implements. Real IE code replaces the stub."""
    def evaluate(self, raw: RawReport, structured: StructuredReport) -> IEResult: ...


def run(text: str, source: str, repo_url: Optional[str] = None,
        evaluator: Optional[InputEvaluator] = None,
        investigator: Optional[ClaimInvestigator] = None) -> MaintainerOutput:
    """receive (INT-1) -> structure (INT-2) -> IE (INT-3) -> CI (INT-4) -> collect (INT-5,7,8) -> output (INT-6)."""
    evaluator = evaluator or StubInputEvaluator()
    investigator = investigator or StubClaimInvestigator()
    raw = intake.receive(text, source, repo_url)
    structured = intake.structure(raw)
    ie = evaluator.evaluate(raw, structured)
    ci = route.to_investigation(raw, structured, ie, investigator)
    findings = assemble.collect(raw.report_id, ie, ci)
    return assemble.build_output(raw.report_id, raw.sha256, findings)
