#!/usr/bin/env python3
"""
Intelligent File Sampling Script
Samples files intelligently for large projects to optimize checking process
"""

import sys
import os
import random
import subprocess
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import argparse
import json

# Entry point patterns by language
ENTRY_POINT_PATTERNS = {
    'java': ['Main.java', 'Application.java', '*Application.java', 'main.java'],
    'python': ['main.py', '__main__.py', 'app.py', 'run.py', 'wsgi.py', 'asgi.py'],
    'javascript': ['index.js', 'main.js', 'app.js', 'server.js', 'start.js'],
    'typescript': ['index.ts', 'main.ts', 'app.ts', 'server.ts'],
    'go': ['main.go', 'main.go'],
    'csharp': ['Main.cs', 'Program.cs', 'Startup.cs'],
    'php': ['index.php', 'app.php'],
    'ruby': ['application.rb', 'server.rb'],
    'kotlin': ['Main.kt', 'Application.kt'],
}

# Core module patterns (business logic)
CORE_MODULE_PATTERNS = {
    'java': ['*Service.java', '*Controller.java', '*Repository.java', '*Dao.java', '*Entity.java', '*Model.java'],
    'python': ['*service.py', '*controller.py', '*model.py', '*dao.py', '*repository.py', '*handler.py'],
    'javascript': ['*service.js', '*controller.js', '*model.js', '*handler.js', '*repository.js'],
    'typescript': ['*service.ts', '*controller.ts', '*model.ts', '*handler.ts', '*repository.ts'],
    'go': ['*service.go', '*handler.go', '*controller.go', '*repository.go', '*model.go'],
    'csharp': ['*Service.cs', '*Controller.cs', '*Repository.cs', '*Model.cs'],
    'php': ['*Service.php', '*Controller.php', '*Model.php', '*Repository.php'],
    'ruby': ['*service.rb', '*controller.rb', '*model.rb', '*repository.rb'],
    'kotlin': ['*Service.kt', '*Controller.kt', '*Repository.kt', '*Model.kt'],
}

# Exclude directories
EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'dist', 'build', 'target', 'out', '.idea', '.vscode',
    'vendor', 'Pods', 'Carthage', '.gradle', '.vs', 'test', 'tests',
    '__tests__', 'spec', 'specs', 'docs', 'doc', 'examples', 'example',
    'samples', 'sample', 'benchmark', 'benchmarks', 'scripts', 'tools',
}

# Extension to language mapping
EXTENSION_MAP = {
    '.java': 'java',
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.cs': 'csharp',
    '.php': 'php',
    '.rb': 'ruby',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.rs': 'rust',
    '.swift': 'swift',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
}


@dataclass
class FileInfo:
    path: str
    language: str
    extension: str
    priority: int  # 0=entry, 1=core, 2=recent, 3=random
    reason: str
    last_modified: Optional[datetime] = None


def get_git_recent_files(project_path: str, days: int = 7) -> List[str]:
    """Get files modified in recent days using git"""
    try:
        # Check if git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return []

        # Get recent changes
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', '--name-only', '--pretty=format:', '--since', since_date],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return []

        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return files

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return []


def get_file_mtime(project_path: str, file_path: str) -> Optional[datetime]:
    """Get file modification time"""
    try:
        full_path = Path(project_path) / file_path
        if full_path.exists():
            return datetime.fromtimestamp(full_path.stat().st_mtime)
    except:
        pass
    return None


def matches_patterns(filename: str, patterns: List[str]) -> bool:
    """Check if filename matches any pattern"""
    from fnmatch import fnmatch
    for pattern in patterns:
        if fnmatch(filename, pattern):
            return True
    return False


def scan_project(project_path: str) -> Tuple[List[Dict], Dict[str, int]]:
    """Scan project and categorize files"""
    path = Path(project_path)
    if not path.exists():
        return [], {}

    all_files = []
    language_counts = Counter()

    for file_path in path.rglob('*'):
        if not file_path.is_file():
            continue
        if any(part.startswith('.') for part in file_path.parts):
            continue
        if any(exclude in file_path.parts for exclude in EXCLUDE_DIRS):
            continue

        ext = file_path.suffix.lower()
        if ext not in EXTENSION_MAP:
            continue

        language = EXTENSION_MAP[ext]
        language_counts[language] += 1

        all_files.append({
            'path': str(file_path.relative_to(path)),
            'language': language,
            'extension': ext,
            'filename': file_path.name,
        })

    return all_files, dict(language_counts)


