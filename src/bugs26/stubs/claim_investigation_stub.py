"""PLACEHOLDER Claim Investigation. The real CI subsystem (another team) replaces this."""
from ..integration.models import CIResult, Evidence, Finding, InvestigationRequest

PLACEHOLDER = "[PLACEHOLDER Claim Investigation] "


class StubClaimInvestigator:
    def investigate(self, request: InvestigationRequest) -> CIResult:
        finding = Finding(
            finding_id=f"{request.claim_id}-ci", report_id=request.report_id,
            source="claim_investigation", subject=request.claim_id, status="could_not_check",
            statement=PLACEHOLDER + f"Claim Investigation is not connected; could not check '{request.claim_text}'.",
            evidence=[Evidence(kind="note", ref="placeholder: CI not connected")])
        return CIResult(report_id=request.report_id, findings=[finding])
