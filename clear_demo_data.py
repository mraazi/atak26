#!/usr/bin/env python3
"""
clear_demo_data.py
Removes all demo/seed data from "ATAK Webapp _Standalone_.html"
so the app starts with a clean slate.

Run AFTER update_standalone.py (Billplz patches must already be applied).

Usage:
  python3 clear_demo_data.py
  -> overwrites "ATAK Webapp _Standalone_.html"
"""

import base64
import gzip
import json
import re
import sys

SRC  = 'ATAK Webapp _Standalone_.html'
DEST = 'ATAK Webapp _Standalone_.html'


def decompress_module(b64_data: str) -> str:
    return gzip.decompress(base64.b64decode(b64_data)).decode('utf-8')

def compress_module(text: str) -> str:
    return base64.b64encode(gzip.compress(text.encode('utf-8'), compresslevel=9)).decode('ascii')

def apply_replacement(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        print(f'  ✗ "{label}" — not found, skipping')
        return src
    result = src.replace(old, new, 1)
    print(f'  ✓ {label}')
    return result


# ── Module 577c0d01: clear all demo arrays and IDs ───────────────────────────

def patch_577c0d01(src: str) -> str:

    # Clear students array
    src = re.sub(
        r'students:\s*\[.*?\],',
        'students: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: students')

    # Clear teachers array
    src = re.sub(
        r'teachers:\s*\[.*?\],',
        'teachers: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: teachers')

    # Clear notifications array
    src = re.sub(
        r'notifications:\s*\[.*?\],',
        'notifications: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: notifications')

    # Clear threads array
    src = re.sub(
        r'threads:\s*\[.*?\],',
        'threads: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: threads')

    # Clear dailyLogs array
    src = re.sub(
        r'dailyLogs:\s*\[.*?\],',
        'dailyLogs: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: dailyLogs')

    # Clear homeworks array
    src = re.sub(
        r'homeworks:\s*\[.*?\],',
        'homeworks: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: homeworks')

    # Clear events array
    src = re.sub(
        r'events:\s*\[.*?\],',
        'events: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: events')

    # Clear payments array
    src = re.sub(
        r'payments:\s*\[.*?\],',
        'payments: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: payments')

    # Clear documents array
    src = re.sub(
        r'documents:\s*\[.*?\],',
        'documents: [],',
        src, flags=re.DOTALL
    )
    print('  ✓ Cleared: documents')

    # Clear billplzSettings collectionId (admin must enter their own)
    src = apply_replacement(
        src,
        "    collectionId: 'aou6h6qp',",
        "    collectionId: '',",
        'billplzSettings.collectionId cleared',
    )

    return src


# ── Module e55e5d6e: replace demo names in credentials ───────────────────────

def patch_e55e5d6e(src: str) -> str:
    # Replace hardcoded demo student name with generic
    src = apply_replacement(
        src,
        '  pelajar: { password: "pelajar123", role: "student", name: "Nur Aisyah binti Ahmad", klass: "Al-Mukammil" },',
        '  pelajar: { password: "pelajar123", role: "student", name: "Pelajar", klass: "" },',
        'Credentials: clear demo student name',
    )
    # Replace hardcoded demo teacher name with generic
    src = apply_replacement(
        src,
        '  ustazah: { password: "guru123",    role: "teacher", name: "Ustazah Khairunnisa",     klass: "Al-Mukammil" },',
        '  ustazah: { password: "guru123",    role: "teacher", name: "Ustaz/Ustazah", klass: "" },',
        'Credentials: clear demo teacher name',
    )
    return src


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'Reading {SRC}…')
    with open(SRC, 'r', encoding='utf-8') as f:
        html = f.read()

    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        sys.exit('ERROR: __bundler/manifest not found')

    manifest = json.loads(m.group(2))

    # Find UUIDs by prefix
    def find_uuid(prefix):
        for k in manifest:
            if k.startswith(prefix):
                return k
        return None

    patches = {
        find_uuid('577c0d01'): ('577c0d01 (DATA seed)',    patch_577c0d01),
        find_uuid('e55e5d6e'): ('e55e5d6e (credentials)',  patch_e55e5d6e),
    }

    for uuid, (label, fn) in patches.items():
        if uuid is None:
            print(f'\n⚠ Module {label} not found, skipping')
            continue
        print(f'\nPatching {label}…')
        original = decompress_module(manifest[uuid]['data'])
        patched = fn(original)
        if patched == original:
            print(f'  ⚠ No changes made')
        else:
            manifest[uuid]['data'] = compress_module(patched)
            print(f'  ✓ Module updated')

    new_html = html[:m.start(2)] + json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + html[m.end(2):]

    print(f'\nWriting {DEST}…')
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print('Done ✓')
    print('\nLogin credentials (unchanged):')
    print('  admin   / admin123   → Admin')
    print('  pelajar / pelajar123 → Student (name cleared)')
    print('  ustazah / guru123    → Teacher (name cleared)')


if __name__ == '__main__':
    main()
