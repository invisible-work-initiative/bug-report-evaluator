"""INT-5 Verification: check that Integration receives findings from both subsystems."""
from bugs26.integration import pipeline


def test_findings_from_both_subsystems(good):
    out = pipeline.run(good, "paste")
    sources = {f.source for f in out.findings}
    assert sources == {"input_evaluation", "claim_investigation"}
