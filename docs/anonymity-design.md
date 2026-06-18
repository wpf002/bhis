# BHIS Anonymity & Member Report Retrieval — Design Doc

**Status:** Draft for review
**Date:** 2026-06-18
**Owner:** Will Foti
**Related:** [ROADMAP.md](../ROADMAP.md) Phase 1 Week 2 (anonymity architecture), risk register ("Church weaponizes data against members" — Critical)

---

## The problem in one sentence

A member must be able to **retrieve their own report**, while the church **must not be able to link any response back to an individual** — and these two requirements pull in opposite directions, because both need some identifier attached to a session.

## Why the current schema leaks

In `backend/app/models/models.py`:

```
RespondentSession.user_id  → FK to users.id  (nullable)   # models.py:151
RespondentSession.anonymous_token → String                # models.py:152
User.church_id → FK to churches.id                        # models.py:48
```

A church admin legitimately holds their `church_id`. With the current model, a single join re-identifies every respondent:

```
responses → respondent_sessions → users (filtered by church_id) → first_name, last_name, email
```

The `anonymous_token` column suggests anonymity was intended, but **`user_id` being populated defeats it**. Worse, the roadmap's "optional account creation after survey" (Phase 2, Week 7) would back-fill `user_id` on completed sessions — turning a previously-anonymous response set into a fully-identified one retroactively.

**Conclusion: an anonymous session must never carry a church-resolvable `user_id`.** Identity and responses must be *severed at the data layer*, not merely hidden in the UI.

---

## Threat model

| Party | Trust | Must NOT be able to |
|---|---|---|
| **Church admin / leader** | Semi-trusted (the adversary we design against) | Link any response or individual score to a named member; view raw individual responses; defeat the minimum-N floor |
| **Member / respondent** | Owns their own data | Access anyone else's report |
| **Platform operator (BHIS/Will)** | Trusted-but-accountable | (Can technically access data for support; governed by TOS + audit, not by crypto in MVP) |
| **Outside attacker** | Untrusted | Anything (standard auth/transport security) |

The design defends primarily against the **church admin**, because that is the Critical risk in the register and the relationship most likely to be abused (a pastor pressuring a member, or a leader trying to find "who said the church has a trust problem").

We do **not** attempt to hide data from the platform operator in MVP — that would require end-to-end encryption and break server-side scoring. We treat operator access as a policy/audit control, and say so plainly in the privacy policy.

---

## Design principle: capability, not identity

A member retrieves their report by **possessing a secret token** (a capability), not by **being a known user** (an identity). The server resolves the token → session → score, and never needs to know *who* the holder is. The church never holds the token.

This is the same pattern as an unguessable "view your receipt" link.

### The report-access token

- On survey start (via invite link), the server creates a `RespondentSession` with:
  - `anonymous_token` — a high-entropy (≥128-bit) secret, returned to the member's browser and **never shown to the church**.
  - `user_id` = **NULL, always, for anonymous participation.** (See schema change below.)
- The member's report URL is `/report/{anonymous_token}` (or token in header). Whoever holds the token sees that report; nobody else can.
- The token is delivered to the member two ways, their choice:
  1. **Device-local** — stored in `localStorage`; "bookmark this page to return to your report."
  2. **Emailed link** — member optionally enters their email *to themselves*; we send the report link. The email address is stored **only** on a separate delivery record keyed by token, **never joined to `church_id`** and never exposed to church admins (see "Email delivery without re-identification").

---

## Schema changes

### 1. Sever identity from anonymous sessions

Do **not** populate `respondent_sessions.user_id` for survey participation. Two options:

- **Option A (minimal):** Keep the column but enforce `user_id IS NULL` for any session belonging to a survey instance. Add a CHECK or application-level invariant + a test. The column stays only for a future *non-anonymous* survey mode, if ever wanted.
- **Option B (cleaner, recommended):** Drop `user_id` from `respondent_sessions` entirely in a new migration. Sessions are identified solely by `anonymous_token`. Logged-in admins/leaders don't take surveys *as themselves* through this table.

Recommendation: **Option B.** It makes the severance structural — there is no column to accidentally populate, so the Week-7 account feature *cannot* re-identify anyone.

### 2. Email delivery without re-identification

New table, deliberately **not** linked to `users` or `churches`:

```
report_deliveries
  id              uuid pk
  session_token   string   # = respondent_sessions.anonymous_token (the capability)
  email           string   # member's own email, for sending the link only
  sent_at         datetime
  -- NO church_id, NO user_id, NO survey_instance_id
```

- Only the platform's email-send job reads this table. No API endpoint exposes it to church roles.
- A church admin querying their own data has no FK path from `church_id` to `report_deliveries`.

### 3. Optional account creation (resolving the Week-7 tension)

The roadmap wants "Create account to revisit your report." Make the account store **opaque report tokens**, not a back-link from session to user:

```
user_report_tokens
  id              uuid pk
  user_id         uuid fk → users.id
  session_token   string   # the capability the member already holds
  created_at      datetime
```

