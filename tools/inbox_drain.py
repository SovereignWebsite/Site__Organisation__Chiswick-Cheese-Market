#!/usr/bin/env python3
"""Drain this site's inbox (chiswick-cheese-market.c, 22 November 2026, at Dinis Cruz's word). After
kate-curtis-evans.b's tools/inbox_drain.py, itself after SGit-AI__Website__Web-Summit's admin/tools/feedback_drain.py (Apache-2.0).

    python3 -I tools/inbox_drain.py [--creds ~/.sg-send/lanes/chiswick-cheese-market-c.json] [--dry]

Lists the lane with the enum key, fetches what is pending, opens each envelope with the keeper's private key (sgit's key
store; passphrase from SG_SEND_PASSPHRASE or ~/.sw-secret/pass), checks the sender's ECDSA signature against
site/send/requesters.json, writes each message into the inbox vault (messages/<date>/<id>.json, photos beside it),
commits and pushes the vault, and only then marks the lane files processed: a failed push loses nothing.

Only messages signed by a named requester's active key are written in full and printed for the keeper, who acts on them
only within site/policy/abp.json site_requests. Anything else is recorded as its id, time, length and why, never its
words: a stranger's text never reaches the keeper. Prints no credential.
"""
import argparse, base64, json, os, re, subprocess, sys, urllib.error, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(c, op, body):
    req = urllib.request.Request(f"{c['host']}/api/vault/append/{op}/{c['vault_id']}", data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'x-sgraph-vault-enum-key': c['enum_key']})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'inbox_drain: {op} failed with {e.code}')


def verify(msg):
    sg = msg.get('signed')
    if not sg:
        return False, 'unsigned'
    try:
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives import hashes
        keys = json.load(open(os.path.join(ROOT, 'site', 'send', 'requesters.json')))['keys']
        k = next((k for k in keys if k['person'] == sg.get('person') and k['fingerprint'] == sg.get('key') and k.get('status') == 'active'), None)
        if not k:
            return False, f"no active published key {sg.get('key')} for {sg.get('person')}"
        b = lambda x: int.from_bytes(base64.urlsafe_b64decode(x + '=' * (-len(x) % 4)), 'big')
        pub = ec.EllipticCurvePublicNumbers(b(k['sign']['x']), b(k['sign']['y']), ec.SECP256R1()).public_key()
        raw = base64.b64decode(sg['sig'])
        pub.verify(utils.encode_dss_signature(int.from_bytes(raw[:32], 'big'), int.from_bytes(raw[32:], 'big')), msg['items_json'].encode(), ec.ECDSA(hashes.SHA256()))
        return True, f"signed by {sg['person']} (verified, key {sg['key']})"
    except Exception as e:
        return False, f'signature invalid ({type(e).__name__})'


def main():
    a = argparse.ArgumentParser(); a.add_argument('--creds', default='~/.sg-send/lanes/chiswick-cheese-market-c.json'); a.add_argument('--dry', action='store_true')
    o = a.parse_args(); c = json.load(open(os.path.expanduser(o.creds)))
    entries, after = [], None
    while True:
        r = call(c, 'list', {'include_content': False, **({'after_file_id': after} if after else {})})
        page = r.get('entries', []); entries += page
        if not r.get('truncated') or not page:
            break
        after = page[-1]['file_id']
    mine = [e for e in entries if e.get('inbox') == c['append_token']]
    if not mine:
        print('inbox_drain: the inbox is empty'); return
    if o.dry:
        print(f'inbox_drain: {len(mine)} pending (dry run)'); return
    from sgit_ai.crypto.PKI__Crypto import PKI__Crypto
    from sgit_ai.crypto.pki.PKI__Key_Store import PKI__Key_Store
    crypto = PKI__Crypto()
    pw = os.environ.get('SG_SEND_PASSPHRASE') or open(os.path.expanduser('~/.sw-secret/pass')).read().strip()
    key = PKI__Key_Store(keys_dir=os.path.expanduser('~/.sg-send/keys'), crypto=crypto).load_key_pair(c['recipient'], pw)['encryption_private']
    vault = c['vault_dir']; done, acted = [], []
    for k in range(0, len(mine), 20):
        ids = [e['file_id'] for e in mine[k:k + 20]]
        for f in call(c, 'fetch', {'inbox': c['append_token'], 'file_ids': ids}).get('files', []):
            fid = f['file_id'].replace('.enc', '')
            try:
                plain = crypto.hybrid_decrypt(key, base64.b64decode(f['content']))['plaintext']
                msg = json.loads(plain if isinstance(plain, str) else plain.decode())
            except Exception as e:
                print(f'inbox_drain: {fid} could not be opened ({type(e).__name__}); left pending'); continue
            ok, why = verify(msg)
            day = datetime.now(timezone.utc).date().isoformat(); d = os.path.join(vault, 'messages', day); os.makedirs(d, exist_ok=True)
            if not ok:
                rec = {'lane_file': f['file_id'], 'drained_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'status': why, 'length': len(plain)}
                open(os.path.join(d, f'{fid}.json'), 'w').write(json.dumps(rec, indent=1) + '\n')
            else:
                body = json.loads(msg['items_json'])
                for n, im in enumerate(body.get('images', []), 1):
                    data = re.sub(r'^data:[^,]*,', '', im.get('data', ''))
                    name = f'{fid}-{n}.jpg'; open(os.path.join(d, name), 'wb').write(base64.b64decode(data)); im['data'] = name
                rec = {'lane_file': f['file_id'], 'from': msg['signed']['person'], 'verified': why, 'sent_at': msg.get('sent_at'), **body}
                open(os.path.join(d, f'{fid}.json'), 'w').write(json.dumps(rec, indent=1, ensure_ascii=False) + '\n')
                acted.append((fid, rec, d))
            done.append(f['file_id'])
    if not done:
        print('inbox_drain: nothing opened'); return
    for cmd in (['sgit', 'commit', f'inbox: {len(done)} message(s), {len(acted)} signed'], ['sgit', 'push']):
        p = subprocess.run(cmd, cwd=vault, capture_output=True, text=True)
        if p.returncode:
            raise SystemExit(f'inbox_drain: {" ".join(cmd[:2])} failed; lane files stay pending')
    moved = len(call(c, 'mark-processed', {'inbox': c['append_token'], 'file_ids': done}).get('moved', []))
    print(f'inbox_drain: {len(done)} message(s), {len(acted)} signed by a named requester, {len(done) - len(acted)} not acted on; marked processed {moved}')
    for fid, rec, d in acted:
        imgs = ', '.join(os.path.join(d, i['data']) for i in rec.get('images', []))
        print(f"\n--- {fid} from {rec['from']} ({rec['verified']}), {rec.get('sent_at')}\nkind: {rec.get('kind')}\n{rec.get('text')}" + (f'\nphotos: {imgs}' if imgs else ''))


if __name__ == '__main__':
    main()
