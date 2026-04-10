---
name: spec-analyzer
description: Analyze project code compliance against specification documents and generate violation reports. Use when users mention code standards, compliance checking, code audit, spec checking, or code quality. Trigger scenarios: 'check code standards', 'analyze code standards', 'code audit', 'generate compliance report', 'check against spec', 'violation report', 'code quality issues', 'compliance analysis', 'coding standards check', 'check project against spec'. Even without explicit 'spec' keywords, consider using when code quality checking is involved.
---

# Specification Document Analyzer

Automatically match specification documents based on project file types, check code compliance, and generate violation reports.

## Core Philosophy

**Dynamic Rule Parsing**: Rules are not hardcoded. Instead:
1. Analyze Project → Identify file types
2. Match Specs → User-specified or auto-discovered
3. Parse Rules → Extract from spec documents
4. Execute Checks → Apply rules to code
5. Generate Reports → Markdown + HTML

---

## Scalability Strategy

For large projects (>1000 files) or large spec documents (>500 lines), use intelligent strategies:

### Large Projects

| Strategy | When to Use | Method |
|----------|-------------|--------|
| **Sampling** | Files > 500 | Use `scripts/sample_files.py` for intelligent selection |
| **Directory Scope** | Monorepo structure | Focus on specific subdirectories |
| **Severity Filtering** | Quick audit | Check only MANDATORY rules first |
| **Batch Processing** | Files > 1000 | Process in batches, generate incremental reports |
| **Change-Based** | Recent work | Focus on recently modified files (git-based) |

**Sampling Priority** (handled by `scripts/sample_files.py`):
1. Entry point files (main.*, index.*, app.*)
2. Recently modified files (last 7 days)
3. Core module files (service, controller, model patterns)
4. Random sample for coverage

### Large Spec Documents

| Strategy | When to Use | Method |
|----------|-------------|--------|
| **Rule Index** | Spec > 300 lines | Use `scripts/chunk_spec.py` to create index |
| **Severity Priority** | Any size | Check MANDATORY → RECOMMENDED → REFERENCE |
| **Category Focus** | Targeted audit | Focus on specific rule categories |
| **Chunked Parsing** | Spec > 500 lines | Parse spec in sections, not entire file |

**Rule Priority Order**:
1. `MANDATORY` / `【强制】` / `MUST` — Always check these first
2. `RECOMMENDED` / `【推荐】` / `SHOULD` — Check if time permits
3. `REFERENCE` / `【参考】` / `MAY` — Optional, skip for quick audits

---

## Execution Flow

### 1. Analyze Project Scale

First determine project size to choose strategy:

```python
# Run via script
python scripts/analyze_project.py ./src --max-files 100
```

**Scale Classification**:
- Small (<100 files): Full scan
- Medium (100-500 files): Priority sampling
- Large (>500 files): Intelligent sampling + batch processing
- Huge (>1000 files): Directory scope + batch processing

**Output**: `project_analysis.json` with file list, language stats, and recommended strategy.

### 2. Get Specification Documents

Priority order:
1. **User-specified** → Use the provided path directly
2. **Auto-match** → Search in `references/examples/`
3. **Not found** → Log warning, skip that language, note in report

For large specs, create a rule index first:
```bash
python scripts/chunk_spec.py large-spec.md output_index.json
```

### 3. Parse Specification (Scalable)

**Small Spec (<300 lines)**: Read entire file, parse all rules.

**Large Spec (>300 lines)**:
1. Run `scripts/chunk_spec.py` to create rule index
2. Read index to get rule categories and counts
3. Parse only relevant sections based on priority

**Rule Index Structure**:
```json
{
  "total_rules": 85,
  "by_severity": {"MANDATORY": 30, "RECOMMENDED": 40, "REFERENCE": 15},
  "by_category": {"Naming": 15, "Formatting": 20, ...},
  "chunks": [
    {"start_line": 1, "end_line": 50, "rules": ["1.1", "1.2"]}
  ]
}
```

### 4. Select Files for Checking

**Small Project**: Check all relevant files.

**Large Project**: Use `scripts/sample_files.py`:

