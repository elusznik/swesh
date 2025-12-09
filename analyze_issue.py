#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path

def find_potential_issues():
    """Look for potential issues in the codebase."""
    issues = []
    
    # Check for shell=True without proper validation
    for py_file in Path(".").rglob("*.py"):
        try:
            content = py_file.read_text()
            if "shell=True" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "shell=True" in line:
                        # Check if there's any input validation
                        context_start = max(0, i-5)
                        context_end = min(len(lines), i+5)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        # Look for user input patterns
                        if any(pattern in context.lower() for pattern in ['input', 'prompt', 'user']):
                            issues.append({
                                'file': str(py_file),
                                'line': i+1,
                                'issue': 'Potential shell injection with shell=True',
                                'context': context
                            })
        except Exception as e:
            pass
    
    return issues

def main():
    issues = find_potential_issues()
    if issues:
        print(f"Found {len(issues)} potential issue(s):")
        for issue in issues:
            print(f"\nFile: {issue['file']}:{issue['line']}")
            print(f"Issue: {issue['issue']}")
            print(f"Context:\n{issue['context']}")
            print("-" * 50)
    else:
        print("No potential issues found.")

if __name__ == "__main__":
    main()
