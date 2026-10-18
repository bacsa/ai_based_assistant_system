from assistant_core import knowledge as K

def test_golden_questions_hit_expected_document(docs, glossary, golden):
    misses = [g["q"] for g in golden if not (K.search(g["q"], docs, glossary) or [{"doc": None}])[0]["doc"] == g["doc"]]
    assert misses == [], misses

def test_glossary_expansion_bridges_languages(docs, glossary):
    hits = K.search("When is the VAT return due?", docs, glossary)
    assert hits and hits[0]["doc"] == "vat-return-procedure"

def test_chunking_and_obligations():
    text = "Travel expenses must be submitted by the 10th of the following month.\n\nClaims open for more than 10 days are escalated.\n\n" + "A long sentence. " * 80
    chunks = K.chunk_text(text)
    assert len(chunks) >= 3 and all(len(c) <= 700 for c in chunks)
    ob = K.extract_obligations(text)
    assert {o["kind"] for o in ob} == {"time", "state"} and ob[0]["due"] == {"day_of_month": 10}

def test_low_coverage_is_low_confidence(docs, glossary):
    hits = K.search("What is the mileage reimbursement rate?", docs, glossary)
    assert not hits or K.confidence(hits[0]) < 0.58
