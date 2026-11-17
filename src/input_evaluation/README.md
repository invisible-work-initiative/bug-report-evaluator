# Input Evaluation

Owners: Julian, Lurui (`#bugs26-evaluators`).

Put Input Evaluation code here. `placeholder.py` stands in until it exists; replace it when yours is ready.

To connect: write a class with an `evaluate(record)` method, following `InputEvaluator` in [integration/interfaces.py](../integration/interfaces.py). It takes an `IEReportRecord` and returns an `IEResult` (both in [integration/models.py](../integration/models.py)). Then tell Integration so it can make your class the default in `integration/pipeline.py`.
