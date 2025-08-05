#!/usr/bin/env python3
"""
Debug script to check CDL template issues
"""

import sys
from pathlib import Path

def check_cdl_syntax(cdl_file):
    """Check CDL file for common syntax issues"""
    
    if not Path(cdl_file).exists():
        print(f"ERROR: CDL file not found: {cdl_file}")
        return False
    
    with open(cdl_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"CDL file: {cdl_file}")
    print(f"Total lines: {len(lines)}")
    print(f"File size: {len(content)} characters")
    print()
    
    # Check for missing closing brace
    if not content.strip().endswith('}'):
        print("ERROR: CDL file doesn't end with closing brace '}'")
        print("Last 5 lines:")
        for i, line in enumerate(lines[-5:], start=len(lines)-4):
            print(f"  {i:3d}: {line}")
        return False
    
    # Check for unmatched braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"Open braces: {open_braces}")
    print(f"Close braces: {close_braces}")
    
    if open_braces != close_braces:
        print("ERROR: Unmatched braces")
        return False
    
    # Check for template variables
    template_vars = []
    for line in lines:
        if '$' in line:
            # Find template variables
            import re
            vars_in_line = re.findall(r'\$(\w+)', line)
            template_vars.extend(vars_in_line)
    
    if template_vars:
        print(f"Template variables found: {set(template_vars)}")
    
    # Show last few lines
    print("\nLast 3 lines:")
    for i, line in enumerate(lines[-3:], start=len(lines)-2):
        print(f"  {i:3d}: {line}")
    
    print("\nCDL syntax appears OK")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_cdl.py <cdl_file>")
        sys.exit(1)
    
    check_cdl_syntax(sys.argv[1])
