#!/usr/bin/env python3
"""
HTML Report Generator
Generates interactive HTML compliance reports from the template
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def generate_html_report(
    project_name: str,
    language: str,
    spec_name: str,
    total_files: int,
    violations: List[Dict],
    categories: Dict[str, int],
    output_path: str,
    template_path: str = None,
    date: str = None
) -> None:
    """
    Generate HTML report from template

    Args:
        project_name: Project name
        language: Primary language
        spec_name: Specification document name
        total_files: Number of files checked
        violations: List of violation dicts with file, line, rule, severity, suggestion
        categories: Dict of category -> violation count
        output_path: Where to save the HTML file
        template_path: Path to report_template.html (optional, will search if not provided)
        date: Report date (optional, defaults to today)
    """
    # Find template
    if not template_path:
        # Search for template in skill assets
        search_paths = [
            Path(__file__).parent.parent / 'assets' / 'report_template.html',
            Path(__file__).parent / 'report_template.html',
            Path('assets/report_template.html'),
        ]
        for p in search_paths:
            if p.exists():
                template_path = str(p)
                break

    if not template_path or not Path(template_path).exists():
        print(f"Error: Template not found. Please provide --template path", file=sys.stderr)
        sys.exit(1)

    # Read template
    template = Path(template_path).read_text(encoding='utf-8')

    # Calculate statistics
    total_violations = len(violations)
    compliance_rate = 100 - (total_violations / max(total_files, 1) * 100) if total_files > 0 else 100
    compliance_rate = max(0, min(100, round(compliance_rate, 1)))

    # Determine severity class for stats card
    severity_class = "success" if compliance_rate >= 90 else "warning" if compliance_rate >= 70 else "danger"

    # Generate category rows
    category_rows = ""
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        percentage = round(count / total_violations * 100, 1) if total_violations > 0 else 0
        category_rows += f"""
        <tr>
            <td>{cat}</td>
            <td>{count}</td>
            <td>{percentage}%</td>
        </tr>
"""

    # Generate violation rows
    violation_rows = ""
    for v in violations:
        severity_tag = _get_severity_tag(v.get('severity', 'unknown'))
        row_class = "violation-row"
        if v.get('severity') in ['MANDATORY', 'mandatory', '强制']:
            row_class += " critical"

        file_path = v.get('file', 'unknown')
        line = v.get('line', '-')
        rule = v.get('rule', 'unknown')
        severity = v.get('severity', 'unknown')
        suggestion = v.get('suggestion', '')

        # Truncate long paths
        if len(file_path) > 50:
            file_path = "..." + file_path[-47:]

        violation_rows += f"""
        <tr class="{row_class}">
            <td><code>{file_path}</code></td>
            <td>{line}</td>
            <td>{rule}</td>
            <td>{severity_tag}</td>
            <td>{suggestion[:80] if len(suggestion) > 80 else suggestion}</td>
        </tr>
"""

    if not violation_rows:
        violation_rows = '<tr class="empty"><td colspan="5">No violations found</td></tr>'

    # Generate spec reference section
    spec_reference = ""
    if spec_name:
        spec_reference = f"""
        <div class="card">
            <div class="card-header" data-i18n="specReference">Specification Reference</div>
            <div class="card-body">
                <p>Checked against: <strong>{spec_name}</strong></p>
                <p>Rules parsed: Dynamic from specification document</p>
            </div>
        </div>
"""

    # Replace placeholders
    report_date = date or datetime.now().strftime('%Y-%m-%d')

    html = template.replace('{{PROJECT_NAME}}', project_name)
    html = html.replace('{{LANGUAGE}}', language)
    html = html.replace('{{SPEC_NAME}}', spec_name or 'Auto-detected')
    html = html.replace('{{DATE}}', report_date)
    html = html.replace('{{TOTAL_FILES}}', str(total_files))
    html = html.replace('{{TOTAL_VIOLATIONS}}', str(total_violations))
    html = html.replace('{{COMPLIANCE_RATE}}', str(compliance_rate))
    html = html.replace('{{SEVERITY_CLASS}}', severity_class)
    html = html.replace('{{CATEGORY_ROWS}}', category_rows)
    html = html.replace('{{VIOLATION_ROWS}}', violation_rows)
    html = html.replace('{{SPEC_REFERENCE}}', spec_reference)

    # Write output
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"HTML report saved to: {output_path}")


def _get_severity_tag(severity: str) -> str:
    """Get HTML tag for severity level"""
    severity_upper = severity.upper()
    if severity_upper in ['MANDATORY', '强制']:
        return '<span class="tag tag-danger">MANDATORY</span>'
    elif severity_upper in ['RECOMMENDED', '推荐']:
        return '<span class="tag tag-warning">RECOMMENDED</span>'
    elif severity_upper in ['REFERENCE', '参考']:
        return '<span class="tag tag-info">REFERENCE</span>'
    else:
        return '<span class="tag tag-info">UNKNOWN</span>'


def generate_from_json(json_path: str, output_path: str, template_path: str = None) -> None:
    """
    Generate HTML report from JSON analysis results

    Args:
        json_path: Path to JSON file with analysis results
        output_path: Where to save HTML
        template_path: Path to template (optional)
    """
    data = json.loads(Path(json_path).read_text(encoding='utf-8'))

    generate_html_report(
        project_name=data.get('project_name', 'Unknown'),
        language=data.get('language', 'Unknown'),
        spec_name=data.get('spec_name', ''),
        total_files=data.get('total_files', 0),
        violations=data.get('violations', []),
        categories=data.get('categories', {}),
        output_path=output_path,
        template_path=template_path,
        date=data.get('date')
    )


def main():
    parser = argparse.ArgumentParser(description='Generate HTML compliance report')
    parser.add_argument('--json', help='Generate from JSON results file')
    parser.add_argument('--output', required=True, help='Output HTML file path')
    parser.add_argument('--template', help='Template HTML file path')

    # Direct parameters (alternative to --json)
    parser.add_argument('--project', help='Project name')
    parser.add_argument('--language', help='Primary language')
    parser.add_argument('--spec', help='Specification name')
    parser.add_argument('--files', type=int, help='Total files checked')
    parser.add_argument('--violations-json', help='JSON file with violations list')
    parser.add_argument('--categories-json', help='JSON file with categories dict')
    parser.add_argument('--date', help='Report date')

    args = parser.parse_args()

    if args.json:
        generate_from_json(args.json, args.output, args.template)
    else:
        # Load violations and categories from JSON files if provided
        violations = []
        categories = {}

        if args.violations_json:
            violations = json.loads(Path(args.violations_json).read_text(encoding='utf-8'))
        if args.categories_json:
            categories = json.loads(Path(args.categories_json).read_text(encoding='utf-8'))

        generate_html_report(
            project_name=args.project or 'Unknown',
            language=args.language or 'Unknown',
            spec_name=args.spec or '',
            total_files=args.files or 0,
            violations=violations,
            categories=categories,
            output_path=args.output,
            template_path=args.template,
            date=args.date
        )


if __name__ == '__main__':
    main()