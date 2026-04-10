#!/usr/bin/env python3
"""
Project Analysis Script
Scans project directory, identifies file types, matches specification documents
Enhanced with scale detection and large project support
"""

import sys
import json
import argparse
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import subprocess
from datetime import datetime, timedelta

# File extension to language mapping
EXTENSION_MAP = {
    '.java': 'java',
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cs': 'csharp',
    '.php': 'php',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.vue': 'vue',
}

# Language to spec file pattern mapping
SPEC_FILE_MAP = {
    'java': ['java-*.md', 'alibaba-*.md'],
    'python': ['python-*.md', 'pep8*.md', 'pep-*.md'],
    'javascript': ['javascript-*.md', 'js-*.md', 'eslint-*.md'],
    'typescript': ['typescript-*.md', 'ts-*.md'],
    'go': ['go-*.md', 'golang-*.md'],
    'c': ['c-*.md'],
    'cpp': ['cpp-*.md', 'c++-*.md'],
    'csharp': ['csharp-*.md', 'c#-*.md', 'dotnet-*.md'],
    'php': ['php-*.md', 'psr-*.md'],
    'rust': ['rust-*.md'],
    'ruby': ['ruby-*.md', 'rails-*.md'],
    'swift': ['swift-*.md'],
    'kotlin': ['kotlin-*.md', 'android-*.md'],
    'scala': ['scala-*.md'],
    'vue': ['vue-*.md'],
}

# Exclude directories
EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'dist', 'build', 'target', 'out', '.idea', '.vscode',
    'vendor', 'Pods', 'Carthage', '.gradle', '.vs',
    'test', 'tests', '__tests__', 'spec', 'specs',
    'docs', 'doc', 'examples', 'example', 'samples', 'sample',
    'benchmark', 'benchmarks', 'scripts', 'tools',
}

# Scale thresholds
SCALE_THRESHOLDS = {
    'small': 100,
    'medium': 500,
    'large': 1000,
    'huge': 5000,
}


@dataclass
class ProjectScale:
    category: str  # small, medium, large, huge
    total_files: int
    recommended_strategy: str
    max_files_suggestion: int
    batch_size: Optional[int] = None


def detect_scale(total_files: int) -> ProjectScale:
    """Detect project scale and recommend strategy"""
    if total_files < SCALE_THRESHOLDS['small']:
        return ProjectScale(
            category='small',
            total_files=total_files,
            recommended_strategy='full_scan',
            max_files_suggestion=total_files
        )
    elif total_files < SCALE_THRESHOLDS['medium']:
        return ProjectScale(
            category='medium',
            total_files=total_files,
            recommended_strategy='priority_sampling',
            max_files_suggestion=min(100, total_files)
        )
    elif total_files < SCALE_THRESHOLDS['large']:
        return ProjectScale(
            category='large',
            total_files=total_files,
            recommended_strategy='intelligent_sampling',
            max_files_suggestion=50,
            batch_size=50
        )
    else:
        return ProjectScale(
            category='huge',
            total_files=total_files,
            recommended_strategy='directory_scope_batch',
            max_files_suggestion=30,
            batch_size=30
        )


def analyze_project(project_path: str, max_files: int = None) -> Dict:
    """
    Analyze project, return file type statistics and main language
    Enhanced with scale detection
    """
    path = Path(project_path)
    if not path.exists():
        return {'error': f'Project path does not exist: {project_path}'}

    file_types = Counter()
    file_list = []
    directory_list = set()

    # Scan files
    for file_path in path.rglob('*'):
        # Skip directories and hidden files
        if not file_path.is_file():
            continue
        if any(part.startswith('.') for part in file_path.parts):
            continue
        if any(exclude in file_path.parts for exclude in EXCLUDE_DIRS):
            continue

        ext = file_path.suffix.lower()
        if ext in EXTENSION_MAP:
            lang = EXTENSION_MAP[ext]
            file_types[lang] += 1

            rel_path = file_path.relative_to(path)
            file_list.append({
                'path': str(rel_path),
                'language': lang,
                'extension': ext,
                'directory': str(rel_path.parent),
            })
            directory_list.add(str(rel_path.parent))

    total_files = sum(file_types.values())
    main_language = file_types.most_common(1)[0][0] if file_types else None

    # Detect scale
    scale = detect_scale(total_files)

    # Apply max_files limit
    effective_max = max_files if max_files else scale.max_files_suggestion
    files_to_return = file_list[:effective_max]

    # Directory distribution
    dir_distribution = Counter(f['directory'] for f in file_list)
    top_dirs = dir_distribution.most_common(10)

    return {
        'project_path': str(path),
        'total_files': total_files,
        'file_types': dict(file_types),
        'main_language': main_language,
        'scale': asdict(scale),
        'directories': {
            'total': len(directory_list),
            'distribution': dict(top_dirs),
            'all': sorted(list(directory_list))[:50],
        },
        'files': files_to_return,
        'files_returned': len(files_to_return),
        'sampling_command': _generate_sampling_command(project_path, scale),
    }


