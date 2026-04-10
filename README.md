# Spec-Analyzer Usage Guide

Automatically analyze project file types, match built-in specification documents, check code compliance, and generate violation reports.

**Enhanced with scalable architecture for large projects and large specification documents.**

## Design Philosophy

**Dynamic Specification Matching**: Not hardcoded rules, but:
1. Analyze project file types
2. Auto-match corresponding spec documents
3. Parse check rules from spec documents
4. Execute checks and generate reports

**Scalable Architecture**:
- Intelligent file sampling for large projects (>1000 files)
- Chunked parsing for large spec documents (>500 lines)
- Severity-based rule prioritization
- Batch processing for huge projects

---

## Install


Install the skill directly from GitHub:

```bash
npx skills add jclown/spec-analyzer-skill
```
---

## Quick Start

Use built-in default specification file for code compliance check
```
Check current project code standards
```

Use local specification file for code compliance check
```
Check current project code standards use @xxx.md
```

---

## Project Scale Detection

The skill automatically detects project scale and recommends appropriate strategy:

| Scale | Files | Strategy | Max Files |
|-------|-------|----------|-----------|
| Small | <100 | Full scan | All files |
| Medium | 100-500 | Priority sampling | 100 |
| Large | 500-1000 | Intelligent sampling | 50 |
| Huge | >1000 | Directory scope + batch | 30/batch |

---

## Sampling Strategies

For large projects, use intelligent file sampling:

| Strategy | Description | Best For |
|----------|-------------|----------|
| `smart` | Balanced mix (entry + core + recent + random) | General audit |
| `recent` | Git-based recent changes (last 7 days) | PR review |
| `entry-points` | Main entry files only (main.*, index.*) | Architecture review |
| `core` | Service/controller/model patterns | Business logic |
| `random` | Pure random sample | Coverage test |

### Sampling Commands

```bash
# Smart sampling (recommended)
python scripts/sample_files.py ./src --strategy smart --max-files 50

# Focus on recent changes
python scripts/sample_files.py ./src --strategy recent --days 7

# Entry points only
python scripts/sample_files.py ./src --strategy entry-points
```

---

## Spec Document Scale Detection

Large spec documents (>300 lines) are automatically chunked:

| Size | Lines | Strategy |
|------|-------|----------|
| Small | <200 | Read entire file |
| Medium | 200-500 | Indexed parsing |
| Large | >500 | Chunked parsing + severity priority |

### Rule Priority Order

Rules are checked in severity order:
1. `MANDATORY` / `【强制】` / `MUST` — Always check first
2. `RECOMMENDED` / `【推荐】` / `SHOULD` — Check if time permits
3. `REFERENCE` / `【参考】` / `MAY` — Optional, skip for quick audits

### Chunking Commands

```bash
# Create spec index
python scripts/chunk_spec.py large-spec.md output_index.json

# Filter by severity
python scripts/chunk_spec.py spec.md --severity MANDATORY --summary

# Filter by category
python scripts/chunk_spec.py spec.md --category "Naming"
```

---

## Specification Document Matching

### Language Matching

| Language | File Extensions | Match Files |
|----------|-----------------|-------------|
| Java | `.java` | `java-*.md`, `alibaba-*.md` |
| Python | `.py` | `python-*.md`, `pep8*.md` |
| JavaScript | `.js`, `.jsx` | `javascript-*.md`, `js-*.md` |
| TypeScript | `.ts`, `.tsx` | `typescript-*.md`, `ts-*.md` |
| Go | `.go` | `go-*.md`, `golang-*.md` |
| C | `.c`, `.h` | `c-*.md` |
| C++ | `.cpp`, `.hpp` | `cpp-*.md`, `c++-*.md` |
| C# | `.cs` | `csharp-*.md`, `dotnet-*.md` |
| PHP | `.php` | `php-*.md`, `psr-*.md` |
| Rust | `.rs` | `rust-*.md` |
| Ruby | `.rb` | `ruby-*.md` |
| Swift | `.swift` | `swift-*.md` |
| Kotlin | `.kt` | `kotlin-*.md` |

### Framework Matching

