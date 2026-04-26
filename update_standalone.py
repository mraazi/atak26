#!/usr/bin/env python3
"""
update_standalone.py
Patches "ATAK Webapp _Standalone_.html" to add live Billplz payment integration.

Changes applied:
  Module bab51bd9  — PaymentView: replace simulated payment modal with Billplz
  Module bab51bd9  — ManageView:  add ⚙ Tetapan tab with Billplz Worker URL config
  Module 577c0d01  — DATA:        add billplzSettings { workerUrl, collectionId }

Usage:
  python3 update_standalone.py
  -> writes "ATAK Webapp _Standalone_.html" (overwrites original)
"""

import base64
import gzip
import json
import re
import sys

SRC  = 'ATAK Webapp _Standalone_.html'
DEST = 'ATAK Webapp _Standalone_.html'   # overwrite in-place

# ── helpers ──────────────────────────────────────────────────────────────────

def decompress_module(b64_data: str) -> str:
    raw = base64.b64decode(b64_data)
    return gzip.decompress(raw).decode('utf-8')

def compress_module(text: str) -> str:
    compressed = gzip.compress(text.encode('utf-8'), compresslevel=9)
    return base64.b64encode(compressed).decode('ascii')

def apply_replacement(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        print(f'  ✗ Replacement "{label}" — OLD string NOT found, skipping')
        return src
    count = src.count(old)
    if count > 1:
        print(f'  ⚠ Replacement "{label}" — found {count} occurrences, replacing first only')
    result = src.replace(old, new, 1)
    print(f'  ✓ Applied: {label}')
    return result


# ── bab51bd9 patches ──────────────────────────────────────────────────────────

def patch_bab51bd9(src: str) -> str:
    """Apply all changes to the PaymentView + ManageView module."""

    # 1. Add `name` to useApp destructure
    src = apply_replacement(
        src,
        '  const { role, push } = useApp();',
        '  const { role, push, name } = useApp();',
        'useApp: add name',
    )

    # 2. Add bpLoading state
    src = apply_replacement(
        src,
        '  const [payOpen, setPayOpen] = useS3(null);\n  const [tab, setTab] = useS3("all");',
        '  const [payOpen, setPayOpen] = useS3(null);\n  const [tab, setTab] = useS3("all");\n  const [bpLoading, setBpLoading] = useS3(false);',
        'PaymentView: add bpLoading state',
    )

    # 3. Insert handleBillplz async function before `const outstanding`
    BILLPLZ_FN = (
        '  const handleBillplz = async (p) => {\n'
        "    let settings = { ...(DATA.billplzSettings || {}) };\n"
        "    try { const ls = JSON.parse(localStorage.getItem('atak-bp-settings') || 'null'); if (ls) Object.assign(settings, ls); } catch {}\n"
        "    const workerUrl = (settings.workerUrl || '').replace(/\\/$/, '');\n"
        "    const collectionId = settings.collectionId || 'aou6h6qp';\n"
        "    if (!workerUrl) { push('URL Worker Billplz belum dikonfigurasi. Sila hubungi admin.'); return; }\n"
        '    setBpLoading(true);\n'
        '    try {\n'
        '      const body = new URLSearchParams({\n'
        '        collection_id: collectionId,\n'
        "        email: '',\n"
        "        mobile: '',\n"
        "        name: name || 'Pelajar ATAK',\n"
        '        amount: Math.round(p.amount * 100),\n'
        '        description: p.desc.slice(0, 200),\n'
        '        redirect_url: window.location.href,\n'
        '        callback_url: window.location.href,\n'
        "        reference_1_label: 'Invois',\n"
        '        reference_1: p.inv,\n'
        '      });\n'
        "      const resp = await fetch(workerUrl + '/bills', {\n"
        "        method: 'POST',\n"
        "        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },\n"
        '        body: body.toString(),\n'
        '      });\n'
        '      if (!resp.ok) throw new Error(await resp.text());\n'
        '      const data = await resp.json();\n'
        '      setPayments(payments.map(x => x.id === p.id ? { ...x, billplzUrl: data.url, billplzBillId: data.id, status: \'pending\' } : x));\n'
        "      window.open(data.url, '_blank');\n"
        '      setPayOpen(null);\n'
        "      push('Pautan Billplz dibuka — sila selesaikan pembayaran.');\n"
        '    } catch (e) {\n'
        "      push('Gagal cipta bil Billplz: ' + (e.message || 'Ralat tidak diketahui'));\n"
        '    } finally {\n'
        '      setBpLoading(false);\n'
        '    }\n'
        '  };\n'
        '\n'
    )
    src = apply_replacement(
        src,
        '  const outstanding = payments.filter',
        BILLPLZ_FN + '  const outstanding = payments.filter',
        'PaymentView: insert handleBillplz',
    )

    # 4. Replace table action cell to add 🔗 link when billplzUrl exists
    OLD_TD = (
        '                <td>\n'
        '                  {p.status!=="paid" ? <button className="btn sm accent" onClick={()=>setPayOpen(p)}>Bayar</button> : <button className="btn sm ghost" title="Resit">{I.receipt}</button>}\n'
        '                </td>'
    )
    NEW_TD = (
        '                <td>\n'
        '                  <div className="row" style={{gap:4}}>\n'
        '                    {p.status!=="paid" ? <button className="btn sm accent" onClick={()=>setPayOpen(p)}>Bayar</button> : <button className="btn sm ghost" title="Resit">{I.receipt}</button>}\n'
        "                    {p.billplzUrl && <a href={p.billplzUrl} target=\"_blank\" className=\"btn sm ghost\" title=\"Buka Billplz\" style={{textDecoration:'none'}}>&#128279;</a>}\n"
        '                  </div>\n'
        '                </td>'
    )
    src = apply_replacement(src, OLD_TD, NEW_TD, 'PaymentView: add billplz link in table row')

    # 5. Replace payment modal (simulated → Billplz)
    OLD_MODAL = (
        '      {payOpen && (\n'
        '        <Modal title="Pembayaran" onClose={()=>setPayOpen(null)} footer={<>\n'
        '          <button className="btn" onClick={()=>setPayOpen(null)}>Batal</button>\n'
        '          <button className="btn accent" onClick={()=>pay(payOpen.id)}>Bayar RM {payOpen.amount.toFixed(2)}</button>\n'
        '        </>}>\n'
        '          <div style={{background:"var(--bg)", padding:14, borderRadius:8, marginBottom:16}}>\n'
        '            <div className="row between" style={{fontSize:12, marginBottom:6}}><span className="muted">Invois</span><span style={{fontFamily:"var(--f-mono)"}}>{payOpen.inv}</span></div>\n'
        '            <div className="row between" style={{fontSize:13, marginBottom:6}}><span>{payOpen.desc}</span><span className="tabnums" style={{fontWeight:600}}>RM {payOpen.amount.toFixed(2)}</span></div>\n'
        '            <div className="row between" style={{fontSize:12}}><span className="muted">Tamat tempoh</span><span>{payOpen.due}</span></div>\n'
        '          </div>\n'
        '          <div className="field"><label>Kaedah pembayaran</label>\n'
        '            <div className="col" style={{gap:6}}>\n'
        '              {["FPX Perbankan Internet","Kad Kredit/Debit","e-Wallet (Touch \'n Go / Boost)","Pindahan manual"].map((m,i)=>(\n'
        '                <label key={m} className="row" style={{padding:10, border:"1px solid var(--line)", borderRadius:6, cursor:"pointer", gap:10}}>\n'
        '                  <input type="radio" name="pay" defaultChecked={i===0}/>\n'
        '                  <span style={{flex:1, fontSize:13}}>{m}</span>\n'
        '                </label>\n'
        '              ))}\n'
        '            </div>\n'
        '          </div>\n'
        '          <div className="muted" style={{fontSize:11, textAlign:"center"}}>Pembayaran selamat oleh ATAK Pay • disulitkan SSL</div>\n'
        '        </Modal>\n'
        '      )}'
    )
    NEW_MODAL = (
        '      {payOpen && (\n'
        '        <Modal title="Pembayaran via Billplz" onClose={()=>setPayOpen(null)} footer={<>\n'
        '          <button className="btn" onClick={()=>setPayOpen(null)}>Batal</button>\n'
        '          <button className="btn accent" onClick={()=>handleBillplz(payOpen)} disabled={bpLoading}>\n'
        '            {bpLoading ? "Mencipta bil…" : `💳 Bayar RM ${payOpen.amount.toFixed(2)} via Billplz`}\n'
        '          </button>\n'
        '        </>}>\n'
        '          <div style={{background:"var(--bg)", padding:14, borderRadius:8, marginBottom:16}}>\n'
        '            <div className="row between" style={{fontSize:12, marginBottom:6}}><span className="muted">Invois</span><span style={{fontFamily:"var(--f-mono)"}}>{payOpen.inv}</span></div>\n'
        '            <div className="row between" style={{fontSize:13, marginBottom:6}}><span>{payOpen.desc}</span><span className="tabnums" style={{fontWeight:600}}>RM {payOpen.amount.toFixed(2)}</span></div>\n'
        '            <div className="row between" style={{fontSize:12}}><span className="muted">Tamat tempoh</span><span>{payOpen.due}</span></div>\n'
        '          </div>\n'
        '          <div className="muted" style={{fontSize:12, textAlign:"center", marginBottom:12}}>\n'
        '            Pembayaran selamat melalui Billplz • FPX, kad kredit, e-dompet diterima\n'
        '          </div>\n'
        '        </Modal>\n'
        '      )}'
    )
    src = apply_replacement(src, OLD_MODAL, NEW_MODAL, 'PaymentView: replace modal with Billplz modal')

    # 6. Add Billplz state to ManageView (reads from localStorage so it survives refresh)
    src = apply_replacement(
        src,
        '  const [selFees, setSelFees] = useS3([]);',
        (
            '  const [selFees, setSelFees] = useS3([]);\n'
            "  const [bpWorkerUrl, setBpWorkerUrl] = useS3(() => { try { return JSON.parse(localStorage.getItem('atak-bp-settings') || 'null')?.workerUrl || DATA.billplzSettings?.workerUrl || ''; } catch { return ''; } });\n"
            "  const [bpCollId, setBpCollId] = useS3(() => { try { return JSON.parse(localStorage.getItem('atak-bp-settings') || 'null')?.collectionId || DATA.billplzSettings?.collectionId || 'aou6h6qp'; } catch { return 'aou6h6qp'; } });"
        ),
        'ManageView: add Billplz state (localStorage-backed)',
    )

    # 7. Add settings tab to Tabs
    OLD_FEES_TAB = (
        "        {id:\"fees\",     label:\"Yuran\",   count:feeStats.overdue ? `${feeStats.overdue} lewat` : feeStats.due || undefined},\n"
        "      ]} value={tab} onChange={t=>{setTab(t); setSearch(\"\");}}/>"
    )
    NEW_FEES_TAB = (
        "        {id:\"fees\",     label:\"Yuran\",   count:feeStats.overdue ? `${feeStats.overdue} lewat` : feeStats.due || undefined},\n"
        "        {id:\"settings\", label:\"⚙ Tetapan\"},\n"
        "      ]} value={tab} onChange={t=>{setTab(t); setSearch(\"\");}}/>"
    )
    src = apply_replacement(src, OLD_FEES_TAB, NEW_FEES_TAB, 'ManageView: add settings tab')

    # 8. Add settings panel before student profile modal
    SETTINGS_PANEL = (
        '      {/* ── TETAPAN BILLPLZ ───────────────────────────── */}\n'
        '      {tab==="settings" && (\n'
        '        <div className="card" style={{maxWidth:520}}>\n'
        '          <div style={{fontWeight:700, fontSize:15, marginBottom:4}}>💳 Tetapan Billplz</div>\n'
        '          <div className="muted" style={{fontSize:12, marginBottom:16}}>Konfigurasi Cloudflare Worker untuk pemprosesan pembayaran automatik melalui Billplz.</div>\n'
        '          <div className="col" style={{gap:14}}>\n'
        '            <div className="field">\n'
        '              <label>URL Cloudflare Worker *</label>\n'
        "              <input value={bpWorkerUrl} onChange={e=>setBpWorkerUrl(e.target.value)} placeholder=\"https://billplz-proxy.yourname.workers.dev\" style={{width:'100%'}}/>\n"
        '              <div className="muted" style={{fontSize:11, marginTop:4}}>Deploy Worker menggunakan fail billplz-worker.js, kemudian tampal URL di sini.</div>\n'
        '            </div>\n'
        '            <div className="field">\n'
        '              <label>ID Koleksi Billplz *</label>\n'
        "              <input value={bpCollId} onChange={e=>setBpCollId(e.target.value)} placeholder=\"aou6h6qp\" style={{width:'100%'}}/>\n"
        '              <div className="muted" style={{fontSize:11, marginTop:4}}>Dijumpai dalam papan pemuka Billplz → Koleksi → lajur ID.</div>\n'
        '            </div>\n'
        '            <button className="btn accent" style={{alignSelf:\'flex-start\'}} onClick={()=>{\n'
        '              const _url = bpWorkerUrl.trim().replace(/\\/$/, "");\n'
        '              const _coll = bpCollId.trim() || "aou6h6qp";\n'
        '              if (!DATA.billplzSettings) DATA.billplzSettings = {};\n'
        '              DATA.billplzSettings.workerUrl = _url;\n'
        '              DATA.billplzSettings.collectionId = _coll;\n'
        "              try { localStorage.setItem('atak-bp-settings', JSON.stringify({workerUrl:_url, collectionId:_coll})); } catch {}\n"
        "              push('Tetapan Billplz disimpan ✓');\n"
        '            }}>Simpan tetapan</button>\n'
        '          </div>\n'
        '        </div>\n'
        '      )}\n'
        '\n'
        '      {/* ── MODAL: PROFIL PELAJAR'
    )
    src = apply_replacement(
        src,
        '      {/* ── MODAL: PROFIL PELAJAR',
        SETTINGS_PANEL,
        'ManageView: add Billplz settings panel',
    )

    return src


# ── 577c0d01 patches ──────────────────────────────────────────────────────────

def patch_577c0d01(src: str) -> str:
    """Add billplzSettings to DATA."""
    src = apply_replacement(
        src,
        '  documents: [',
        (
            '  billplzSettings: {\n'
            "    workerUrl: '',\n"
            "    collectionId: 'aou6h6qp',\n"
            '  },\n'
            '  documents: ['
        ),
        'DATA: add billplzSettings',
    )
    return src


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f'Reading {SRC}…')
    with open(SRC, 'r', encoding='utf-8') as f:
        html = f.read()

    # Parse manifest
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        sys.exit('ERROR: __bundler/manifest not found in HTML')

    manifest_raw = m.group(2)
    manifest = json.loads(manifest_raw)

    PATCHES = {
        'bab51bd9-0d33-4c18-802c-7a8b44efbf66': patch_bab51bd9,
        '577c0d01-8cb3-46f5-a559-a2a032d7504b': patch_577c0d01,
    }

    for uuid, patch_fn in PATCHES.items():
        print(f'\nPatching module {uuid[:8]}…')
        mod = manifest[uuid]
        original = decompress_module(mod['data'])
        patched = patch_fn(original)
        if patched == original:
            print(f'  ⚠ No changes made to {uuid[:8]}')
        else:
            manifest[uuid]['data'] = compress_module(patched)
            print(f'  ✓ Module {uuid[:8]} updated')

    # Serialise manifest back (compact, no trailing space)
    new_manifest = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]

    print(f'\nWriting {DEST}…')
    with open(DEST, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print('Done ✓')


if __name__ == '__main__':
    main()
