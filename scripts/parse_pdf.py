#!/usr/bin/env python3
"""
PDF Document Parser
Parse .pdf format specification documents
"""

import sys
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class Severity(Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


@dataclass
class SpecRule:
    """Specification rule data structure"""
    id: str
    name: str
    category: str
    content: str
    severity: str
    positive_example: Optional[str] = None
    negative_example: Optional[str] = None


def install_dependency(package: str) -> bool:
    """
    Automatically install missing dependency package
    Returns True if installation succeeds, False otherwise
    """
    try:
        print(f"Installing dependency: {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"Successfully installed {package}")
            return True
        else:
            print(f"Failed to install {package}: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"Installation timed out for {package}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error installing {package}: {e}", file=sys.stderr)
        return False


def parse_pdf(file_path: str, start_page: int = 1, end_page: int = None, auto_install: bool = True) -> Dict:
    """
    Parse PDF document

    Args:
        file_path: PDF file path
        start_page: Start page number (1-based)
        end_page: End page number (None means last page)
        auto_install: Whether to automatically install missing dependencies

    Returns:
        Dict containing parsed rules and metadata
    """
    # Try pdfplumber first (better results)
    try:
        import pdfplumber
        return _parse_with_pdfplumber(file_path, start_page, end_page)
    except ImportError:
        if auto_install:
            if install_dependency("pdfplumber"):
                try:
                    import pdfplumber
                    return _parse_with_pdfplumber(file_path, start_page, end_page)
                except ImportError:
                    pass  # Fall through to PyPDF2

        # Fall back to PyPDF2
        try:
            from PyPDF2 import PdfReader
            return _parse_with_pypdf2(file_path, start_page, end_page)
        except ImportError:
            if auto_install:
                if install_dependency("PyPDF2"):
                    try:
                        from PyPDF2 import PdfReader
                        return _parse_with_pypdf2(file_path, start_page, end_page)
                    except ImportError:
                        return {
                            'error': 'Failed to import PDF parsing library even after installation',
                            'fallback': 'Please convert PDF to Markdown format, or use online tools to extract text'
                        }

            return {
                'error': 'PDF parsing library not installed',
                'install_options': [
                    'pip install pdfplumber (recommended)',
                    'pip install PyPDF2'
                ],
                'fallback': 'Please convert PDF to Markdown format, or use online tools to extract text'
            }


def _parse_with_pdfplumber(file_path: str, start_page: int, end_page: int) -> Dict:
    """Parse PDF using pdfplumber library"""
    import pdfplumber

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        end_page = end_page or total_pages

        text_content = []
        for i in range(start_page - 1, min(end_page, total_pages)):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                text_content.append({
                    'page': i + 1,
                    'text': text
                })

    return _process_extracted_text(file_path, text_content)


def _parse_with_pypdf2(file_path: str, start_page: int, end_page: int) -> Dict:
    """Parse PDF using PyPDF2 library"""
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    end_page = end_page or total_pages

    text_content = []
    for i in range(start_page - 1, min(end_page, total_pages)):
        page = reader.pages[i]
        text = page.extract_text()
        if text:
            text_content.append({
                'page': i + 1,
                'text': text
            })

    return _process_extracted_text(file_path, text_content)


def _process_extracted_text(file_path: str, text_content: List[Dict]) -> Dict:
    """Process extracted text content"""
    # Merge all text
    full_text = '\n\n'.join([t['text'] for t in text_content])

    # Parse rules
    rules = _extract_rules_from_text(full_text)
    categories = _extract_categories_from_text(full_text)

    return {
        'file': file_path,
        'total_pages': len(text_content),
        'total_rules': len(rules),
        'categories': categories,
        'rules': [asdict(r) for r in rules],
        'raw_text_preview': full_text[:1000] + '...' if len(full_text) > 1000 else full_text
    }


def _extract_categories_from_text(text: str) -> Dict[str, List[str]]:
    """Extract categories from text"""
    categories = {}
    lines = text.split('\n')

    current_category = "General"
    rule_ids = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect category headings (Chinese numeral prefixes)
        if re.match(r'^[一二三四五六七八九十]+[、．.]', line):
            if rule_ids:
                categories[current_category] = rule_ids
            current_category = re.sub(r'^[一二三四五六七八九十]+[、．.]?\s*', '', line)
            rule_ids = []
        elif re.match(r'^\d+\.\s+.+', line):
            # Possible rule ID
            match = re.match(r'^(\d+)', line)
            if match:
                rule_ids.append(match.group(1))

    if rule_ids:
        categories[current_category] = rule_ids

    return categories


def _extract_rules_from_text(text: str) -> List[SpecRule]:
    """Extract rules from text"""
    rules = []
    lines = text.split('\n')

    current_category = "General"
    rule_counter = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Detect category
        if re.match(r'^[一二三四五六七八九十]+[、．.]', line):
            current_category = re.sub(r'^[一二三四五六七八九十]+[、．.]?\s*', '', line)
            i += 1
            continue

        # Detect severity level
        severity = _detect_severity(line)
        if severity != Severity.UNKNOWN.value:
            rule_counter += 1

            # Extract rule ID
            rule_id_match = re.match(r'(\d+\.?\d*)', line)
            rule_id = rule_id_match.group(1) if rule_id_match else f"{rule_counter}"

            # Extract content
            content = re.sub(r'^(\d+\.?\d*\s*)?', '', line)
            content = re.sub(r'^【[^】]+】', '', content).strip()

            rule = SpecRule(
                id=rule_id,
                name=content[:50] if len(content) > 50 else content,
                category=current_category,
                content=content,
                severity=severity
            )
            rules.append(rule)

        i += 1

    return rules


def _detect_severity(text: str) -> str:
    """Detect severity level from text"""
    # Chinese markers
    if '【强制】' in text:
        return Severity.MANDATORY.value
    if '【推荐】' in text:
        return Severity.RECOMMENDED.value
    if '【参考】' in text:
        return Severity.REFERENCE.value
    # English markers
    if re.search(r'\bMUST\b', text, re.IGNORECASE):
        return Severity.MANDATORY.value
    if re.search(r'\bSHOULD\b', text, re.IGNORECASE):
        return Severity.RECOMMENDED.value
    if re.search(r'\bMAY\b', text, re.IGNORECASE):
        return Severity.REFERENCE.value
    # Keyword detection (Chinese)
    for kw in ['禁止', '不得', '不要', '严禁', '必须']:
        if kw in text:
            return Severity.MANDATORY.value
    for kw in ['建议', '推荐', '最好']:
        if kw in text:
            return Severity.RECOMMENDED.value
    return Severity.UNKNOWN.value


def get_pdf_info(file_path: str, auto_install: bool = True) -> Dict:
    """Get PDF file information"""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            return {
                'pages': len(pdf.pages),
                'metadata': pdf.metadata
            }
    except ImportError:
        if auto_install:
            if install_dependency("pdfplumber"):
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        return {
                            'pages': len(pdf.pages),
                            'metadata': pdf.metadata
                        }
                except:
                    pass

        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return {
                'pages': len(reader.pages),
                'metadata': reader.metadata
            }
        except ImportError:
            if auto_install:
                if install_dependency("PyPDF2"):
                    try:
                        from PyPDF2 import PdfReader
                        reader = PdfReader(file_path)
                        return {
                            'pages': len(reader.pages),
                            'metadata': reader.metadata
                        }
                    except:
                        pass
        return {'error': 'Unable to read PDF file'}


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <pdf_file> [start_page] [end_page] [output_file]")
        print("Options:")
        print("  --no-auto-install    Disable automatic dependency installation")
        print("\nExamples:")
        print("  python parse_pdf.py spec.pdf")
        print("  python parse_pdf.py spec.pdf 1 10 output.json")
        sys.exit(1)

    file_path = sys.argv[1]
    start_page = 1
    end_page = None
    output_path = None
    auto_install = True

    # Parse arguments
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--no-auto-install':
            auto_install = False
        elif not arg.startswith('--'):
            if i == 0:
                start_page = int(arg)
            elif i == 1:
                end_page = int(arg)
            elif i == 2:
                output_path = arg

    result = parse_pdf(file_path, start_page, end_page, auto_install)

    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        if 'install_options' in result:
            print("Install options:", file=sys.stderr)
            for opt in result['install_options']:
                print(f"  {opt}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        Path(output_path).write_text(output, encoding='utf-8')
        print(f"Parsing complete: {result['total_pages']} pages, {result['total_rules']} rules")
    else:
        print(output)


if __name__ == '__main__':
    main()