| Framework | Detection Condition | Match Files |
|-----------|--------------------|-------------|
| Spring | `pom.xml` contains spring | `spring-*.md` |
| Django | `settings.py` exists | `django-*.md` |
| React | `.jsx` files exist | `react-*.md` |
| Vue | `.vue` files exist | `vue-*.md` |
| Angular | `angular.json` exists | `angular-*.md` |

---

## Built-in Specifications

Located in `references/examples/`:

| File | Language | Lines | Size Category |
|------|----------|-------|---------------|
| `typescript-guidelines.md` | TypeScript | ~280 | Medium |
| `go-standards.md` | Go | ~330 | Medium |

**Adding Specs**: Add new files to `references/examples/`:
- Supported formats: `.md`, `.docx`, `.pdf`, `.txt`
- Naming convention: `<language>-*.md`

---

## Report Output

Two formats generated:

| File | Description |
|------|-------------|
| `compliance_report_YYYYMMDD.md` | Markdown report |
| `compliance_report_YYYYMMDD.html` | Visual HTML report |

### Report Structure

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

## Top Violations (by frequency)
| Rule | Occurrences | Example Files |

## Detailed Violations
| File | Line | Rule | Severity | Suggestion |
```

---

## Helper Scripts

### Analyze Project (with scale detection)

```bash
python scripts/analyze_project.py ./src --summary

# With max files limit
python scripts/analyze_project.py ./src --max-files 100

# With spec matching
python scripts/analyze_project.py ./src --examples-dir references/examples
```

### Sample Files (intelligent sampling)

```bash
# Smart sampling (balanced)
python scripts/sample_files.py ./src --strategy smart --max-files 50

# Recent changes only
python scripts/sample_files.py ./src --strategy recent --days 7

# Core modules only
python scripts/sample_files.py ./src --strategy core --max-files 30
```

### Chunk Spec Documents

```bash
# Create index for large spec
python scripts/chunk_spec.py spec.md output_index.json --summary

# Filter by severity
python scripts/chunk_spec.py spec.md --severity MANDATORY
```

### Parse Word Documents

```bash
pip install python-docx
python scripts/parse_docx.py spec.docx output.json
```

### Parse PDF Documents

```bash
pip install pdfplumber
python scripts/parse_pdf.py spec.pdf 1 50 output.json
```

---

## Specification Document Format

### Chinese Format

```markdown
### 1.1 Class Naming Convention
【强制】Class names must use UpperCamelCase style.

**反例**：
class userinfo {}

**正例**：
class UserInfo {}
```

### English Format

```markdown
### Class Names
**MUST** use UpperCamelCase style.

- Example: `UserInfo`
- Counter-example: `userinfo`
```

---

## Configuration Options

Specify via natural language or script parameters:

| Option | Description | Example |
|--------|-------------|---------|
| `--max-files` | Limit files to check | "check 50 files" |
| `--severity` | Focus on severity level | "only mandatory rules" |
| `--category` | Focus on rule category | "check naming rules only" |
| `--strategy` | Sampling strategy | "focus on recent changes" |
| `--directory` | Scope to directory | "check src/services only" |

---

## File Structure

```
spec-analyzer/
├── SKILL.md
├── README.md
├── scripts/
│   ├── analyze_project.py    (scale detection)
│   ├── sample_files.py       (intelligent sampling)
│   ├── chunk_spec.py         (spec chunking)
│   ├── parse_docx.py         (Word parsing)
│   └── parse_pdf.py          (PDF parsing)
├── references/
│   ├── spec-matching-rules.md
│   └── examples/
│       ├── typescript-guidelines.md
│       └── go-standards.md
└── assets/
    └── report_template.html
```

---

## Trigger Keywords

- `check project standards` / `analyze code against standards`
- `spec check` / `generate compliance report`
- `code audit` / `check against spec`
- `check coding standards` / `violation report`

---

## Performance Notes

1. Large projects use intelligent sampling - not full scan
2. Large specs use chunked parsing - not entire file load
3. Rule priority: MANDATORY > RECOMMENDED > REFERENCE
4. Batch processing for projects >1000 files
5. PDF parsing may be incomplete - prefer Markdown format
6. For best performance: combine sampling + severity filtering
