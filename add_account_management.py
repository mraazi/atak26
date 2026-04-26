#!/usr/bin/env python3
"""
add_account_management.py
- Removes hardcoded demo accounts (pelajar, ustazah) from login
- Login now checks localStorage accounts created by admin
- Adds account management UI in Admin → ⚙ Tetapan

Run after update_standalone.py and clear_demo_data.py.

Usage:
  python3 add_account_management.py
  -> overwrites "ATAK Webapp _Standalone_.html"
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


# ── e55e5d6e: remove demo accounts, extend login to check localStorage ────────

def patch_e55e5d6e(src):

    # 1. Remove demo accounts — keep only admin
    src = apply_replacement(
        src,
        'CREDENTIALS = {\n'
        '  admin:   { password: "admin123",   role: "admin",   name: "Admin Akademi",          klass: "" },\n'
        '  pelajar: { password: "pelajar123", role: "student", name: "Pelajar", klass: "" },\n'
        '  ustazah: { password: "guru123",    role: "teacher", name: "Ustaz/Ustazah", klass: "" },\n'
        '};',
        'CREDENTIALS = {\n'
        '  admin: { password: "admin123", role: "admin", name: "Admin Akademi", klass: "" },\n'
        '};',
        'Remove demo accounts from CREDENTIALS',
    )

    # 2. Extend attempt() to also check localStorage accounts
    src = apply_replacement(
        src,
        '      const cred = CREDENTIALS[username.trim().toLowerCase()];\n'
        '      if (!cred || cred.password !== password) {\n'
        '        setError("ID pengguna atau kata laluan tidak sah."); setLoading(false); return;\n'
        '      }',
        '      const _user = username.trim().toLowerCase();\n'
        '      let cred = CREDENTIALS[_user];\n'
        "      if (!cred) { try { const _a = JSON.parse(localStorage.getItem('atak-accounts') || '{}'); cred = _a[_user]; } catch {} }\n"
        '      if (!cred || cred.password !== password) {\n'
        '        setError("ID pengguna atau kata laluan tidak sah."); setLoading(false); return;\n'
        '      }',
        'Login: check localStorage accounts',
    )

    return src


# ── bab51bd9: add account states + account management UI in settings ──────────

def patch_bab51bd9(src):

    # 1. Add account management states after bpCollId state
    src = apply_replacement(
        src,
        "  const [bpCollId, setBpCollId] = useS3(() => { try { return JSON.parse(localStorage.getItem('atak-bp-settings') || 'null')?.collectionId || DATA.billplzSettings?.collectionId || 'aou6h6qp'; } catch { return 'aou6h6qp'; } });",
        "  const [bpCollId, setBpCollId] = useS3(() => { try { return JSON.parse(localStorage.getItem('atak-bp-settings') || 'null')?.collectionId || DATA.billplzSettings?.collectionId || 'aou6h6qp'; } catch { return 'aou6h6qp'; } });\n"
        "  const [accs, setAccs] = useS3(() => { try { return JSON.parse(localStorage.getItem('atak-accounts') || '{}'); } catch { return {}; } });\n"
        "  const [newUser, setNewUser] = useS3('');\n"
        "  const [newPw, setNewPw] = useS3('');\n"
        "  const [newName, setNewName] = useS3('');\n"
        "  const [newRole, setNewRole] = useS3('student');\n"
        "  const [newKlass, setNewKlass] = useS3('');",
        'ManageView: add account management states',
    )

    # 2. Add account management panel inside settings tab (after Simpan tetapan button)
    ACCT_PANEL = (
        'Simpan tetapan</button>\n'
        '          </div>\n'
        '        </div>\n'
        '      )}\n'
        '\n'
        '      {/* ── PENGURUSAN AKAUN ──────────────────────────── */}\n'
        '      {tab==="settings" && (\n'
        '        <div className="card" style={{maxWidth:520, marginTop:16}}>\n'
        '          <div style={{fontWeight:700, fontSize:15, marginBottom:4}}>👤 Pengurusan Akaun</div>\n'
        '          <div className="muted" style={{fontSize:12, marginBottom:16}}>Cipta akaun login untuk pelajar dan guru. Akaun disimpan dalam peranti ini.</div>\n'
        '\n'
        '          {/* existing accounts list */}\n'
        '          {Object.keys(accs).length > 0 && (\n'
        '            <div className="col" style={{gap:6, marginBottom:16}}>\n'
        '              {Object.entries(accs).map(([u, a]) => (\n'
        '                <div key={u} className="row between" style={{padding:"8px 12px", border:"1px solid var(--line)", borderRadius:6, fontSize:13}}>\n'
        '                  <div className="col" style={{gap:2}}>\n'
        '                    <span style={{fontWeight:600}}>{a.name} <span className="muted" style={{fontWeight:400}}>(@{u})</span></span>\n'
        '                    <span className="muted" style={{fontSize:11}}>{a.role === "student" ? "Pelajar" : "Guru"}{a.klass ? " • " + a.klass : ""}</span>\n'
        '                  </div>\n'
        '                  <button className="btn sm ghost" style={{color:"var(--red, #e53)"}} onClick={()=>{\n'
        '                    const updated = {...accs}; delete updated[u];\n'
        "                    localStorage.setItem('atak-accounts', JSON.stringify(updated));\n"
        '                    setAccs(updated);\n'
        "                    push('Akaun ' + u + ' dipadam.');\n"
        '                  }}>Padam</button>\n'
        '                </div>\n'
        '              ))}\n'
        '            </div>\n'
        '          )}\n'
        '\n'
        '          {/* add account form */}\n'
        '          <div className="col" style={{gap:10}}>\n'
        '            <div style={{fontSize:12, fontWeight:600, color:"var(--ink-2)"}}>Tambah akaun baru</div>\n'
        '            <div className="row" style={{gap:8, flexWrap:"wrap"}}>\n'
        '              <input value={newUser} onChange={e=>setNewUser(e.target.value.toLowerCase().replace(/\\s/g,""))} placeholder="ID pengguna" style={{flex:1, minWidth:120}}/>\n'
        '              <input type="password" value={newPw} onChange={e=>setNewPw(e.target.value)} placeholder="Kata laluan" style={{flex:1, minWidth:120}}/>\n'
        '            </div>\n'
        '            <input value={newName} onChange={e=>setNewName(e.target.value)} placeholder="Nama penuh" style={{width:"100%"}}/>\n'
        '            <div className="row" style={{gap:8}}>\n'
        '              <select value={newRole} onChange={e=>setNewRole(e.target.value)} style={{flex:1}}>\n'
        '                <option value="student">Pelajar</option>\n'
        '                <option value="teacher">Guru</option>\n'
        '              </select>\n'
        '              <select value={newKlass} onChange={e=>setNewKlass(e.target.value)} style={{flex:1}}>\n'
        '                <option value="">— Pilih kelas —</option>\n'
        '                {DATA.classes.map(c => <option key={c} value={c}>{c}</option>)}\n'
        '              </select>\n'
        '            </div>\n'
        '            <button className="btn accent" style={{alignSelf:"flex-start"}} onClick={()=>{\n'
        '              const u = newUser.trim();\n'
        '              if (!u || !newPw || !newName) { push("Sila isi semua medan."); return; }\n'
        '              if (u === "admin") { push("Nama pengguna ini tidak dibenarkan."); return; }\n'
        '              const updated = {...accs, [u]: {password:newPw, role:newRole, name:newName, klass:newKlass}};\n'
        "              localStorage.setItem('atak-accounts', JSON.stringify(updated));\n"
        '              setAccs(updated);\n'
        "              setNewUser(''); setNewPw(''); setNewName(''); setNewRole('student'); setNewKlass('');\n"
        "              push('Akaun ' + u + ' berjaya dicipta.');\n"
        '            }}>Cipta akaun</button>\n'
        '          </div>\n'
        '        </div>\n'
        '      )}\n'
        '\n'
        '      {/* ── MODAL: PROFIL PELAJAR'
    )

    src = apply_replacement(
        src,
        'Simpan tetapan</button>\n'
        '          </div>\n'
        '        </div>\n'
        '      )}\n'
        '\n'
        '      {/* ── MODAL: PROFIL PELAJAR',
        ACCT_PANEL,
        'ManageView: add account management panel',
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
        find_uuid('e55e5d6e'): ('e55e5d6e (login)', patch_e55e5d6e),
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
    print('\nOnly one login account remains:')
    print('  admin / admin123 → Admin (change this password after first login)')
    print('\nTo create student/teacher accounts:')
    print('  Login as admin → ⚙ Tetapan → 👤 Pengurusan Akaun → Cipta akaun')


if __name__ == '__main__':
    main()
