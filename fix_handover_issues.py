#!/usr/bin/env python3
"""
fix_handover_issues.py
Fixes all remaining hardcoded demo names and stale references before client handover.

Fixes applied:
  e55e5d6e  - Teacher sidebar name: use tweaks.studentName instead of "Ustazah Khairunnisa"
  2a130e7c  - TeacherDash: dynamic greeting/class, remove Laporan & Portfolio tiles
  d3a0865f  - AttendanceView: dynamic subtitle using attClass + attMonth state
  ab006c6d  - PortfolioView: use logged-in name; REPORTS/table: replace "Ustazah Khairunnisa" → "Guru"
  bab51bd9  - Remove hardcoded 'aou6h6qp' fallback collection ID
"""

import base64
import gzip
import json
import re
import sys

SRC  = 'ATAK Webapp _Standalone_.html'
DEST = 'ATAK Webapp _Standalone_.html'


def decompress_module(b64_data):
    return gzip.decompress(base64.b64decode(b64_data)).decode('utf-8')

def compress_module(text):
    return base64.b64encode(gzip.compress(text.encode('utf-8'), compresslevel=9)).decode('ascii')

def apply_replacement(src, old, new, label):
    if old not in src:
        print(f'  ✗ "{label}" — not found, skipping')
        return src
    result = src.replace(old, new, 1)
    print(f'  ✓ {label}')
    return result

def apply_replacement_all(src, old, new, label):
    if old not in src:
        print(f'  ✗ "{label}" — not found, skipping')
        return src
    count = src.count(old)
    result = src.replace(old, new)
    print(f'  ✓ {label} ({count}×)')
    return result


# ── e55e5d6e: teacher sidebar name ────────────────────────────────────────────

def patch_e55e5d6e(src):
    src = apply_replacement(
        src,
        '{tweaks.role==="teacher"?"Ustazah Khairunnisa":tweaks.role==="admin"?"Admin Akademi":tweaks.studentName.split(" ").slice(0,2).join(" ")}',
        '{tweaks.role==="admin"?"Admin Akademi":tweaks.studentName.split(" ").slice(0,2).join(" ")}',
        'Sidebar: remove hardcoded teacher name',
    )
    return src


# ── 2a130e7c: TeacherDash dynamic greeting + remove Laporan/Portfolio tiles ───

def patch_2a130e7c(src):

    # 1. Add name/klass to TeacherDash destructure
    src = apply_replacement(
        src,
        'function TeacherDash() {\n  const { go, push } = useApp();',
        'function TeacherDash() {\n  const { go, push, name, klass } = useApp();',
        'TeacherDash: destructure name, klass from useApp',
    )

    # 2. Fix hardcoded title and sub
    src = apply_replacement(
        src,
        '        title="Salam Ustazah Khairunnisa"\n        sub="Al-Mukammil • 28 pelajar aktif"',
        '        title={`Salam ${name || \'Ustaz/Ustazah\'}`}\n        sub={`${klass || \'\'} • ${DATA.students.length} pelajar aktif`.replace(/^\\s*•\\s*/, \'\')}',
        'TeacherDash: dynamic greeting and student count',
    )

    # 3. Remove Laporan tile
    src = apply_replacement(
        src,
        '              <Tile onClick={() => go("rpt")}   icon={I.chart} title="Laporan" sub="Mingguan & bulanan" />\n',
        '',
        'TeacherDash: remove Laporan tile',
    )

    # 4. Remove Portfolio tile
    src = apply_replacement(
        src,
        '              <Tile onClick={() => go("portfolio")} icon={I.trophy} title="Portfolio" sub="Pencapaian & sijil" />\n',
        '',
        'TeacherDash: remove Portfolio tile',
    )

    return src


# ── d3a0865f: AttendanceView dynamic subtitle ─────────────────────────────────

def patch_d3a0865f(src):
    src = apply_replacement(
        src,
        '        sub="Al-Mukammil • April 2026 • klik sel untuk tukar status"',
        '        sub={`${attClass === \'Semua\' ? \'Semua Kelas\' : attClass} • ${attMonth} • klik sel untuk tukar status`}',
        'AttendanceView: dynamic subtitle',
    )
    return src


