import re

from app.summarize.types import GeneratedClaim

CLAIM_LINE = re.compile(r"^(?P<text>.+?)\s*\[(?P<chunk_id>\d+)\]$")


class ClaimParseError(ValueError):
    """Raised when LLM output can't be parsed into cited claims."""


def parse_claims(raw_text: str) -> list[GeneratedClaim]:
    """Parse one claim per non-blank line, each ending in a `[chunk_id]` citation."""
    claims = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = CLAIM_LINE.match(line)
        if not match:
            raise ClaimParseError(f"line does not end with a [chunk_id] citation: {line!r}")
        claims.append(
            GeneratedClaim(text=match.group("text").strip(), source_chunk_id=int(match.group("chunk_id")))
        )

    if not claims:
        raise ClaimParseError("no claims parsed from writer output")
    return claims
