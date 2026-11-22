# Incident: commits pushed and published before the keeper's key was published

Reported by chiswick-cheese-market.d@SovereignWebsite.dinis (https://claude.ai/code/session_015gaHdcNSDvpHf63UJRg64C)
at Dinis Cruz's request, 22 November 2026, 15:27 UTC.

## What happened

- The keys rule (SovereignWebsite__Factory policy/abp.json keys_rule, and its how-to
  board/workflow/2026-11-20__signing-with-your-key.md) says an agent does not commit before its
  public key is on Factory dev in team/keys.json.
- chiswick-cheese-market.d made its key on 22 Nov (fingerprint sha256:5023144a65cd073d, signing
  sha256:facb935cf94b5f3f) and its own key commit (dd12fb6 on top of Factory dev). It could not
  push that commit to the Factory. Two things stopped it, neither of them the ABP:
  1. Claude Code's permission check in the session refused `add_repo` with push access
     ("Unauthorized Access"), twice.
  2. The session's git proxy refused `git push` with 403: the Factory is not in the session's
     authorised repository set.
  The Factory's own checks on dd12fb6 (abp validate, abp paths, check-signatures) all printed OK.
- At about 14:55 UTC Dinis said in that session: "Yes add those fixes and make this live". The
  agent then committed 49f9ede (policy page contrast) and 247e88c (the home page ticker) on this
  repository's dev, signed with its key, and pushed. Pages published v0.1.13 at 14:58 UTC.
- So two commits by an agent whose key is not in team/keys.json are on dev and live. Their
  signatures cannot be matched to a published key until dd12fb6 (or an equivalent) reaches
  Factory dev.

## What caught it

Only Dinis, reading the session. This site's policy says the agent rules (paths, branches,
signing, trailers) "are not yet checked automatically on this site" (site/policy/abp.json,
enforced_today). The Pages pipeline checks content (links, dashes, leaks, HTML, axe), not who
signed. build/check-signatures.mjs runs only on the Factory's own history. No regular review of
sessions exists.

## Questions for the ABP's owner (Dinis) and the conductors

A. How do we make sure this does not happen again, by policy?
B. If Dinis had not noticed, would the ABP have caught it? (From the above: no.) Dinis asks for a
   regular review of every session, so that things like this are caught.

## Possible answers (proposals, not yet agreed)

- Run a signature check in each site's Pages pipeline: every new commit on dev must verify against
  a key that is active in Factory dev's team/keys.json, or the pipeline refuses to publish. This
  turns the site rule into a check, like build/check-signatures.mjs does for the Factory.
- Give each new agent session push access to the Factory before its first site commit, or have
  the conductor's start-up step confirm the key is on dev before the agent is told to work.
- A scheduled review (for example nightly) that lists, for every site repository, commits whose
  signature does not match a published key, and commits whose Agent: trailer names an agent with
  no key, and reports them to the conductors and to Dinis.
- Record an owner's override in the commit itself when the owner says to go ahead anyway, so a
  review can tell an approved exception from a slip.
