# Specification Document Matching Rules

This document defines how specification documents are matched based on project file types.

---

## Language Matching

### File Extension Mapping

| Language | Extensions | Match Patterns |
|----------|------------|----------------|
| Java | `.java` | `java-*.md`, `alibaba-*.md`, `java-*.docx`, `java-*.pdf` |
| Python | `.py` | `python-*.md`, `pep8*.md`, `pep-*.md`, `python-*.docx` |
| JavaScript | `.js`, `.jsx`, `.mjs` | `javascript-*.md`, `js-*.md`, `eslint-*.md`, `js-*.docx` |
| TypeScript | `.ts`, `.tsx` | `typescript-*.md`, `ts-*.md`, `ts-*.docx`, `typescript-*.pdf` |
| Go | `.go` | `go-*.md`, `golang-*.md`, `go-*.docx`, `go-*.pdf` |
| C | `.c`, `.h` | `c-*.md`, `c-language-*.md`, `c-*.docx` |
| C++ | `.cpp`, `.hpp`, `.cc` | `cpp-*.md`, `c++-*.md`, `cpp-*.docx` |
| C# | `.cs` | `csharp-*.md`, `c#-*.md`, `dotnet-*.md`, `csharp-*.docx` |
| PHP | `.php` | `php-*.md`, `psr-*.md`, `php-*.docx` |
| Rust | `.rs` | `rust-*.md`, `rust-*.docx`, `rust-*.pdf` |
| Ruby | `.rb` | `ruby-*.md`, `rails-*.md`, `ruby-*.docx` |
| Swift | `.swift` | `swift-*.md`, `swift-*.docx`, `swift-*.pdf` |
| Kotlin | `.kt`, `.kts` | `kotlin-*.md`, `android-*.md`, `kotlin-*.docx` |
| Scala | `.scala` | `scala-*.md`, `scala-*.docx` |
| Vue | `.vue` | `vue-*.md`, `vue-*.docx` |
| React | `.jsx`, `.tsx` | `react-*.md`, `react-*.docx` |

### Matching Priority

When multiple matching files exist, select in this order:

1. **User-specified file** — explicitly provided by user
2. **Language-prefixed file** — filename contains primary language name (e.g., `java-coding-standards.md`)
3. **First alphabetical match** — the first file when sorted alphabetically

### Multi-Language Projects

Projects with multiple languages get matched specs for each:

| Scenario | Matching Behavior |
|----------|-------------------|
| Java primary (60%) + Python secondary (40%) | Match `java-*.md` + `python-*.md` |
| TypeScript + React framework | Match `typescript-*.md` + `react-*.md` |
| Mixed frontend/backend | Match separate specs per language |

---

## Framework/Library Matching

Framework specifications are matched in addition to language specs (layered, not replacement).

### Framework Detection Conditions

| Framework | Detection Condition | Match Patterns |
|-----------|--------------------|----------------|
| Spring | `pom.xml` or `build.gradle` contains `spring` | `spring-*.md` |
| Spring Boot | `pom.xml` contains `spring-boot-starter` | `springboot-*.md`, `spring-*.md` |
| Django | `settings.py` or `manage.py` exists | `django-*.md` |
| Flask | Python files + `flask` in imports | `flask-*.md` |
| React | `.jsx` files exist | `react-*.md` |
| Vue | `.vue` files exist | `vue-*.md` |
| Angular | `angular.json` exists | `angular-*.md` |
| Flutter | `pubspec.yaml` exists | `flutter-*.md` |
| Node.js | `package.json` exists (no frontend framework) | `nodejs-*.md` |
| Express | `package.json` contains `express` | `express-*.md` |
| Next.js | `package.json` contains `next` | `nextjs-*.md` |
| NestJS | `package.json` contains `@nestjs` | `nestjs-*.md` |
| FastAPI | Python files + `fastapi` in imports | `fastapi-*.md` |

### Framework Spec Layering

Framework specs are **applied on top of language specs**, not as replacements:

| Project Type | Applied Specs |
|--------------|---------------|
| Java + Spring | `java-*.md` + `spring-*.md` |
| JavaScript + React | `javascript-*.md` + `react-*.md` |
| TypeScript + Angular | `typescript-*.md` + `angular-*.md` |
| Python + Django | `python-*.md` + `django-*.md` |

---

## Universal Specification Matching

These specs apply to all projects and are always checked if present.

### Security Specifications

**Match Patterns**: `security-*.md`, `secure-*.md`

**Always Applies**: All projects

**Typical Checks**:
- Hardcoded passwords/credentials
- SQL injection vulnerabilities
- XSS vulnerabilities
- Sensitive data exposure
- Authentication/authorization flaws

### Database Specifications

**Match Patterns**: `database-*.md`, `mysql-*.md`, `sql-*.md`, `postgresql-*.md`, `mongodb-*.md`

**Applies When**:
- `.sql` files exist
- Code contains SQL statements or ORM queries
- Database configuration files exist

### API Specifications

**Match Patterns**: `api-*.md`, `rest-*.md`, `openapi-*.md`, `graphql-*.md`

**Applies When**:
- API route files exist (`routes/`, `controllers/`, `api/`)
- OpenAPI/Swagger definitions exist
- GraphQL schema files exist

### Logging Specifications

**Match Patterns**: `logging-*.md`, `log-*.md`

**Applies When**: All projects with logging code

### Testing Specifications

**Match Patterns**: `testing-*.md`, `test-*.md`

**Applies When**: Test files exist (`*_test.*`, `*Test.*`, `tests/`)

---

## Matching Workflow

```
Step 1: Scan Project
    → Collect all file extensions
    → Count files per language
    ↓
Step 2: Identify Primary Language
    → Language with most files
    → Record secondary languages (>10% of files)
    ↓
Step 3: Match Language Specs
    → Search examples/ directory
    → Found → Add to spec list
    → Not found → Log warning, continue
    ↓
Step 4: Detect Frameworks
    → Check for framework-specific files
    → Check imports/dependencies
    ↓
Step 5: Match Framework Specs
    → Search examples/ directory
    → Found → Add to spec list (layered)
    → Not found → Skip
    ↓
Step 6: Match Universal Specs
    → security-*.md (always)
    → database-*.md (if SQL files)
    → api-*.md (if API files)
    ↓
Step 7: Return Spec List
    → Ordered by priority: user > language > framework > universal
```

---

## Adding Custom Specifications

### Naming Convention

```
<language>-<description>.md      # Language-specific
<framework>-<description>.md     # Framework-specific
<category>-<description>.md      # Universal/category
```

**Examples**:
- `java-company-standards.md` — Company-specific Java rules
- `spring-security.md` — Spring framework security rules
- `security-hardening.md` — General security hardening
- `database-mysql.md` — MySQL-specific database rules

### Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Markdown | `.md` | **Recommended** — most accurate parsing |
| Word | `.docx` | Requires `python-docx` library |
| PDF | `.pdf` | Requires `pdfplumber` library |
| Plain Text | `.txt` | Basic text parsing |

### Placement Location

Place specification files in the skill's examples directory:

```
spec-analyzer/references/examples/
├── typescript-guidelines.md     # Built-in
├── go-standards.md              # Built-in
├── java-mycompany.md            # Your custom spec ←
├── security-owasp.md            # Your custom spec ←
└── ...
```

---

## Spec Size Categories

| Category | Lines | Parsing Strategy |
|----------|-------|------------------|
| Small | <200 | Full file read |
| Medium | 200-500 | Indexed parsing |
| Large | >500 | Chunked parsing with priority |

Large specs (>300 lines) should be pre-chunked using `scripts/chunk_spec.py` for efficient parsing.