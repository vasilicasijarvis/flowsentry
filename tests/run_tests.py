#!/usr/bin/env python3
"""Zero-dependency test runner for FlowSentry.

Runs free test_* functions from tests/test_rules.py and unittest.TestCase
classes from tests/test_cli.py. Also compatible with pytest.

Usage: python3 tests/run_tests.py
"""

import os
import sys
import traceback
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import test_rules  # noqa: E402
import test_cli  # noqa: E402


def main():
    passed, failed = 0, 0

    # free functions (test_rules style)
    free = [(name, fn) for name, fn in sorted(vars(test_rules).items())
            if name.startswith("test_") and callable(fn)]
    for name, fn in free:
        try:
            fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"\nFAIL: {name}\n{traceback.format_exc()}")

    # unittest TestCase classes (test_cli style)
    suite = unittest.TestLoader().loadTestsFromModule(test_cli)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    passed += result.testsRun - len(result.failures) - len(result.errors)
    failed += len(result.failures) + len(result.errors)

    print(f"FlowSentry test suite: {passed} passed, {failed} failed "
          f"(of {passed + failed} tests)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
