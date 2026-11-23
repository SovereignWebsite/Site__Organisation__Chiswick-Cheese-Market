// Edit with the keeper (chiswick-cheese-market.c, 23 November 2026, at Dinis Cruz's word: "putting this to the side and
// the whole messaging workflow ... this pane should be on the left with the website on the right"). The site runs in the
// frame on the right; the pane on the left is the conversation. Each request is sealed to the keeper's key and signed
// with the requester's browser key (as ../send.js), and carries the page shown on the right. What was sent is kept in
// this browser only (localStorage: the words, the page and the time; never the pictures); the keeper's answers are
// sealed to the requester in ../replies/<label>.json and opened here, checked again every 30 seconds.
(() => {
    'use strict'
    const $ = s => document.querySelector(s)
    const b64 = bytes => { let s = ''; for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b); return btoa(s) }
    const unpem = pem => Uint8Array.from(atob(pem.replace(/-----[^-]+-----/g, '').replace(/\s/g, '')), c => c.charCodeAt(0))
    const KR = () => window.WSKeyring
    let CFG = null, images = [], replies = [], page = '/'

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
        if (!r.ok) throw new Error(r.status === 413 ? 'that is too big for one message: try fewer or smaller pictures' : r.status === 507 ? 'the inbox is full until the keeper reads it' : `the inbox answered ${r.status}`)
    }
    function shrink(file) {
        return new Promise((ok, no) => {
            const img = new Image(), url = URL.createObjectURL(file)
            img.onload = () => {
                const k = Math.min(1, 1600 / Math.max(img.width, img.height)), cv = document.createElement('canvas')
                cv.width = Math.round(img.width * k); cv.height = Math.round(img.height * k)
                cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height); URL.revokeObjectURL(url)
                ok({ name: file.name || 'screenshot.jpg', type: 'image/jpeg', data: cv.toDataURL('image/jpeg', 0.85) })
            }
            img.onerror = () => no(new Error('that picture could not be read')); img.src = url
        })
    }
    function say(t, bad) { const el = $('#status'); el.textContent = t; el.className = bad ? 'status bad' : 'status' }

    // what this browser sent, kept here only
    const store = {
        key: () => 'ccm.thread.' + (KR().person || ''),
        get() { try { return JSON.parse(localStorage.getItem(this.key()) || '[]') } catch { return [] } },
        add(m) { try { const l = this.get(); l.push(m); localStorage.setItem(this.key(), JSON.stringify(l.slice(-200))) } catch { } }
    }
    function render() {
        const box = $('#thread'), mine = store.get().map(m => ({ ...m, who: 'me' })), all = mine.concat(replies).sort((a, b) => String(a.at).localeCompare(String(b.at)))
        if (!all.length) return
        const atEnd = box.scrollHeight - box.scrollTop - box.clientHeight < 40
        box.innerHTML = ''
        for (const m of all) {
            const d = document.createElement('div'); d.className = 'msg ' + m.who
            const meta = document.createElement('span'); meta.className = 'meta'
            const when = m.at ? new Date(m.at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''
            meta.textContent = (m.who === 'me' ? 'You' : 'The keeper') + (when ? ', ' + when : '') + (m.page ? ' · ' + m.page : m.re ? ' · ' + m.re : '') + (m.pictures ? ` · ${m.pictures} picture${m.pictures > 1 ? 's' : ''}` : '')
            d.appendChild(meta); d.appendChild(document.createTextNode(m.text || '')); box.appendChild(d)
        }
        if (atEnd || all.length === 1) box.scrollTop = box.scrollHeight
    }
    async function loadReplies() {
        const who = KR().person; if (!who) return
        let list = []
        try { const r = await fetch(`../replies/${who}.json`, { cache: 'no-store' }); if (r.ok) list = await r.json() } catch { }
        const out = []
        for (const env of list) {
            try { const m = await KR().open(env); out.push({ who: 'them', at: m.at || env.at, re: m.re, text: m.text }) }
            catch { out.push({ who: 'them', at: env.at, text: 'An answer this browser cannot open.' }) }
        }
        if (JSON.stringify(out) !== JSON.stringify(replies)) { replies = out; render() }
    }

    // the page on the right
    function track() {
        try { const l = $('#site').contentWindow.location; page = l.pathname + l.search + l.hash } catch { page = '(another site)' }
        $('#onpage').textContent = page
        try { history.replaceState(null, '', '?page=' + encodeURIComponent(page)) } catch { }
    }

    async function send(ev) {
        ev.preventDefault()
        const text = $('#text').value.trim()
        if (!text && !images.length) return say('Write something first.', true)
        $('#send').disabled = true; say('Sealing and sending...')
        try {
            const body = { kind: 'request', text, images, page }, items_json = JSON.stringify(body)
            const signed = { person: KR().person, key: KR().fingerprint, alg: 'ECDSA-P256-SHA256-P1363', sig: await KR().sign(items_json) }
            const at = new Date().toISOString()
            await append(JSON.stringify({ type: 'ccm.request/v1', to: CFG.agent, site: location.origin, sent_at: at, from: KR().person, signed, items_json }))
            store.add({ at, text, page, pictures: images.length })
            $('#text').value = ''; images = []; $('#thumbs').innerHTML = ''
            say('Sent. The keeper answers here.'); render()
        } catch (e) { say('Not sent: ' + e.message, true) } finally { $('#send').disabled = false }
    }

    // the key: QR picture pasted, dropped or chosen, or the link pasted (as ../send.js)
    let jsqrLoad = null
    const loadJsQR = () => (jsqrLoad = jsqrLoad || new Promise((ok, no) => {
        const sc = document.createElement('script'); sc.src = '/vendor/jsqr-1.4.0/jsQR.js'
        sc.onload = () => ok(window.jsQR); sc.onerror = () => no(new Error('the QR reader could not be loaded')); document.head.append(sc)
    }))
    async function qrFrom(src, w, h) {
        if ('BarcodeDetector' in window) { try { const c = await new BarcodeDetector({ formats: ['qr_code'] }).detect(src); if (c.length) return c[0].rawValue } catch { } }
        const jsQR = await loadJsQR(), k = Math.min(1, 1600 / Math.max(w, h)), cv = document.createElement('canvas')
        cv.width = Math.round(w * k); cv.height = Math.round(h * k)
        const cx = cv.getContext('2d'); cx.drawImage(src, 0, 0, cv.width, cv.height)
        const r = jsQR(cx.getImageData(0, 0, cv.width, cv.height).data, cv.width, cv.height); return r ? r.data : null
    }
    async function useKeyText(t) {
        try { await KR().add(t); $('#keylink').value = ''; await showWho(); $('#text').focus(); say('Key added. Browse on the right and write here.') }
        catch (e) { say(e.message, true); $('#who').textContent = e.message }
    }
    const pictures = l => [...l].filter(f => f && f.type && f.type.startsWith('image/'))
    async function takePictures(files) {
        const imgs = pictures(files); if (!imgs.length) return
        if (!KR().person) {
            try { const bmp = await createImageBitmap(imgs[0]), t = await qrFrom(bmp, bmp.width, bmp.height); if (t && /key=/.test(t)) return useKeyText(t) } catch { }
            $('#who').textContent = 'No key found in that picture. Try the QR code itself, or paste the link.'; return
        }
        for (const f of imgs) {
            if (images.length >= 4) { say('Four pictures at most in one request.', true); break }
            try { const im = await shrink(f); images.push(im); const t = document.createElement('img'); t.src = im.data; t.alt = ''; $('#thumbs').appendChild(t) } catch (x) { say(x.message, true) }
        }
    }

    async function showWho() {
        await KR().ready
        const who = KR().person
        document.body.classList.toggle('has-key', !!who); $('#wholine').classList.toggle('has-key', !!who)
        $('#who').textContent = who ? `Signed in as ${who}` : 'Add your key to talk to the keeper.'
        $('#lock').hidden = !who; $('#form').hidden = !who; $('#addkey').hidden = !!who
        if (who) { render(); loadReplies() }
    }

    async function main() {
        const want = new URLSearchParams(location.search).get('page')
        if (want && want.startsWith('/') && !want.startsWith('//') && !want.startsWith('/send/edit')) $('#site').src = want
        $('#site').addEventListener('load', track)
        try { CFG = await (await fetch('../inbox.json', { cache: 'no-store' })).json() } catch { say('The inbox details could not be loaded.', true) }
        $('#form').addEventListener('submit', send)
        $('#text').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) $('#form').requestSubmit() })
        $('#files').addEventListener('change', e => { takePictures(e.target.files); e.target.value = '' })
        $('#qrfile').addEventListener('change', e => { takePictures(e.target.files); e.target.value = '' })
        $('#keylink').addEventListener('input', e => { if (/key=[A-Za-z0-9_-]{100,}/.test(e.target.value)) useKeyText(e.target.value) })
        $('#lock').addEventListener('click', async () => { await KR().lock(); replies = []; $('#thread').innerHTML = '<p class="empty">Your key is removed from this browser.</p>'; showWho() })
        $('#fold').addEventListener('click', () => { const f = document.body.classList.toggle('folded'); $('#fold').textContent = f ? 'Show the conversation' : 'Hide the conversation'; $('#fold').setAttribute('aria-expanded', String(!f)) })
        document.addEventListener('paste', e => {
            const cd = e.clipboardData; if (!cd) return
            const files = [...cd.items].filter(i => i.kind === 'file').map(i => i.getAsFile())
            if (pictures(files).length) { e.preventDefault(); return takePictures(files) }
            const t = cd.getData('text') || ''
            if (!KR().person && /key=[A-Za-z0-9_-]{100,}/.test(t)) { e.preventDefault(); useKeyText(t) }
        })
        const over = on => document.documentElement.classList.toggle('dropping', on)
        window.addEventListener('dragover', e => { if ([...(e.dataTransfer?.items || [])].some(i => i.kind === 'file')) { e.preventDefault(); over(true) } })
        window.addEventListener('dragleave', e => { if (!e.relatedTarget) over(false) })
        window.addEventListener('drop', e => { over(false); if (e.dataTransfer?.files?.length) { e.preventDefault(); takePictures(e.dataTransfer.files) } })
        await showWho()
        setInterval(loadReplies, 30000)
    }
    main()
})()
