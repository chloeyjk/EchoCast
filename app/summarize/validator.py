from app.summarize.types import GeneratedClaim


class UngroundedClaimError(ValueError):
    """Raised when a claim cites a chunk id outside the retrieved set."""


def validate_claims(claims: list[GeneratedClaim], allowed_chunk_ids: set[int]) -> None:
    """Reject any claim whose source_chunk_id was not among the retrieved chunks."""
    for claim in claims:
        if claim.source_chunk_id not in allowed_chunk_ids:
            raise UngroundedClaimError(
                f"claim cites chunk {claim.source_chunk_id}, which is not in the retrieved set"
            )
