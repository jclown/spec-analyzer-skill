#!/usr/bin/env python3
"""
Specification Chunking Script
Creates an index and chunks for large specification documents to enable efficient parsing
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import argparse


@dataclass
class RuleInfo:
    id: str
    name: str
    category: str
    severity: str
    start_line: int
    end_line: int
    keywords: List[str]


@dataclass
class ChunkInfo:
    start_line: int
    end_line: int
    category: str
    rules: List[str]
    line_count: int


# Severity detection patterns
SEVERITY_PATTERNS = {
    'MANDATORY': [
        r'【强制】',
        r'\*\*MUST\*\*',
        r'\bMUST\b',
        r'禁止',
        r'不得',
        r'严禁',
        r'必须',
        r'禁止',
    ],
    'RECOMMENDED': [
        r'【推荐】',
        r'\*\*SHOULD\*\*',
        r'\bSHOULD\b',
        r'建议',
        r'推荐',
        r'最好',
    ],
    'REFERENCE': [
        r'【参考】',
        r'\*\*MAY\*\*',
        r'\bMAY\b',
        r'可选',
        r'参考',
    ]
}


def detect_severity(text: str) -> str:
    """Detect severity level from text"""
    for severity, patterns in SEVERITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return severity
    return 'UNKNOWN'


def extract_keywords(text: str) -> List[str]:
    """Extract key terms from rule text for quick matching"""
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Extract key terms
    keywords = []

    # Common patterns
    patterns = [
        r'(类名|class\s+name|ClassName)',  # Class naming
        r'(方法名|method\s+name|methodName)',  # Method naming
        r'(变量名|variable\s+name|varName)',  # Variable naming
        r'(常量|constant|CONST)',  # Constants
        r'(接口|interface)',  # Interface
        r'(包名|package)',  # Package
        r'(注释|comment)',  # Comments
        r'(缩进|indent)',  # Indentation
        r'(空格|space|blank)',  # Spaces
        r'(换行|newline|line\s+break)',  # Line breaks
        r'(括号|bracket|parenthesis)',  # Brackets
        r'(异常|exception|error)',  # Exceptions
        r'(日志|log)',  # Logging
        r'(密码|password|secret|key)',  # Security
        r'(SQL|sql)',  # SQL
        r'(注入|injection)',  # Injection
        r'(并发|concurrent|thread|goroutine)',  # Concurrency
        r'(测试|test|testing)',  # Testing
        r'(导入|import)',  # Imports
        r'(命名|naming)',  # Naming general
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keywords.append(match.group(1).lower())

    return keywords[:5]  # Limit to 5 keywords


def parse_spec_file(file_path: str, chunk_size: int = 50) -> Dict:
    """Parse specification file and create index with chunks"""

    path = Path(file_path)
    if not path.exists():
        return {'error': f'File not found: {file_path}'}

    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    total_lines = len(lines)

    # Parse rules
    rules = []
    chunks = []
    current_category = "General"
    current_chunk_start = 0
    current_chunk_rules = []

    i = 0
    while i < total_lines:
        line = lines[i]

        # Detect category changes (Chinese numerals or markdown headers)
        category_match = re.match(r'^[一二三四五六七八九十]+[、．.]\s*(.+)', line)
        if category_match:
            # Save previous chunk if has rules
            if current_chunk_rules:
                chunks.append(ChunkInfo(
                    start_line=current_chunk_start,
                    end_line=i - 1,
                    category=current_category,
                    rules=current_chunk_rules.copy(),
                    line_count=i - current_chunk_start
                ))
                current_chunk_rules = []
                current_chunk_start = i

            current_category = category_match.group(1).strip()

        # Also detect markdown headers as categories
        header_match = re.match(r'^##\s+(.+)', line)
        if header_match:
            if current_chunk_rules:
                chunks.append(ChunkInfo(
                    start_line=current_chunk_start,
                    end_line=i - 1,
                    category=current_category,
                    rules=current_chunk_rules.copy(),
                    line_count=i - current_chunk_start
                ))
                current_chunk_rules = []
                current_chunk_start = i

            current_category = header_match.group(1).strip()

        # Detect rules (numbered items or severity markers)
        severity = detect_severity(line)

        if severity != 'UNKNOWN' or re.match(r'^###?\s*\d+\.?\d*', line):
            # Extract rule ID
            rule_id_match = re.match(r'###?\s*(\d+\.?\d*)', line)
            if rule_id_match:
                rule_id = rule_id_match.group(1)
            else:
                rule_id = f"{len(rules) + 1}"

            # Find rule boundaries
            rule_start = i
            rule_end = i

            # Look ahead for rule content
            j = i + 1
            while j < total_lines:
                next_line = lines[j]
                # Stop at next rule or category
                if re.match(r'^###?\s*\d+\.?\d*', next_line) or \
                   re.match(r'^[一二三四五六七八九十]+[、．.]', next_line) or \
                   re.match(r'^##\s+', next_line) or \
                   detect_severity(next_line) != 'UNKNOWN':
                    rule_end = j - 1
                    break
                j += 1
                if j - i > 20:  # Max 20 lines per rule
                    rule_end = j - 1
                    break

            if rule_end == i:
                rule_end = min(i + 10, total_lines - 1)

            # Extract rule name and content
            rule_text = '\n'.join(lines[rule_start:rule_end + 1])
            rule_name = re.sub(r'^###?\s*\d+\.?\d*\s*', '', line)
            rule_name = re.sub(r'【[^】]+】', '', rule_name).strip()
            rule_name = rule_name[:50] if len(rule_name) > 50 else rule_name

            keywords = extract_keywords(rule_text)

            rule_info = RuleInfo(
                id=rule_id,
                name=rule_name,
                category=current_category,
                severity=severity,
                start_line=rule_start,
                end_line=rule_end,
                keywords=keywords
            )

            rules.append(rule_info)
            current_chunk_rules.append(rule_id)

            i = rule_end + 1
            continue

        i += 1

    # Save final chunk
    if current_chunk_rules:
        chunks.append(ChunkInfo(
            start_line=current_chunk_start,
            end_line=total_lines - 1,
            category=current_category,
            rules=current_chunk_rules,
            line_count=total_lines - current_chunk_start
        ))

    # Build statistics
    severity_counts = Counter(r.severity for r in rules)
    category_counts = Counter(r.category for r in rules)

    # Create keyword index for quick lookup
    keyword_index = {}
    for r in rules:
        for kw in r.keywords:
            if kw not in keyword_index:
                keyword_index[kw] = []
            keyword_index[kw].append(r.id)

    return {
        'file': file_path,
        'total_lines': total_lines,
        'total_rules': len(rules),
        'statistics': {
            'by_severity': dict(severity_counts),
            'by_category': dict(category_counts),
        },
        'keyword_index': keyword_index,
        'rules': [asdict(r) for r in rules],
        'chunks': [asdict(c) for c in chunks],
        'recommended_strategy': _recommend_strategy(total_lines, len(rules)),
    }


def _recommend_strategy(total_lines: int, total_rules: int) -> Dict:
    """Recommend parsing strategy based on size"""
    if total_lines < 200:
        return {
            'method': 'full_parse',
            'reason': 'Small document, read entire file',
            'estimated_tokens': total_lines * 2,
        }
    elif total_lines < 500:
        return {
            'method': 'indexed_parse',
            'reason': 'Medium document, use index then read sections',
            'estimated_tokens': 100 + total_rules * 10,
        }
    else:
        return {
            'method': 'chunked_parse',
            'reason': 'Large document, read chunks by priority',
            'estimated_tokens': 100 + total_rules * 5,
            'priority_order': ['MANDATORY', 'RECOMMENDED', 'REFERENCE'],
        }


def get_rules_by_severity(index: Dict, severity: str) -> List[RuleInfo]:
    """Filter rules by severity level"""
    return [r for r in index.get('rules', []) if r.get('severity') == severity]


def get_rules_by_category(index: Dict, category: str) -> List[RuleInfo]:
    """Filter rules by category"""
    return [r for r in index.get('rules', []) if r.get('category') == category]


def get_rules_by_keywords(index: Dict, keywords: List[str]) -> List[RuleInfo]:
    """Find rules matching keywords"""
    keyword_index = index.get('keyword_index', {})
    matched_ids = set()

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in keyword_index:
            matched_ids.update(keyword_index[kw_lower])

    return [r for r in index.get('rules', []) if r.get('id') in matched_ids]


def get_chunk_for_rule(index: Dict, rule_id: str) -> Optional[ChunkInfo]:
    """Find the chunk containing a specific rule"""
    for chunk in index.get('chunks', []):
        if rule_id in chunk.get('rules', []):
            return chunk
    return None


def main():
    parser = argparse.ArgumentParser(description='Chunk large specification documents for efficient parsing')
    parser.add_argument('spec_file', help='Path to specification file (.md)')
    parser.add_argument('--output', help='Output JSON index file')
    parser.add_argument('--chunk-size', type=int, default=50, help='Lines per chunk')
    parser.add_argument('--severity', choices=['MANDATORY', 'RECOMMENDED', 'REFERENCE', 'ALL'],
                        default='ALL', help='Filter by severity')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--keywords', help='Search by keywords (comma-separated)')
    parser.add_argument('--summary', action='store_true', help='Show summary only')

    args = parser.parse_args()

    # Parse spec file
    result = parse_spec_file(args.spec_file, args.chunk_size)

    if 'error' in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Apply filters if specified
    if args.severity != 'ALL':
        filtered_rules = get_rules_by_severity(result, args.severity)
        result['filtered_rules'] = [asdict(r) for r in filtered_rules]
        result['filter_applied'] = f"severity={args.severity}"

    if args.category:
        filtered_rules = get_rules_by_category(result, args.category)
        result['filtered_rules'] = [asdict(r) for r in filtered_rules]
        result['filter_applied'] = f"category={args.category}"

    if args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split(',')]
        filtered_rules = get_rules_by_keywords(result, keywords)
        result['filtered_rules'] = [asdict(r) for r in filtered_rules]
        result['filter_applied'] = f"keywords={args.keywords}"

    # Summary output
    if args.summary:
        print(f"\n=== Specification Index Summary ===")
        print(f"File: {args.spec_file}")
        print(f"Total lines: {result['total_lines']}")
        print(f"Total rules: {result['total_rules']}")
        print(f"\nBy Severity:")
        for sev, count in result['statistics']['by_severity'].items():
            print(f"  {sev}: {count}")
        print(f"\nBy Category:")
        for cat, count in result['statistics']['by_category'].items():
            print(f"  {cat}: {count}")
        print(f"\nChunks: {len(result['chunks'])}")
        print(f"Recommended strategy: {result['recommended_strategy']['method']}")
        return

    # Full output
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Index saved to: {args.output}")
        print(f"Total rules indexed: {result['total_rules']}")
    else:
        print(output)


if __name__ == '__main__':
    main()