import pytest

from app.summarize.types import GeneratedClaim
from app.summarize.validator import UngroundedClaimError, validate_claims


def test_passes_when_every_claim_cites_a_retrieved_chunk():
    claims = [
        GeneratedClaim(text="a", source_chunk_id=1),
        GeneratedClaim(text="b", source_chunk_id=2),
    ]

    validate_claims(claims, {1, 2, 3})


def test_raises_when_a_claim_cites_an_invented_id():
    claims = [
        GeneratedClaim(text="a", source_chunk_id=1),
        GeneratedClaim(text="made up", source_chunk_id=999),
    ]

    with pytest.raises(UngroundedClaimError):
        validate_claims(claims, {1, 2, 3})


def test_passes_on_empty_claims():
    validate_claims([], {1, 2, 3})
