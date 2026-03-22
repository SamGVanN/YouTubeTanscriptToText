#!/usr/bin/env python3
"""Extract timestamps and their associated text from a YouTube transcript HTML dump.

Usage:
  python extractor.py path/to/example.txt

Outputs lines in the format: TIMESTAMP<TAB>TEXT
"""
import argparse
import os
import re
import sys
from html import unescape


def clean_leading_readable_time(seg: str) -> str:
    # remove leading human-readable time phrases like "1 minute et 6 secondes" or "5 minutes"
    pattern = re.compile(
        r'^(?:'
        r'\d+\s*(?:hours?|hour|heures?|heure)\b(?:\s*(?:et|and)\s*\d+\s*(?:minutes?|minute)\b)?'  # hours optional
        r'|' 
        r'\d+\s*(?:minutes?|minute|mins|min)\s*(?:et|and)\s*\d+\s*(?:seconds?|secondes|secs|sec)\b'  # minutes and seconds
        r'|' 
        r'\d+\s*(?:minutes?|minute|mins|min)\b'  # minutes only
        r'|' 
        r'\d+\s*(?:seconds?|secondes|secs|sec)\b'
        r')\s*',
        flags=re.I,
    )
    return pattern.sub('', seg).strip()


def extract_pairs(text: str):
    # remove HTML tags
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = unescape(clean)
    # normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()

    # match timestamps like M:SS or MM:SS or H:MM:SS
    ts_re = re.compile(r'\b\d{1,2}(?::\d{2}){1,2}\b')
    matches = list(ts_re.finditer(clean))
    pairs = []
    for i, m in enumerate(matches):
        ts = m.group()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(clean)
        seg = clean[start:end].strip()
        seg = clean_leading_readable_time(seg)
        pairs.append((ts, seg))
    return pairs


def main():
    p = argparse.ArgumentParser(description='Extract timestamps and text from a YouTube transcript HTML file')
    p.add_argument('file', help='Path to transcript file (HTML/text)')
    p.add_argument('-o', '--output', help='Optional output file. If omitted, the script will prompt for a filename or print to stdout')
    p.add_argument('-f', '--format', choices=['txt', 'md', 'tsv'], help='Output format (txt, md, tsv). If omitted, the script will ask you')
    args = p.parse_args()

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    pairs = extract_pairs(content)

    # Ask whether to include timestamps (numbered options)
    include_ts = True
    if sys.stdin.isatty():
        try:
            print('Choose transcript content:')
            print('1) With timestamps')
            print('2) Without timestamps')
            choice_ts = input('Enter the option number [1]: ').strip()
        except EOFError:
            choice_ts = ''
        if not choice_ts:
            choice_ts = '1'
        include_ts = (choice_ts == '1')

    # Determine output format (numbered options)
    fmt = args.format
    if not fmt:
        if sys.stdin.isatty():
            try:
                print('Choose output format:')
                print('1) tsv')
                print('2) txt')
                print('3) md')
                choice_fmt = input('Enter the option number [1]: ').strip()
            except EOFError:
                choice_fmt = ''
            if not choice_fmt:
                choice_fmt = '1'
            fmt_map = {'1': 'tsv', '2': 'txt', '3': 'md'}
            fmt = fmt_map.get(choice_fmt, 'tsv')
        else:
            fmt = 'tsv'

    # Determine output path (ask for name without extension if interactive)
    out_path = args.output
    if not out_path:
        base = os.path.splitext(os.path.basename(args.file))[0]
        if sys.stdin.isatty():
            try:
                name = input('Enter output filename (no extension) [output]: ').strip()
            except EOFError:
                name = ''
            if not name:
                name = 'output'
            out_path = name + '.' + fmt
        else:
            out_path = base + '.' + fmt

    # Build output content
    def escape_md(s: str) -> str:
        return s.replace('|', '\\|')

    if include_ts:
        if fmt == 'tsv':
            lines = [f"{ts}\t{seg}" for ts, seg in pairs]
        elif fmt == 'txt':
            lines = [f"{ts} - {seg}" for ts, seg in pairs]
        else:  # md
            lines = ['| Time | Text |', '|---:|---|'] + [f"| {ts} | {escape_md(seg)} |" for ts, seg in pairs]
    else:
        if fmt == 'tsv':
            lines = [f"{seg}" for ts, seg in pairs]
        elif fmt == 'txt':
            lines = [f"{seg}" for ts, seg in pairs]
        else:  # md (single-column table)
            lines = ['| Text |', '|---|'] + [f"| {escape_md(seg)} |" for ts, seg in pairs]

    content_out = '\n'.join(lines)

    if out_path:
        with open(out_path, 'w', encoding='utf-8') as fo:
            fo.write(content_out)
        print(f'Wrote {len(lines)} lines to {out_path}')
    else:
        print(content_out)


if __name__ == '__main__':
    main()
