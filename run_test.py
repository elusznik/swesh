#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from tests.agents.test_interactive_shell_escape import test_shell_escape

if __name__ == "__main__":
    test_shell_escape()
    print("Test passed!")