def sample_smart(project_path: str, max_files: int, all_files: List[Dict]) -> List[FileInfo]:
    """Smart sampling: balanced mix of priorities"""
    main_language = max(EXTENSION_MAP.values(), key=lambda l: sum(1 for f in all_files if f['language'] == l))

    # Categorize files
    entry_files = []
    core_files = []
    recent_files = []
    other_files = []

    # Get recent files from git
    git_recent = set(get_git_recent_files(project_path, days=7))

    for f in all_files:
        lang = f['language']
        filename = f['filename']

        # Check entry point
        patterns = ENTRY_POINT_PATTERNS.get(lang, [])
        if matches_patterns(filename, patterns):
            entry_files.append(FileInfo(
                path=f['path'],
                language=lang,
                extension=f['extension'],
                priority=0,
                reason='entry_point'
            ))
            continue

        # Check core module
        patterns = CORE_MODULE_PATTERNS.get(lang, [])
        if matches_patterns(filename, patterns):
            core_files.append(FileInfo(
                path=f['path'],
                language=lang,
                extension=f['extension'],
                priority=1,
                reason='core_module'
            ))
            continue

        # Check recent
        if f['path'] in git_recent:
            recent_files.append(FileInfo(
                path=f['path'],
                language=lang,
                extension=f['extension'],
                priority=2,
                reason='recently_modified'
            ))
            continue

        other_files.append(FileInfo(
            path=f['path'],
            language=lang,
            extension=f['extension'],
            priority=3,
            reason='random_sample'
        ))

    # Calculate allocation
    total = len(all_files)
    if total <= max_files:
        # Return all if within limit
        result = entry_files + core_files + recent_files + other_files
        return result[:max_files]

    # Allocate percentages: entry 10%, core 40%, recent 30%, random 20%
    entry_alloc = max(5, min(len(entry_files), int(max_files * 0.10)))
    core_alloc = max(10, min(len(core_files), int(max_files * 0.40)))
    recent_alloc = max(5, min(len(recent_files), int(max_files * 0.30)))
    random_alloc = max_files - entry_alloc - core_alloc - recent_alloc

    # Select files
    selected = []

    # Entry points (all if few, sample if many)
    if len(entry_files) <= entry_alloc:
        selected.extend(entry_files)
    else:
        selected.extend(random.sample(entry_files, entry_alloc))

    # Core modules
    if len(core_files) <= core_alloc:
        selected.extend(core_files)
    else:
        selected.extend(random.sample(core_files, core_alloc))

    # Recent files
    if len(recent_files) <= recent_alloc:
        selected.extend(recent_files)
    else:
        selected.extend(random.sample(recent_files, recent_alloc))

    # Random sample for coverage
    if len(other_files) > random_alloc:
        selected.extend(random.sample(other_files, random_alloc))
    else:
        selected.extend(other_files)

    return selected[:max_files]


def sample_recent(project_path: str, max_files: int, all_files: List[Dict], days: int = 7) -> List[FileInfo]:
    """Sample based on recent git changes"""
    git_recent = get_git_recent_files(project_path, days=days)

    recent_by_lang = Counter()
    result = []

    for f in all_files:
        if f['path'] in git_recent:
            result.append(FileInfo(
                path=f['path'],
                language=f['language'],
                extension=f['extension'],
                priority=0,
                reason='git_recent',
                last_modified=get_file_mtime(project_path, f['path'])
            ))
            recent_by_lang[f['language']] += 1

    # If not enough recent files, add core modules
    if len(result) < max_files:
        remaining = max_files - len(result)
        main_lang = recent_by_lang.most_common(1)[0][0] if recent_by_lang else 'java'

        for f in all_files:
            if f['path'] not in git_recent:
                patterns = CORE_MODULE_PATTERNS.get(f['language'], [])
                if matches_patterns(f['filename'], patterns):
                    result.append(FileInfo(
                        path=f['path'],
                        language=f['language'],
                        extension=f['extension'],
                        priority=1,
                        reason='core_module_fallback'
                    ))
                    if len(result) >= max_files:
                        break

    return result[:max_files]


