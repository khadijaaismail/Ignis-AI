"""Send a minimal request to the configured LLM provider."""

import sys
from pathlib import Path

# Allow direct execution from the repository root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.adapter import LLMUnavailable, get_llm


def main() -> int:
    try:
        reply = get_llm().generate(
            "You are a connectivity check.",
            [{"role": "user", "content": "Reply with OK."}],
            max_tokens=20,
        )
    except LLMUnavailable as error:
        print(f"LLM unavailable: {error}")
        return 1
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
