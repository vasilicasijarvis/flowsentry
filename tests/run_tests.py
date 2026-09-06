#!/usr/bin/env python3
"""Zero-dependency test runner for FlowSentry.

Runs every test_* function in tests/test_rules.py (also compatible with pytest).
Usage: python3 tests/run_tests.py
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import test_rules  # noqa: E402


def main():
    tests = [(name, fn) for name, fn in sorted(vars(test_rules).items())
             if name.startswith("test_") and callable(fn)]
    passed, failed = [], []
    for name, fn in tests:
        try:
            fn()
            passed.append(name)
        except Exception:
            failed.append((name, traceback.format_exc()))
    print(f"FlowSentry test suite: {len(passed)} passed, {len(failed)} failed "
          f"(of {len(tests)} tests)")
    for name, tb in failed:
        print(f"\nFAIL: {name}\n{tb}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