def _generate_sampling_command(project_path: str, scale: ProjectScale) -> str:
    """Generate recommended sampling command"""
    if scale.category in ['large', 'huge']:
        return f"python scripts/sample_files.py {project_path} --strategy smart --max-files {scale.max_files_suggestion}"
    return None


def find_spec_file(language: str, examples_dir: str) -> Optional[str]:
    """
    Find matching spec file in examples directory
    """
    examples_path = Path(examples_dir)
    if not examples_path.exists():
        return None

    patterns = SPEC_FILE_MAP.get(language, [])
    for pattern in patterns:
        matches = list(examples_path.glob(pattern))
        if matches:
            # Prefer .md files
            md_matches = [m for m in matches if m.suffix == '.md']
            if md_matches:
                return str(md_matches[0])
            return str(matches[0])

    return None


def match_specs(project_info: Dict, examples_dir: str, user_spec: str = None) -> Dict:
    """
    Match specification documents
    Enhanced with spec size detection
    """
    result = {
        'user_specified': user_spec,
        'auto_matched': {},
        'missing': [],
        'spec_sizes': {},
    }

    # If user specified spec
    if user_spec and Path(user_spec).exists():
        spec_path = Path(user_spec)
        result['matched_spec'] = user_spec
        result['spec_sizes'][user_spec] = {
            'lines': _count_lines(spec_path),
            'size_category': _detect_spec_size(spec_path),
        }
        return result

    # Auto match
    file_types = project_info.get('file_types', {})

    for language in file_types:
        spec_file = find_spec_file(language, examples_dir)
        if spec_file:
            spec_path = Path(spec_file)
            result['auto_matched'][language] = spec_file
            result['spec_sizes'][spec_file] = {
                'lines': _count_lines(spec_path),
                'size_category': _detect_spec_size(spec_path),
                'chunking_needed': _needs_chunking(spec_path),
                'chunking_command': _generate_chunking_command(spec_file) if _needs_chunking(spec_path) else None,
            }
        else:
            result['missing'].append(language)

    # Main language priority
    main_lang = project_info.get('main_language')
    if main_lang and main_lang in result['auto_matched']:
        result['matched_spec'] = result['auto_matched'][main_lang]

    return result


def _count_lines(file_path: Path) -> int:
    """Count lines in a file"""
    try:
        return len(file_path.read_text(encoding='utf-8').split('\n'))
    except:
        return 0


def _detect_spec_size(file_path: Path) -> str:
    """Detect spec document size category"""
    lines = _count_lines(file_path)
    if lines < 200:
        return 'small'
    elif lines < 500:
        return 'medium'
    else:
        return 'large'


def _needs_chunking(file_path: Path) -> bool:
    """Check if spec needs chunking"""
    return _count_lines(file_path) > 300


def _generate_chunking_command(spec_file: str) -> str:
    """Generate chunking command for large spec"""
    return f"python scripts/chunk_spec.py {spec_file} --output spec_index.json"


def main():
    parser = argparse.ArgumentParser(description='Analyze project for spec compliance checking')
    parser.add_argument('project_path', help='Path to project directory')
    parser.add_argument('--examples-dir', help='Path to examples directory for spec matching')
    parser.add_argument('--user-spec', help='User-specified spec file path')
    parser.add_argument('--max-files', type=int, help='Maximum files to include in output')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--summary', action='store_true', help='Show summary only')

    args = parser.parse_args()

    # Analyze project
    project_info = analyze_project(args.project_path, args.max_files)

    if 'error' in project_info:
        print(json.dumps(project_info, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Match specs if examples_dir provided
    if args.examples_dir:
        spec_info = match_specs(project_info, args.examples_dir, args.user_spec)
        project_info['spec_matching'] = spec_info

    # Summary output
    if args.summary:
        scale = project_info['scale']
        print(f"\n=== Project Analysis Summary ===")
        print(f"Path: {args.project_path}")
        print(f"Total files: {project_info['total_files']}")
        print(f"Scale: {scale['category']} ({scale['recommended_strategy']})")
        print(f"Main language: {project_info['main_language']}")
        print(f"\nFile distribution:")
        for lang, count in project_info['file_types'].items():
            print(f"  {lang}: {count}")
        print(f"\nDirectories: {project_info['directories']['total']}")
        if scale['category'] in ['large', 'huge']:
            print(f"\nRecommended: {project_info['sampling_command']}")
        return

    # Full output
    output = json.dumps(project_info, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Analysis saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()