- The member, holding their token, can attach it to a newly-created account so they can find it later.
- Crucially: this table is keyed *from the user side*. A church admin cannot read another user's `user_report_tokens` (row-level access is restricted to the owning user). There is still **no church-visible join** from a response to a name.
- The session itself remains `user_id`-free. Account creation never writes back to `respondent_sessions`.

> Net effect: even a member who creates an account does not expose their responses to their church. The account is just a personal keyring of report tokens.

---

## Aggregation & the minimum-N floor

Severing identity is necessary but not sufficient — **small aggregates re-identify by inference.** If a pillar drilldown shows "1 respondent rated Trust at 12/100," the leader may know exactly who that is.

Rules (enforced server-side, in the aggregation/report layer — not the UI):

1. **Global floor:** no church report renders at all below `N_MIN` completed sessions (default **15**; configurable). Below the floor, the dashboard shows "Not enough responses yet to protect anonymity — need at least 15."
2. **Cell-level floor:** any *breakdown* (pillar drilldown, qualitative theme, sample response, segment) is suppressed if the subgroup behind it is below `N_MIN`. Show "Suppressed to protect anonymity," not the value.
3. **Qualitative responses are never shown verbatim to church roles by default.** Open-ended text is the highest re-identification risk (people write identifying detail). For pilot, qualitative themes are summarized by the platform (manual-LLM per the roadmap), and raw text is leadership-invisible. If verbatim quotes are ever surfaced, they pass an anonymization + N≥N_MIN gate.
4. **No "drill to individual."** There is no API path from an aggregate to an individual score for any church role. Individual scores are reachable only via the member's own capability token.

`N_MIN` lives in church/instance settings so a future enterprise customer can raise (never lower below the hard floor of, say, 10) it.

---

## Access-control matrix

| Data | Member (token) | Church admin/leader | Platform op |
|---|---|---|---|
| Own individual report | ✅ via token | ❌ | ⚠️ support-only, audited |
| Another member's report | ❌ | ❌ | ⚠️ support-only, audited |
| Raw individual responses | ✅ own only | ❌ | ⚠️ support-only, audited |
| Verbatim open-ended text | ✅ own only | ❌ (themes only) | ⚠️ audited |
| Church aggregate (N ≥ N_MIN) | — | ✅ | ✅ |
| Church aggregate (N < N_MIN) | — | ❌ suppressed | ✅ (ops/debug) |
| `report_deliveries` (emails) | — | ❌ | ⚠️ send-job only |

---

## What we are NOT claiming (be honest in the privacy policy)

- **Not** end-to-end encrypted. The platform can technically read responses; we rely on policy, access controls, and audit logging, not cryptography, to constrain operator access. State this plainly.
- **Not** anonymous against a determined platform-level insider. The guarantee is: *your church cannot identify you.* That is the promise that matters to a member deciding whether to be honest, and it is the one we can actually keep.
- **Not** protected against a member voluntarily writing their own name into an open-ended answer — hence themes-not-verbatim by default.

Saying exactly this on the consent screen builds more trust than an overbroad "100% anonymous" claim that a sharp pastor will poke holes in.

---

## Implementation checklist (maps to Phase 1 Week 2)

- [x] Migration: drop `respondent_sessions.user_id` (Option B) — `0002_anonymity` (commit 836035a)
- [x] Generate ≥128-bit `anonymous_token` on session create; return to client only — `generate_capability_token()` (~256-bit)
- [x] Token retrieval resolves session → score with no identity lookup — `GET /reports/individual/by-token/{token}`
- [x] `user_report_tokens` table for optional post-survey account (keyring) — `/reports/claim`, `/reports/mine`
- [x] No API path from aggregate → individual for any church role — verified by test
- [x] Global `N_MIN` floor (default 15) — `app/services/privacy.py` (commit 78603da)
- [x] Tests: church admin can't reach an individual; aggregate suppressed below N_MIN; keyring is per-user — `tests/test_api_anonymity.py` (12 tests)
- [x] `report_deliveries` **table** (severed from church/user FK) — created in `0002_anonymity`
- [ ] Email **send path** writing to `report_deliveries` — deferred to the transactional-email phase (Phase 1 Week 1; provider not yet integrated)
- [ ] Cell-level `N_MIN` suppression on segment breakdowns — deferred until segmentation lands (aggregate has no per-segment counts yet)
- [ ] Open-ended verbatim excluded once a qualitative endpoint exists — current church endpoints expose only aggregates
- [ ] Consent screen copy reflects the honest guarantee above — Phase 2 (frontend)

---

## Decisions (resolved 2026-06-18)

1. **`N_MIN` = 15** (global + cell-level floor). Hard floor never configurable below 10.
2. **Report retrieval: all three paths** — device-local bookmark, optional email link, and optional post-survey account (the `user_report_tokens` keyring). All three resolve the same capability token; none populates a church-visible session→user link. The `report_deliveries` table (email) stays severed from `church_id`/`user_id` as specified above.
3. **Drop `respondent_sessions.user_id`** (Option B). Severance is structural — there is no column to accidentally populate, so neither the account feature nor any future code path can re-identify a respondent.

### Still open

4. **Operator access audit logging** — log platform-side access to individual data in MVP, or defer to Phase 4 with the rest of compliance? *(Leaning defer, but flagging.)*
