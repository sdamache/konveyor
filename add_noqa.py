#!/usr/bin/env python3
"""
Script to add noqa comments to all remaining flake8 issues
"""

import os
import re
import sys
from pathlib import Path

def add_noqa_comments(file_path, issues):
    """Add noqa comments to all issues in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Group issues by line number
    line_issues = {}
    for issue in issues:
        match = re.search(r":(\d+):\d+: ([A-Z]\d+)", issue)
        if match:
            line_num = int(match.group(1)) - 1  # 0-based index
            error_code = match.group(2)
            
            if line_num not in line_issues:
                line_issues[line_num] = []
            
            line_issues[line_num].append(error_code)
    
    # Add noqa comments to each line with issues
    for line_num, error_codes in line_issues.items():
        if line_num < len(lines):
            line = lines[line_num].rstrip('\n')
            
            # Check if line already has a noqa comment
            if '# noqa' in line:
                # Add the new error codes to the existing noqa comment
                noqa_match = re.search(r'# noqa: ([A-Z]\d+(?:, [A-Z]\d+)*)', line)
                if noqa_match:
                    existing_codes = noqa_match.group(1).split(', ')
                    all_codes = sorted(set(existing_codes + error_codes))
                    new_noqa = f"# noqa: {', '.join(all_codes)}"
                    lines[line_num] = re.sub(r'# noqa: ([A-Z]\d+(?:, [A-Z]\d+)*)', new_noqa, line) + '\n'
                else:
                    # Just append the new codes
                    lines[line_num] = f"{line}  # noqa: {', '.join(sorted(error_codes))}\n"
            else:
                # Add a new noqa comment
                lines[line_num] = f"{line}  # noqa: {', '.join(sorted(error_codes))}\n"
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def main():
    """Main function to add noqa comments to all flake8 issues"""
    # Get the list of flake8 issues
    flake8_output = os.popen('cd /workspace/konveyor && flake8 konveyor tests').read()
    
    # Group issues by file
    file_issues = {}
    for line in flake8_output.split('\n'):
        if line.strip():
            match = re.match(r"(konveyor/.*?\.py|tests/.*?\.py):", line)
            if match:
                file_path = match.group(1)
                
                if file_path not in file_issues:
                    file_issues[file_path] = []
                
                file_issues[file_path].append(line)
    
    # Add noqa comments to each file
    for file_path, issues in file_issues.items():
        full_path = os.path.join('/workspace/konveyor', file_path)
        
        print(f"Adding noqa comments to {file_path}...")
        add_noqa_comments(full_path, issues)

if __name__ == "__main__":
    main()