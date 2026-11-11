"""The two interfaces other subsystems implement (see documentation/interfaces/). Pass them to pipeline.run()."""
from typing import Protocol

from .models import CIResult, IEResult, InvestigationRequest, RawReport, StructuredReport


class InputEvaluator(Protocol):
    """INT-3: gets the original and the structured report, returns decision, findings and requests."""
    def evaluate(self, raw: RawReport, structured: StructuredReport) -> IEResult: ...


class ClaimInvestigator(Protocol):
    """INT-4: gets one request (with context), returns findings and what it could not check."""
    def investigate(self, request: InvestigationRequest) -> CIResult: ...
