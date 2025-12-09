#!/usr/bin/env python3
import sys
import os

def fix_test_file():
    """Fix the incomplete test file."""
    test_file = "tests/agents/test_interactive_shell_escape.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Remove the incomplete first with block and the pass statement
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        if 'with patch("minisweagent.agents.interactive.PromptSession")' in lines[i]:
            # Skip this entire block until we find a line that's not indented
            while i < len(lines) and (lines[i].startswith(' ') or lines[i].startswith('\t') or lines[i] == ''):
                i += 1
            # Skip the empty line after the block
            if i < len(lines) and lines[i] == '':
                i += 1
        else:
            new_lines.append(lines[i])
            i += 1
    
    # Join back
    fixed_content = '\n'.join(new_lines)
    
    # Write back
    with open(test_file, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {test_file}")
    
    # Also create a simple test runner
    runner_content = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from tests.agents.test_interactive_shell_escape import test_shell_escape

if __name__ == "__main__":
    test_shell_escape()
    print("Test passed!")
'''
    
    with open("run_test.py", 'w') as f:
        f.write(runner_content)
    
    print("Created test runner: run_test.py")

if __name__ == "__main__":
    fix_test_file()
