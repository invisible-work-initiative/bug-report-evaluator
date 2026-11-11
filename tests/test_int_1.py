"""INT-1 Verification: submit a sample bug report and check that Integration receives it."""
import hashlib

from bugs26.integration import intake


def test_sample_report_is_received_verbatim(good):
    raw = intake.receive(good, "upload", "https://github.com/o/r")
    assert raw.original_text == good
    assert raw.sha256 == hashlib.sha256(good.encode()).hexdigest()
    assert raw.report_id and raw.source == "upload" and raw.repo_url == "https://github.com/o/r"


def test_each_submission_gets_its_own_id(good):
    assert intake.receive(good, "paste").report_id != intake.receive(good, "paste").report_id