```bash
# Intelligent sampling
python scripts/sample_files.py ./src --strategy smart --max-files 50

# Focus on recent changes
python scripts/sample_files.py ./src --strategy recent --days 7

# Entry points only
python scripts/sample_files.py ./src --strategy entry-points
```

**Sampling Strategies**:
| Strategy | Description | Best For |
|----------|-------------|----------|
| `smart` | Balanced mix of all priorities | General audit |
| `recent` | Git-based recent changes | PR review |
| `entry-points` | Main entry files only | Architecture review |
| `random` | Pure random sample | Coverage test |
| `core` | Service/controller/model patterns | Business logic |

### 5. Execute Checks

Apply parsed rules to selected files:

**Naming conventions** → Grep for naming patterns (fast)
**Formatting rules** → Read sample files, check patterns
**Security rules** → Grep for sensitive patterns (fast)
**Comment rules** → Read sample files, check patterns

**Batch Mode** for large projects:
- Process files in batches of 50
- Generate intermediate results
- Aggregate into final report

### 6. Generate Reports

Create a `compliance-results/` folder in the target project directory with:

```
<project>/
└── compliance-results/
    ├── compliance_report_YYYYMMDD.md
    └── compliance_report_YYYYMMDD.html
```

**Report Formats**:
- **Markdown**: `compliance_report_YYYYMMDD.md` — Detailed text report
- **HTML**: `compliance_report_YYYYMMDD.html` — Interactive visual report

**IMPORTANT: Always generate BOTH Markdown AND HTML reports.** Users expect both formats.

#### HTML Report Generation Process

The skill must generate HTML reports using the template in `assets/report_template.html`:

1. **Collect all analysis results** into a structured format:
   ```python
   results = {
       'project_name': 'MyProject',
       'language': 'java',
       'spec_name': 'alibaba-java-guide.md',
       'total_files': 50,
       'violations': [
           {'file': 'src/Main.java', 'line': 10, 'rule': '1.1', 'severity': 'MANDATORY', 'suggestion': 'Rename class'}
       ],
       'categories': {'Naming': 5, 'Formatting': 3}
   }
   ```

2. **Run the HTML generator script**:
   ```bash
   python scripts/generate_html_report.py --json results.json --output compliance-results/compliance_report_20260410.html
   ```

   Or generate directly with parameters:
   ```bash
   python scripts/generate_html_report.py \
       --project "MyProject" \
       --language "java" \
       --spec "alibaba-java-guide.md" \
       --files 50 \
       --violations-json violations.json \
       --categories-json categories.json \
       --output compliance-results/compliance_report_20260410.html
   ```

3. **The script automatically**:
   - Reads the template from `assets/report_template.html`
   - Replaces all placeholders ({{PROJECT_NAME}}, {{VIOLATION_ROWS}}, etc.)
   - Generates violation table with severity tags
   - Calculates compliance rate and category statistics
   - Writes the final HTML to the output path

#### Template Placeholders

The HTML template uses these placeholders that the generator script fills:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PROJECT_NAME}}` | Project name | MyProject |
| `{{LANGUAGE}}` | Primary language | java |
| `{{SPEC_NAME}}` | Spec document name | alibaba-java-guide.md |
| `{{DATE}}` | Report date | 2026-04-10 |
| `{{TOTAL_FILES}}` | Files checked | 50 |
| `{{TOTAL_VIOLATIONS}}` | Total violations | 15 |
| `{{COMPLIANCE_RATE}}` | Compliance percentage | 85 |
| `{{SEVERITY_CLASS}}` | Stats card color class | danger/warning/success |
| `{{CATEGORY_ROWS}}` | Category table rows | HTML table rows |
| `{{VIOLATION_ROWS}}` | Violation table rows | HTML table rows |
| `{{SPEC_REFERENCE}}` | Spec info section | HTML card |

#### Report Generation Checklist

When completing an analysis, ensure:

- [ ] Created `compliance-results/` directory in project root
- [ ] Generated `compliance_report_YYYYMMDD.md` with full violation details
- [ ] Generated `compliance_report_YYYYMMDD.html` using the template
- [ ] Both files contain the same data (markdown for detailed reading, HTML for interactive viewing)
- [ ] HTML report includes severity filtering and search functionality
- [ ] Compliance rate calculated correctly

**Report Generation Steps**:
1. Create `compliance-results/` directory in the project root
2. Generate Markdown report with full violation details
3. Generate HTML report using the template with placeholder replacement
4. Include summary statistics and categorized violations

---

## Specification Document Format

### Chinese Specs

```markdown
### 1.1 Class Naming Convention
【强制】Class names must use UpperCamelCase style.

