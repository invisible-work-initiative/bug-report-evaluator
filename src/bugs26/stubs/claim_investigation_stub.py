"""PLACEHOLDER Claim Investigation. The real CI subsystem (another team) replaces this."""
from ..integration.models import CIFinding, CIRequest, CIResult

PLACEHOLDER = "[PLACEHOLDER Claim Investigation] "


class StubClaimInvestigator:
    def investigate(self, request: CIRequest) -> CIResult:
        finding = CIFinding(
            claim_id=request.claim_id, outcome="insufficient evidence",
            explanation=PLACEHOLDER + f"Claim Investigation is not connected; could not check '{request.claim_text}'.")
        return CIResult(request_id=request.request_id, claim_id=request.claim_id, findings=[finding],
                        limitation=PLACEHOLDER + "no code was examined")
