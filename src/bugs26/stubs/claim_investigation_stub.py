"""PLACEHOLDER Claim Investigation. The real CI subsystem (another team) replaces this."""
from ..integration.models import CIResult, Evidence, Finding, InvestigationRequest

PLACEHOLDER = "[PLACEHOLDER Claim Investigation] "


class StubClaimInvestigator:
    def investigate(self, request: InvestigationRequest) -> CIResult:
        loc = request.location
        evidence = (Evidence(kind="report_excerpt", ref=f"report:{request.report_id}", excerpt=request.claim_text,
                             start=loc["start"], end=loc["end"]) if loc else
                    Evidence(kind="note", ref=f"report:{request.report_id}", excerpt="placeholder: CI not connected"))
        finding = Finding(
            finding_id=f"{request.claim_id}-ci", report_id=request.report_id,
            source="claim_investigation", subject=request.claim_text, status="could_not_check",
            statement=PLACEHOLDER + f"Claim Investigation is not connected; could not check '{request.claim_text}'.",
            evidence=[evidence])
        return CIResult(report_id=request.report_id, findings=[finding],
                        not_checked=["Claim Investigation is a placeholder: no code was examined"])