**反例**：
class userinfo {}

**正例**：
class UserInfo {}
```

### English Specs

```markdown
### Class Names
**MUST** use UpperCamelCase style.

- Example: `UserInfo`
- Counter-example: `userinfo`
```

**Severity markers**:
- Chinese: `【强制】` / `【推荐】` / `【参考】`
- English: `MUST` / `SHOULD` / `MAY`

---

## Usage Examples

### Quick Audit (Large Project)

```
Quick audit of large project against Java spec, focus on mandatory rules
```
→ Sample 50 files, check only MANDATORY rules, fast report

### Full Audit (Small Project)

```
Check current project code standards
```
→ Full scan, all rules, detailed report

### PR Review (Recent Changes)

```
Check recent code changes against company spec
```
→ Focus on files modified in last 7 days

### Targeted Audit

```
Check security rules in src/services
```
→ Specific directory + specific rule category

---

## Script Tools

Located in `scripts/`:

```bash
# Analyze project (with scale detection)
python scripts/analyze_project.py ./src --max-files 100

# Intelligent file sampling
python scripts/sample_files.py ./src --strategy smart --max-files 50

# Chunk large spec documents
python scripts/chunk_spec.py large-spec.md output_index.json

# Parse Word (for large docs, use chunking)
python scripts/parse_docx.py spec.docx output.json

# Parse PDF (with page range)
python scripts/parse_pdf.py spec.pdf 1 50 output.json

# Generate HTML report from template
python scripts/generate_html_report.py --json results.json --output report.html
```

**HTML Report Generator** (`scripts/generate_html_report.py`):
- Reads template from `assets/report_template.html`
- Accepts JSON input with analysis results
- Replaces placeholders automatically
- Generates interactive HTML with filtering and search

---

## Built-in Specifications

Located in `references/examples/`:
| File | Language | Lines |
|------|----------|-------|
| `typescript-guidelines.md` | TypeScript | ~280 |
| `go-standards.md` | Go | ~330 |

---

## Output Report Structure

Reports are generated in `<project>/compliance-results/` directory:

```
<project>/
└── compliance-results/
    ├── compliance_report_20260410.md
    └── compliance_report_20260410.html
```

### Markdown Report Template

```markdown
# Code Compliance Analysis Report

**Project**: [name] | **Language**: [lang] | **Date**: YYYY-MM-DD
**Strategy**: [Full/Sampling/Batch] | **Files Checked**: X of Y

## Summary
- Violations: Y (MANDATORY: A, RECOMMENDED: B)
- Compliance Rate: Z%
- Coverage: X% of project files

## By Severity
| Severity | Violations | % of Total |
|----------|------------|------------|

## By Category
| Category | Violations | Top Files |
|----------|------------|-----------|

## Top Violations (by frequency)
| Rule | Occurrences | Example Files |
|------|-------------|---------------|

## Detailed Violations
| File | Line | Rule | Severity | Suggestion |
|------|------|------|----------|------------|
```

### HTML Report

Generated from `assets/report_template.html` with:
- Interactive search and filter
- Language toggle (EN/中文)
- Severity-based filtering
- Category breakdown

---

## Configuration Options

Users can specify via natural language or parameters:

| Option | Description | Example |
|--------|-------------|---------|
| `--max-files` | Limit files to check | "check 50 files" |
| `--severity` | Focus on severity level | "only mandatory rules" |
| `--category` | Focus on rule category | "check naming rules only" |
| `--strategy` | Sampling strategy | "focus on recent changes" |
| `--directory` | Scope to directory | "check src/services only" |

---

## Notes

1. Large projects use intelligent sampling - not full scan
2. Large specs use chunked parsing - not entire file load
3. Rule priority: MANDATORY > RECOMMENDED > REFERENCE
4. Batch processing for projects >1000 files
5. PDF parsing may be incomplete - prefer Markdown format
6. For best performance: combine sampling + severity filtering