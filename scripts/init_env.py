"""Create .env from .env.example if it does not exist, and generate a Django secret key.

Never overwrites an existing .env. Prints nothing secret. Works on any OS with Python 3.
"""

import re
import secrets
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / ".env.example"
ENV = ROOT / ".env"


def main() -> int:
    if ENV.exists():
        print(".env already exists, leaving it untouched.")
        return 0
    if not EXAMPLE.exists():
        print("ERROR: .env.example not found.", file=sys.stderr)
        return 1
    shutil.copyfile(EXAMPLE, ENV)
    text = ENV.read_text()
    text = re.sub(
        r"(?m)^DJANGO_SECRET_KEY=.*$",
        lambda _: f"DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}",
        text,
    )
    ENV.write_text(text)
    print("Created .env with a freshly generated DJANGO_SECRET_KEY.")
    print("Next: set OPENROUTER_API_KEY and replace the remaining change-me values in .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
