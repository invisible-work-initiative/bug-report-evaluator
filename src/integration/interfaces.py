"""The two interfaces other subsystems implement (see documentation/interfaces/). Pass them to pipeline.run().
Transport: in-process Python call, provisional pending the IE transport decision (target 2026-11-24)."""
from typing import Protocol

from .models import CIRequest, CIResult, IEReportRecord, IEResult


class InputEvaluator(Protocol):
    """INT-3: gets one report record (original raw_body + sections), returns the IE v1 evaluation result."""
    def evaluate(self, record: IEReportRecord) -> IEResult: ...


class ClaimInvestigator(Protocol):
    """INT-4: gets one claim with its context, returns the result for that claim."""
    def investigate(self, request: CIRequest) -> CIResult: ...
