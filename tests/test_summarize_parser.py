import pytest

from app.summarize.parser import ClaimParseError, parse_claims
from app.summarize.types import GeneratedClaim


def test_parses_one_claim_per_line():
    raw = "Inflation cooled in September. [12]\nThe central bank held rates steady. [7]"

    claims = parse_claims(raw)

    assert claims == [
        GeneratedClaim(text="Inflation cooled in September.", source_chunk_id=12),
        GeneratedClaim(text="The central bank held rates steady.", source_chunk_id=7),
    ]


def test_ignores_blank_lines():
    raw = "\n  \nOnly claim here. [1]\n\n"

    claims = parse_claims(raw)

    assert claims == [GeneratedClaim(text="Only claim here.", source_chunk_id=1)]


def test_raises_when_line_has_no_citation():
    with pytest.raises(ClaimParseError):
        parse_claims("A claim with no bracketed id at all.")


def test_raises_when_citation_is_not_an_integer():
    with pytest.raises(ClaimParseError):
        parse_claims("A claim with a bad id. [abc]")


def test_raises_when_nothing_parses():
    with pytest.raises(ClaimParseError):
        parse_claims("   \n   ")
