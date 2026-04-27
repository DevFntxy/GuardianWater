import re
from collections import defaultdict

with open('pylint_report.txt', 'r', encoding='utf-16') as f:
    text = f.read()

issues = defaultdict(list)
for line in text.split('\n'):
    line = line.strip()
    match = re.match(r'^([^:]+):(\d+):(\d+):\s*([A-Z0-9]+):\s*(.*)', line)
    if match:
        file, l, c, code, desc = match.groups()
        issues[file].append((l, c, code, desc))

total = 0
for file, file_issues in issues.items():
    print(f"\n{file}: {len(file_issues)} issues")
    for l, c, code, desc in file_issues:
        print(f"  Line {l}: {code} - {desc}")
    total += len(file_issues)
print(f"\nTotal issues: {total}")
