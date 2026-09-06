#!/usr/bin/env python3
"""Zero-install launcher: run FlowSentry straight from a git clone.

  git clone https://github.com/vasilicasijarvis/flowsentry
  python3 flowsentry_cli.py scan ./workflows
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowsentry.scanner import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
