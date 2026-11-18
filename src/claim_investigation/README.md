# Claim Investigation

Owners: Boyu, Qinyue (`#bugs26-investigators`).

Put Claim Investigation code here. `placeholder.py` stands in until it exists; replace it when yours is ready.

To connect: write a class with an `investigate(request)` method, following `ClaimInvestigator` in [integration/interfaces.py](../integration/interfaces.py). It takes a `CIRequest` and returns a `CIResult` (both in [integration/models.py](../integration/models.py)). Then tell Integration so it can make your class the default in `integration/pipeline.py`.
