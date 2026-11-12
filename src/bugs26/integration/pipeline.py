"""The whole Integration flow, in memory, for one report."""
from typing import Optional

from . import assemble, intake, route
from .interfaces import ClaimInvestigator, InputEvaluator
from .models import IEResult, MaintainerOutput
from ..stubs.claim_investigation_stub import StubClaimInvestigator
from ..stubs.input_evaluation_stub import StubInputEvaluator


def run(text: str, source: str, repo_url: Optional[str] = None,
        title: Optional[str] = None, issue_url: Optional[str] = None,
        evaluator: Optional[InputEvaluator] = None,
        investigator: Optional[ClaimInvestigator] = None, **meta) -> MaintainerOutput:
    """receive (INT-1) -> structure + check (INT-2) -> IE (INT-3) -> CI per claim (INT-4) -> output (INT-5..8).
    meta: issue_number, labels, created_at, updated_at (GitHub). Raises PreparationError or InputEvaluationError;
    a Claim Investigation failure goes to could_not_check instead."""
    evaluator = evaluator or StubInputEvaluator()
    investigator = investigator or StubClaimInvestigator()
    raw = intake.receive(text, source, repo_url, title, issue_url, **meta)
    structured = intake.structure(raw)
    intake.verify_structured(raw, structured)
    record = intake.to_record(raw, structured)
    try:
        ie = IEResult.model_validate(evaluator.evaluate(record))  # a dict or a wrong shape fails here
        route.match_ie(raw, ie)
    except intake.InputEvaluationError:
        raise
    except Exception as e:
        raise intake.InputEvaluationError(f"Input Evaluation failed: {type(e).__name__}: {str(e)[:200]}") from None
    ci_results, notes, ci_requests = route.to_investigation(raw, ie, investigator)
    placeholders = [name for name, x in (("Input Evaluation", evaluator), ("Claim Investigation", investigator))
                    if getattr(x, "PLACEHOLDER", False)]
    return assemble.build_output(raw, record, ie, ci_requests, ci_results, notes, placeholders)
