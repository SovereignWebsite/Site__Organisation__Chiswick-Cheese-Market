#!/usr/bin/env node
// Reply on the Messages page (after kate-curtis-evans.b's tools/reply.mjs, 20 Nov 2026; chiswick-cheese-market.c, 22 Nov 2026): seals the reply to the person's
// published key (ws-ecies-1, as tools/person-key.mjs seal) and appends it to site/data/replies/<person>.json, which only
// their browser can open. Publish the site afterwards.
//   node tools/reply.mjs --person dinis --re "<what it answers>" --text "<the reply>"
import fs from 'fs'; import path from 'path'; import crypto from 'crypto'
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..')
const args = process.argv.slice(2), opt = k => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : undefined }
const person = opt('person'), text = opt('text'), re = opt('re') || ''
if (!person || !text) { console.error('usage: --person <label> --text "<reply>" [--re "<subject>"]'); process.exit(1) }
const keys = JSON.parse(fs.readFileSync(path.join(ROOT, 'site/data/site-requesters.json'), 'utf8')).keys
const k = keys.find(x => x.person === person && x.status === 'active'); if (!k) { console.error('no active key for ' + person); process.exit(1) }
const at = new Date().toISOString().replace(/\.\d+Z$/, 'Z'), eph = crypto.generateKeyPairSync('ec', { namedCurve: 'prime256v1' })
const secret = crypto.diffieHellman({ privateKey: eph.privateKey, publicKey: crypto.createPublicKey({ key: k.encrypt, format: 'jwk' }) })
const key = Buffer.from(crypto.hkdfSync('sha256', secret, Buffer.alloc(0), Buffer.from('ws-ecies-1'), 32)), iv = crypto.randomBytes(12)
const c = crypto.createCipheriv('aes-256-gcm', key, iv), ct = Buffer.concat([c.update(Buffer.from(JSON.stringify({ at, re, text, by: 'chiswick-cheese-market.c' }))), c.final(), c.getAuthTag()])
const e = eph.publicKey.export({ format: 'jwk' })
const env = { v: 'ws-ecies-1', to: person, key: k.fingerprint, by: 'chiswick-cheese-market.c', at, epk: { kty: 'EC', crv: 'P-256', x: e.x, y: e.y }, iv: iv.toString('base64'), ct: ct.toString('base64') }
const f = path.join(ROOT, 'site/data/replies', person + '.json'); fs.mkdirSync(path.dirname(f), { recursive: true })
const list = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : []; list.push(env)
fs.writeFileSync(f, JSON.stringify(list.slice(-50), null, 1) + '\n'); console.log(`reply sealed to ${person} (${k.fingerprint}): site/data/replies/${person}.json`)
