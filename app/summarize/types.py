from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedClaim:
    """One claim produced by a writer, citing the chunk it was grounded in."""

    text: str
    source_chunk_id: int