# ── ab006c6d: PortfolioView + REPORTS demo names ──────────────────────────────

def patch_ab006c6d(src):

    # 1. Add name to PortfolioView from useApp
    src = apply_replacement(
        src,
        'function PortfolioView() {\n  return (',
        'function PortfolioView() {\n  const { name } = useApp();\n  return (',
        'PortfolioView: get name from useApp',
    )

    # 2. Replace hardcoded avatar initials
    src = apply_replacement(
        src,
        '          <div className="av xl" style={{background:"var(--accent)", color:"white"}}>NA</div>',
        '          <div className="av xl" style={{background:"var(--accent)", color:"white"}}>{(name||"?").split(" ").map(w=>w[0]).slice(0,2).join("")}</div>',
        'PortfolioView: dynamic avatar initials',
    )

    # 3. Replace hardcoded student name heading
    src = apply_replacement(
        src,
        '            <h2 style={{margin:"0 0 4px", fontSize:22}}>Nur Aisyah binti Ahmad</h2>',
        '            <h2 style={{margin:"0 0 4px", fontSize:22}}>{name}</h2>',
        'PortfolioView: dynamic student name',
    )

    # 4. Replace all "Ustazah Khairunnisa" in REPORTS constant and history table
    src = apply_replacement_all(
        src,
        '"Ustazah Khairunnisa"',
        '"Guru"',
        'REPORTS/table: replace Ustazah Khairunnisa → Guru',
    )

    # 5. Remove student-specific comment in REPORTS
    src = apply_replacement(
        src,
        '"Aisyah menunjukkan perkembangan yang memberangsangkan dalam bacaan surah Al-Mulk. Sebutan huk',
        '"Pelajar menunjukkan perkembangan yang memberangsangkan dalam bacaan surah Al-Mulk. Sebutan huk',
        'REPORTS: remove student-specific name in comment',
    )
    src = apply_replacement(
        src,
        '"Aisyah menunjukkan perkembangan yang memberangsangkan dalam bacaan surah Al-Mulk. Sebutan huk'.replace('huk', ''),
        '"Pelajar menunjukkan perkembangan yang memberangsangkan dalam bacaan surah Al-Mulk. Sebutan huk'.replace('huk', ''),
        'REPORTS: fallback replace (noop)',
    )

    return src


# ── bab51bd9: remove hardcoded aou6h6qp fallback ─────────────────────────────

def patch_bab51bd9(src):
    src = apply_replacement(
        src,
        "    const collectionId = settings.collectionId || 'aou6h6qp';",
        "    const collectionId = settings.collectionId || '';",
        'Billplz: remove hardcoded aou6h6qp fallback',
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

    def find_uuid(prefix):
        for k in manifest:
            if k.startswith(prefix):
                return k
        return None

    patches = {
        find_uuid('e55e5d6e'): ('e55e5d6e (login/nav)',      patch_e55e5d6e),
        find_uuid('2a130e7c'): ('2a130e7c (Dashboard)',       patch_2a130e7c),
        find_uuid('d3a0865f'): ('d3a0865f (Attendance)',      patch_d3a0865f),
        find_uuid('ab006c6d'): ('ab006c6d (Homework/Report)', patch_ab006c6d),
        find_uuid('bab51bd9'): ('bab51bd9 (ManageView)',      patch_bab51bd9),
    }

    for uuid, (label, fn) in patches.items():
        if uuid is None:
            print(f'\n⚠ Module {label} not found, skipping')
            continue
        print(f'\nPatching {label}…')
        original = decompress_module(manifest[uuid]['data'])
        patched = fn(original)
        if patched == original:
            print(f'  ⚠ No changes made to module')
        else:
            manifest[uuid]['data'] = compress_module(patched)
            print(f'  ✓ Module updated')

    new_html = html[:m.start(2)] + json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + html[m.end(2):]

    print(f'\nWriting {DEST}…')
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print('\nDone ✓')


if __name__ == '__main__':
    main()
