// Send a request to this site's keeper (chiswick-cheese-market.c, 22 November 2026, after kate-curtis-evans.b's
// admin/message/message.js of 20 November 2026). Built on SGit-AI__Website__Web-Summit's
// assets/feedback.js (Apache-2.0): the message is sealed to the agent's public key with sgit's hybrid envelope v2
// (byte-compatible with PKI__Crypto.hybrid_decrypt), signed with the person's key held in this browser
// (keyring.js), and appended to the keeper's lane on its sgit vault. The lane token can only append.
// Replies from the agent are sealed to the person (ws-ecies-1) in replies/<person>.json; only this browser opens them.
(() => {
    'use strict'
    const $ = s => document.querySelector(s)
    const b64 = bytes => { let s = ''; for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b); return btoa(s) }
    const unpem = pem => Uint8Array.from(atob(pem.replace(/-----[^-]+-----/g, '').replace(/\s/g, '')), c => c.charCodeAt(0))
    let CFG = null, images = []

    async function seal(pem, text) {
        const subtle = crypto.subtle
        const pub = await subtle.importKey('spki', unpem(pem), { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['encrypt'])
        const aes = await subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt'])
        const iv = crypto.getRandomValues(new Uint8Array(12))
        const c = await subtle.encrypt({ name: 'AES-GCM', iv, tagLength: 128 }, aes, new TextEncoder().encode(text))
        const w = await subtle.encrypt({ name: 'RSA-OAEP' }, pub, await subtle.exportKey('raw', aes))
        return btoa(JSON.stringify({ v: 2, w: b64(w), i: b64(iv), c: b64(c) }))
    }
    async function append(text) {
        const enc = await seal(CFG.recipient.encrypt, text)
        const r = await fetch(`${CFG.endpoint}/api/vault/append/write/${CFG.vault_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ append_token: CFG.append_token, payload: btoa(enc) }) })
        if (!r.ok) throw new Error(r.status === 413 ? 'that is too big for one message: try a smaller photo' : r.status === 507 ? 'the inbox is full until the keeper reads it' : `the inbox answered ${r.status}`)
    }
    // photos: scaled to at most 1600 px on the long side, as JPEG, so a message stays well under the service's limit (a request must be under 6 MiB, measured by feedback.b, 21 Nov 2026)
    function shrink(file) {
        return new Promise((ok, no) => {
            const img = new Image(), url = URL.createObjectURL(file)
            img.onload = () => {
                const k = Math.min(1, 1600 / Math.max(img.width, img.height)), cv = document.createElement('canvas')
                cv.width = Math.round(img.width * k); cv.height = Math.round(img.height * k)
                cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height); URL.revokeObjectURL(url)
                ok({ name: file.name, type: 'image/jpeg', data: cv.toDataURL('image/jpeg', 0.85) })
            }
            img.onerror = () => no(new Error(`${file.name} is not an image this browser can read`)); img.src = url
        })
    }
    function say(t, bad) { const el = $('#status'); el.textContent = t; el.className = bad ? 'status bad' : 'status ok' }

    async function showWho() {
        const KR = window.WSKeyring; await KR.ready
        const who = KR.person, name = who
        $('#req').classList.toggle('has-key', !!who)
        $('#who').textContent = who ? `Signed in as ${name} (key ...${(KR.fingerprint || '').slice(-4)})` : 'No key in this browser yet.'
        $('#lock').hidden = !who; $('#form').hidden = !who
        $('#addkey').open = !who; $('#addkey').querySelector('summary').textContent = who ? 'Use a different key' : 'Add your key'
        if (who) showReplies(who)
    }
    async function showReplies(who) {
        const box = $('#replies'); box.innerHTML = ''
        let list = []
        try { const r = await fetch(`replies/${who}.json`, { cache: 'no-store' }); if (r.ok) list = await r.json() } catch { }
        if (!list.length) { box.innerHTML = '<p class="muted">No answers yet. When the keeper answers, it appears here, readable only in this browser.</p>'; return }
        for (const env of list.slice().reverse()) {
            const d = document.createElement('article'); d.className = 'reply'
            try { const m = await window.WSKeyring.open(env); d.innerHTML = `<p class="when"></p><p class="text"></p>`; d.querySelector('.when').textContent = `${m.at || env.at} · ${m.re ? 'about: ' + m.re : ''}`; d.querySelector('.text').textContent = m.text }
            catch (e) { d.textContent = 'A reply this browser cannot open (' + e.message + ').' }
            box.appendChild(d)
        }
    }
    async function send(ev) {
        ev.preventDefault()
        const KR = window.WSKeyring, kind = $('#kind').value, text = $('#text').value.trim()
        if (!text && !images.length) return say('Write something first.', true)
        $('#send').disabled = true; say('Sealing and sending...')
        try {
            const body = { kind, text, images }, items_json = JSON.stringify(body)
            const signed = { person: KR.person, key: KR.fingerprint, alg: 'ECDSA-P256-SHA256-P1363', sig: await KR.sign(items_json) }
            await append(JSON.stringify({ type: 'ccm.request/v1', to: CFG.agent, site: location.origin, sent_at: new Date().toISOString(), from: KR.person, signed, items_json }))
            $('#text').value = ''; images = []; $('#files').value = ''; $('#thumbs').innerHTML = ''
            say('Sent. The keeper reads its inbox, acts on it within the policy, and answers here.')
        } catch (e) { say('Not sent: ' + e.message, true) } finally { $('#send').disabled = false }
    }
    async function addKey() {
        try { const p = await window.WSKeyring.add($('#keylink').value); $('#keylink').value = ''; say(`Key added for ${p}.`); showWho() }
        catch (e) { say(e.message, true) }
    }
    async function main() {
        try { CFG = await (await fetch('inbox.json', { cache: 'no-store' })).json() } catch { return say('The inbox details could not be loaded.', true) }
        $('#form').addEventListener('submit', send)
        $('#addbtn').addEventListener('click', addKey)
        $('#lock').addEventListener('click', async () => { await window.WSKeyring.lock(); say('Your key is removed from this browser.'); showWho() })
                $('#files').addEventListener('change', async e => {
            images = []; $('#thumbs').innerHTML = ''
            for (const f of [...e.target.files].slice(0, 4)) {
                try { const im = await shrink(f); images.push(im); const t = document.createElement('img'); t.src = im.data; t.alt = ''; $('#thumbs').appendChild(t) } catch (x) { say(x.message, true) }
            }
        })
        showWho()
    }
    main()
})()