def sample_entry_points(project_path: str, max_files: int, all_files: List[Dict]) -> List[FileInfo]:
    """Sample only entry point files"""
    result = []

    for f in all_files:
        patterns = ENTRY_POINT_PATTERNS.get(f['language'], [])
        if matches_patterns(f['filename'], patterns):
            result.append(FileInfo(
                path=f['path'],
                language=f['language'],
                extension=f['extension'],
                priority=0,
                reason='entry_point'
            ))

    return result[:max_files]


def sample_core(project_path: str, max_files: int, all_files: List[Dict]) -> List[FileInfo]:
    """Sample only core module files"""
    result = []

    for f in all_files:
        patterns = CORE_MODULE_PATTERNS.get(f['language'], [])
        if matches_patterns(f['filename'], patterns):
            result.append(FileInfo(
                path=f['path'],
                language=f['language'],
                extension=f['extension'],
                priority=0,
                reason='core_module'
            ))

    return result[:max_files]


def sample_random(project_path: str, max_files: int, all_files: List[Dict]) -> List[FileInfo]:
    """Pure random sampling"""
    if len(all_files) <= max_files:
        return [FileInfo(
            path=f['path'],
            language=f['language'],
            extension=f['extension'],
            priority=0,
            reason='random'
        ) for f in all_files]

    sampled = random.sample(all_files, max_files)
    return [FileInfo(
        path=f['path'],
        language=f['language'],
        extension=f['extension'],
        priority=0,
        reason='random'
    ) for f in sampled]


def main():
    parser = argparse.ArgumentParser(description='Intelligent file sampling for large projects')
    parser.add_argument('project_path', help='Path to project directory')
    parser.add_argument('--strategy', choices=['smart', 'recent', 'entry-points', 'core', 'random'],
                        default='smart', help='Sampling strategy')
    parser.add_argument('--max-files', type=int, default=50, help='Maximum files to sample')
    parser.add_argument('--days', type=int, default=7, help='Days for recent strategy')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    args = parser.parse_args()

    # Scan project
    all_files, language_counts = scan_project(args.project_path)

    if not all_files:
        print(json.dumps({'error': 'No relevant files found'}, indent=2))
        sys.exit(1)

    # Sample based on strategy
    if args.strategy == 'smart':
        sampled = sample_smart(args.project_path, args.max_files, all_files)
    elif args.strategy == 'recent':
        sampled = sample_recent(args.project_path, args.max_files, all_files, args.days)
    elif args.strategy == 'entry-points':
        sampled = sample_entry_points(args.project_path, args.max_files, all_files)
    elif args.strategy == 'core':
        sampled = sample_core(args.project_path, args.max_files, all_files)
    else:
        sampled = sample_random(args.project_path, args.max_files, all_files)

    # Build output
    output = {
        'project_path': args.project_path,
        'strategy': args.strategy,
        'total_files_in_project': len(all_files),
        'language_distribution': language_counts,
        'sampled_count': len(sampled),
        'max_files_requested': args.max_files,
        'files': [
            {
                'path': f.path,
                'language': f.language,
                'priority': f.priority,
                'reason': f.reason,
            }
            for f in sampled
        ],
        'statistics': {
            'by_reason': Counter(f.reason for f in sampled),
            'by_language': Counter(f.language for f in sampled),
        }
    }

    if args.verbose:
        print(f"\n=== Sampling Report ===")
        print(f"Project: {args.project_path}")
        print(f"Strategy: {args.strategy}")
        print(f"Total files: {len(all_files)}")
        print(f"Sampled: {len(sampled)} / {args.max_files}")
        print(f"\nLanguage distribution:")
        for lang, count in language_counts.items():
            print(f"  {lang}: {count}")
        print(f"\nSample breakdown:")
        for reason, count in output['statistics']['by_reason'].items():
            print(f"  {reason}: {count}")

    # Output
    json_output = json.dumps(output, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(json_output, encoding='utf-8')
        print(f"Output saved to: {args.output}")
    else:
        print(json_output)


if __name__ == '__main__':
    main()