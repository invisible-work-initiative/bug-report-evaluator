"""INT-9 Verification (inspection, automated): stored data and logs do not link a reporter across submissions."""
import re
from pathlib import Path

from bugs26.integration import models, pipeline

SRC = Path(models.__file__).resolve().parents[1]
IDENTITY = re.compile(r"author|reporter|user|username|login|email|ip_addr", re.I)


def test_no_model_has_an_identity_field():
    for cls in (models.RawReport, models.StructuredReport, models.Finding, models.Evidence,
                models.InvestigationRequest, models.IEResult, models.CIResult, models.MaintainerOutput):
        for name in cls.model_fields:
            assert not IDENTITY.search(name), f"{cls.__name__}.{name}"


def test_output_has_no_identity_keys(good):
    out = pipeline.run(good, "paste").model_dump(mode="json")

    def keys(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from keys(v)
        elif isinstance(x, list):
            for i in x:
                yield from keys(i)
    assert not [k for k in keys(out) if IDENTITY.search(k)]


def test_two_submissions_share_no_identifier(good):
    a, b = pipeline.run(good, "paste"), pipeline.run(good, "paste")
    assert a.report_id != b.report_id
    ids_a = {a.report_id, *(f.finding_id for f in a.findings)}
    ids_b = {b.report_id, *(f.finding_id for f in b.findings)}
    assert not ids_a & ids_b


def test_code_neither_logs_nor_writes_files():
    for py in SRC.rglob("*.py"):
        code = py.read_text(encoding="utf-8")
        assert "import logging" not in code and "print(" not in code, py
        assert not re.search(r"\bopen\(|write_text|write_bytes|sqlite|shelve|pickle", code), py
