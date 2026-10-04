"""Targeted credential guard. Never prints matched text or credential values."""
import json
import re
import subprocess
import sys
from pathlib import Path

LITERAL = re.compile(r'''(?i)(?:api_key|ROBOFLOW_API_KEY)\s*[=:]\s*["']([^"'\r\n]+)["']''')
URL_KEY = re.compile(r'''(?i)[?&]api_key=([^\s&"'<>]+)''')
PLACEHOLDERS = {'your_api_key', 'your-key-here', 'api_key', 'xxx', 'placeholder', 'your_roboflow_api_key'}


def suspect(text):
    return any(m.group(1).lower() not in PLACEHOLDERS and len(m.group(1)) >= 16
               for pattern in (LITERAL, URL_KEY) for m in pattern.finditer(text))


def main():
    failed = False
    paths = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    for name in filter(None, paths):
        path = Path(name)
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b'\0' in raw:
            continue
        text = raw.decode('utf-8', errors='replace')
        locations = []
        if path.suffix == '.ipynb':
            try:
                notebook = json.loads(text)
            except json.JSONDecodeError:
                print(f'Invalid notebook: {name}')
                failed = True
                continue
            for index, cell in enumerate(notebook.get('cells', []), 1):
                # Serialized cell also scans outputs and metadata; joined source handles split lines.
                if suspect(''.join(cell.get('source', []))) or suspect(json.dumps(cell)):
                    locations.append(f'cell {index}')
        elif suspect(text):
            locations.append('file')
        if locations:
            print(f'Possible embedded credential: {name} ({", ".join(locations)})')
            failed = True
    print('Credential guard: FAIL' if failed else 'Credential guard: PASS')
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
