"""PLACEHOLDER Claim Investigation. The real CI subsystem (another team) replaces this.
It invents no outcome: every call fails, so Integration lists each claim as not investigated."""
from ..integration.models import CIRequest, CIResult


class StubClaimInvestigator:
    PLACEHOLDER = True

    def investigate(self, request: CIRequest) -> CIResult:
        raise NotImplementedError("Claim Investigation not connected (placeholder)")
