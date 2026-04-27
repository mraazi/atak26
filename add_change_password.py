#!/usr/bin/env python3
"""
add_change_password.py
Adds "Tukar Kata Laluan" (change password) feature for admin.
- Admin password override stored in localStorage 'atak-admin-pw'
- Login checks the override before CREDENTIALS
- Settings tab has a 🔒 Tukar Kata Laluan panel before 💳 Billplz
- Export/Import includes the admin password

Run from the ATAK directory.
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


# ── e55e5d6e: add admin password override at login ────────────────────────────────────────────

def patch_e55e5d6e(src):
    src = apply_replacement(
        src,
        "      const _user = username.trim().toLowerCase();\n"
        "      let cred = CREDENTIALS[_user];\n"
        "      if (!cred) { try { const _a = JSON.parse(localStorage.getItem('atak-accounts') || '{}'); cred = _a[_user]; } catch {} }",
        "      const _user = username.trim().toLowerCase();\n"
        "      let cred = CREDENTIALS[_user] ? {...CREDENTIALS[_user]} : null;\n"
        "      if (cred && _user === 'admin') { try { const _pw = localStorage.getItem('atak-admin-pw'); if (_pw) cred.password = _pw; } catch {} }\n"
        "      if (!cred) { try { const _a = JSON.parse(localStorage.getItem('atak-accounts') || '{}'); cred = _a[_user]; } catch {} }",
        'Login: admin password override from localStorage',
    )
    return src


# ── bab51bd9: add change-password states, function, UI, export/import ─────────────────

def patch_bab51bd9(src):

    # 1. Add oldPw/newPw1/newPw2 states after newKlass state
    src = apply_replacement(
        src,
        "  const [newKlass, setNewKlass] = useS3('');",
        "  const [newKlass, setNewKlass] = useS3('');\n"
        "  const [oldPw, setOldPw] = useS3('');\n"
        "  const [newPw1, setNewPw1] = useS3('');\n"
        "  const [newPw2, setNewPw2] = useS3('');",
        'Add change-password states',
    )

    # 2. Add changePw() function before exportData
    src = apply_replacement(
        src,
        "  const exportData = () => {",
        "  const changePw = () => {\n"
        "    const current = (() => { try { return localStorage.getItem('atak-admin-pw') || 'admin123'; } catch { return 'admin123'; } })();\n"
        "    if (oldPw !== current) { push('Kata laluan semasa tidak tepat.'); return; }\n"
        "    if (newPw1.length < 4) { push('Kata laluan baru terlalu pendek (min. 4 aksara).'); return; }\n"
        "    if (newPw1 !== newPw2) { push('Kata laluan baru tidak sepadan.'); return; }\n"
        "    try { localStorage.setItem('atak-admin-pw', newPw1); } catch {}\n"
        "    setOldPw(''); setNewPw1(''); setNewPw2('');\n"
        "    push('Kata laluan berjaya ditukar ✓');\n"
        "  };\n"
        "\n"
        "  const exportData = () => {",
        'Add changePw() function',
    )

    # 3. Include adminPw in exportData object
    src = apply_replacement(
        src,
        "        billplzSettings: JSON.parse(localStorage.getItem('atak-bp-settings') || '{}'),\n"
        "        exportedAt: new Date().toISOString(),",
        "        billplzSettings: JSON.parse(localStorage.getItem('atak-bp-settings') || '{}'),\n"
        "        adminPw: localStorage.getItem('atak-admin-pw') || null,\n"
        "        exportedAt: new Date().toISOString(),",
        'Include admin password in export',
    )

    # 4. Restore adminPw in importData
    src = apply_replacement(
        src,
        "        if (d.billplzSettings) { localStorage.setItem('atak-bp-settings', JSON.stringify(d.billplzSettings)); }\n"
        "        push('Data berjaya diimport ✓');",
        "        if (d.billplzSettings) { localStorage.setItem('atak-bp-settings', JSON.stringify(d.billplzSettings)); }\n"
        "        if (d.adminPw)         { localStorage.setItem('atak-admin-pw', d.adminPw); }\n"
        "        push('Data berjaya diimport ✓');",
        'Restore admin password on import',
    )

    # 5. Add 🔒 Tukar Kata Laluan panel before 💳 Tetapan Billplz card
    src = apply_replacement(
        src,
        "      {/* ── TETAPAN BILLPLZ ───────────────────────────── */}\n"
        '      {tab==="settings" && (\n'
        '        <div className="card" style={{maxWidth:520}}>\n'
        '          <div style={{fontWeight:700, fontSize:15, marginBottom:4}}>💳 Tetapan Billplz</div>',
        "      {/* ── TUKAR KATA LALUAN ─────────────────────────── */}\n"
        '      {tab==="settings" && (\n'
        '        <div className="card" style={{maxWidth:520, marginBottom:16}}>\n'
        '          <div style={{fontWeight:700, fontSize:15, marginBottom:4}}>🔒 Tukar Kata Laluan Admin</div>\n'
        '          <div className="muted" style={{fontSize:12, marginBottom:16}}>Tukar kata laluan akaun admin. Kata laluan lalai: <code>admin123</code></div>\n'
        '          <div className="col" style={{gap:10}}>\n'
        '            <input type="password" value={oldPw} onChange={e=>setOldPw(e.target.value)} placeholder="Kata laluan semasa" style={{maxWidth:300}}/>\n'
        '            <input type="password" value={newPw1} onChange={e=>setNewPw1(e.target.value)} placeholder="Kata laluan baru (min. 4 aksara)" style={{maxWidth:300}}/>\n'
        '            <input type="password" value={newPw2} onChange={e=>setNewPw2(e.target.value)} placeholder="Ulang kata laluan baru" style={{maxWidth:300}}/>\n'
        '            <button className="btn accent" style={{alignSelf:"flex-start"}} onClick={changePw}>Tukar Kata Laluan</button>\n'
        '          </div>\n'
        '        </div>\n'
        '      )}\n'
        '\n'
        "      {/* ── TETAPAN BILLPLZ ───────────────────────────── */}\n"
        '      {tab==="settings" && (\n'
        '        <div className="card" style={{maxWidth:520}}>\n'
        '          <div style={{fontWeight:700, fontSize:15, marginBottom:4}}>💳 Tetapan Billplz</div>',
        'Add 🔒 Tukar Kata Laluan panel before Billplz',
    )

    return src


# ── main ──────────────────────────────────────────────────────────────────────────────

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
        find_uuid('e55e5d6e'): ('e55e5d6e (login)',      patch_e55e5d6e),
        find_uuid('bab51bd9'): ('bab51bd9 (ManageView)', patch_bab51bd9),
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

    print('\nDone ✓')
    print('\nAdmin can now change their password:')
    print('  Login as admin → ⚙ Tetapan → 🔒 Tukar Kata Laluan Admin')
    print('  Default password: admin123')


if __name__ == '__main__':
    main()
