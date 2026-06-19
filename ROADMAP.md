# BHIS Product Roadmap
## Biblical Health Intelligence System

**Last updated:** 2026-06-18
**Current status:** Phases 0–2 complete (backend + frontend live, 164 backend tests); next = Phase 3 (pilot launch / deployment)
**Target:** Paying pilot churches within 90 days of Phase 2 completion

---

## Revision Notes (2026-06-18)

This revision is grounded in a code audit of the actual scaffold. Key changes from the prior draft:

1. **Phase 0 claims corrected** to match the codebase (single migration file; unit-tests-only; Watermark doctrinal framework defined but not yet wired into scoring).
2. **New Phase 1.5 — Concierge Validation** inserted: validate questions, scoring, and pastor trust with 1–2 churches using the existing engine *before* the full hardening build.
3. **Transactional email moved into Phase 1** (was Phase 3) so email verification / password reset are testable end-to-end when built.
4. **Celery dropped from Phase 1** in favor of FastAPI `BackgroundTasks`; scoring stays synchronous at pilot scale. A real queue returns only when load demands it.
5. **S3 dependency deferred**; pilot PDFs served from the app.
6. **Privacy & anonymity architecture pulled into Phase 1/2** (was Phase 4/5): anonymity model, minimum-N floor, consent-at-survey-start.
7. **Watermark framework operationalization** added as an explicit Phase 1 task.
8. **Week 4 rule-based NLP cut**; qualitative analysis for pilot is manual-LLM (Claude API) during debrief prep. Productized NLP stays in Phase 6.
9. **Superadmin / audit endpoints deferred** out of the path-to-pilot.
10. **Capacity assumption made explicit** and timelines flagged as optimistic for a single developer (expect ~1.5–2×).

---

## Capacity & Timeline Assumptions

- **Team size assumed:** 1 primary developer unless otherwise staffed.
- The per-week scopes below are dense. Several individual weeks (notably the original Week 3) are closer to 3–4 weeks of single-developer work. **Treat all calendar durations as optimistic and plan for 1.5–2×.**
- Phase durations are ordered by dependency, not padded for slippage. Update this section if headcount changes.

---

## Roadmap Summary

| Phase | Name | Duration | Outcome |
|---|---|---|---|
| 0 | Foundation | ✅ Complete | Full project scaffold, scoring engine, 60 questions |
| 1.5 | Concierge Validation | 1–2 weeks | 1–2 churches' real data validates questions + scoring + trust |
| 1 | Backend Complete | ✅ Complete | All API endpoints production-ready, tested (164 tests), email-capable |
| 2 | Frontend Complete | ✅ Complete | Full survey + dashboard experience live, wired to backend |
| 3 | Pilot Launch | 6 weeks | 5–10 churches actively using BHIS |
| 4 | Pilot Iteration | 4 weeks | Feedback-driven refinement, second round pilots |
| 5 | Public Launch | 4 weeks | Self-serve onboarding, billing, public access |
| 6 | Intelligence Layer | 8 weeks | AI qualitative analysis, benchmarking, trends |
| 7 | Platform Features | 8 weeks | Multi-church networks, white-label, advanced reporting |

**Total to public launch:** ~22 weeks from Phase 1 start (single-dev: plan for more).

---

## Phase 0 — Foundation
### Status: ✅ Complete

**Delivered (verified against codebase):**
- Full monorepo: FastAPI backend + React/TypeScript frontend
- PostgreSQL schema — 13 tables, delivered in a **single initial Alembic migration** (`backend/alembic/versions/0001_initial.py`). Note: every Phase 1 schema change needs its own new migration.
- Scoring engine (`backend/app/services/scoring_engine.py`): pillar normalization, contradiction detection (7 pairs CP-01…CP-07), drift signals, composite weighting, maturity tiers (5)
- Archetype classification engine (`backend/app/services/archetype_engine.py`) — 12 church archetypes
- Recommendation engine — church + individual (rule-based)
- 60-question assessment bank — all 7 pillars, seeded via `backend/seeds/seed_questions.py`
- Doctrinal framework module (`backend/app/services/doctrinal_framework.py`) — Watermark Community Church Full Doctrinal Statement, 11 sections mapped to BHIS dimensions
  - ⚠️ **Defined but not yet operationalized:** the doctrinal weights are not applied to Q1–Q10 scoring. Wiring this in is a Phase 1 task (Week 3).
- Survey-taking flow (mobile-first, all question types)
- Leadership dashboard (radar chart, pillar bars, maturity distribution, trend line) — ⚠️ church_id hardcoded in `frontend/src/pages/Dashboard.tsx`
- Individual report page
- Admin survey management page
- Church onboarding flow
- Docker Compose for local development (Postgres + Redis + backend + frontend)
- **43 passing tests — unit tests of the scoring/archetype/recommendation engines only.** No API, auth, or DB integration tests exist yet.

**What Phase 0 does not include:**
- Email delivery
- Real authentication (no refresh token rotation, no email verification flow, no rate limiting, no 2FA)
- PDF report generation
- Billing
- Production deployment
- Qualitative (NLP) analysis
- Benchmark data (no comparison churches yet)
- Privacy/anonymity guarantees enforced in code
- API / integration test coverage

---

## Phase 1.5 — Concierge Validation
### Duration: 1–2 weeks
### Goal: Prove the thesis with real church data *before* spending 8 weeks hardening

The engine works and is tested. The unvalidated assumptions are not technical — they are: (1) do pastors find the diagnostic credible and valuable, (2) are the questions theologically sound and not off-putting, (3) does the archetype/scoring classification ring true. None of that requires production auth, queues, PDF, or billing. Validate it manually, cheaply, now.

**Setup**
- [ ] Deploy the scaffold somewhere reachable (or run locally + screen-share) — no production hardening required
- [ ] Recruit 1–2 friendly churches (existing relationships; theological diversity helpful — include one charismatic-adjacent church if possible to stress-test doctrine scoring)
- [ ] Members take the survey; you manually trigger `POST /scoring/individual` and `POST /scoring/church` (endpoints already exist)

**Validate (manual is fine — concierge)**
- [ ] Walk the pastor through the dashboard / hand-assembled report
- [ ] Run open-ended responses through the Claude API yourself for qualitative themes (no NLP build needed)
- [ ] Capture: which questions confused or felt loaded? Does the archetype match the pastor's self-understanding? Does the credibility/drift framing land or offend?

**Deliverables:**
- A prioritized list of question/scoring changes **before** Phase 1 hardens around them
- Early read on the doctrinal-bias risk with a non-Watermark-aligned church
- Go/no-go confidence on the core thesis

> Rationale: changing a question after Phase 2 polish is expensive; changing it now is free. This phase de-risks the 8 weeks that follow.

---

## Phase 1 — Backend Complete
### Duration: 4 weeks
### Goal: Every API endpoint is production-ready, tested, secure, and email-capable

> Changes from prior draft: transactional email pulled in (Week 1); Celery replaced by `BackgroundTasks`; S3 dropped; superadmin/audit endpoints deferred; privacy/anonymity architecture and Watermark wiring added.

---

### Week 1 — Auth hardening + email + church management

**Transactional email (moved up from Phase 3 — unblocks every email flow below)**
- [ ] Integrate an email provider (SendGrid free tier is sufficient for pilot)
- [ ] Send-email service abstraction with templated transactional sends
- [ ] Verify deliverability end-to-end before building flows that depend on it

**Auth**
- [ ] Refresh token rotation (invalidate old token on each refresh)
- [ ] Email verification flow (send verification email on register — now actually sendable)
- [ ] Password reset flow (forgot password → email link → reset)
- [ ] Rate limiting on `/auth/login` and `/auth/register` (wire Redis, which is already in compose but unused)
- [ ] Session management — track active sessions, allow revocation

**Church management**
- [ ] Church invite system — admin generates invite link for members
- [ ] Invite tokens table — `church_invites` (token, church_id, role, expires_at, used) — **new migration**
- [ ] `POST /churches/{id}/invites` — generate invite
- [ ] `POST /auth/register-via-invite` — register using invite token, auto-assign church + role
- [ ] Church settings endpoint — `PUT /churches/{id}/settings`
- [ ] Soft delete for churches (deactivate, not destroy)

**Deliverables:**
- Invite-based onboarding works end-to-end
- Auth is production-safe (token rotation, **working** email verification, rate limits)

---

### Week 2 — Survey flow hardening + response validation + anonymity model

**Anonymity & privacy architecture (pulled forward from Phase 4 — core to value prop AND the Critical risk in the register)**
> Design + decisions: [docs/anonymity-design.md](docs/anonymity-design.md). Key resolved choices: drop `respondent_sessions.user_id` (structural severance), capability-token report retrieval (bookmark + email + optional keyring account), `N_MIN` = 15.
- [ ] Migration: drop `respondent_sessions.user_id`; sessions identified by `anonymous_token` only
- [ ] Capability-token report retrieval — `GET /report/{token}`, no identity lookup; `report_deliveries` + `user_report_tokens` tables severed from `church_id`
- [ ] Minimum-N floor (default 15) — global + cell-level suppression on every aggregate breakdown; enforced server-side
- [ ] Aggregate-only default for all leadership views; raw individual responses and verbatim open-ended text never exposed to church admins
- [ ] Tests: church-admin JWT cannot reach any individual response/score; aggregate suppressed below N_MIN; account creation creates no church-visible session→user link

**Survey instances**
- [ ] Survey instance `close` endpoint — `POST /surveys/instances/{id}/close`
- [ ] Auto-close surveys past their `close_date` (background check; no queue needed)
- [ ] Survey instance status transitions enforced (draft → active → closed only)
- [ ] Anonymous survey participation — session creation without auth, via invite link

**Response validation**
- [ ] Prevent duplicate sessions (one per user per instance, or one per anonymous token)
- [ ] Validate all required non-open-ended questions answered before `complete` fires
- [ ] Response idempotency — re-submitting same question_id overwrites, does not duplicate
- [ ] Completion time tracking — enforce minimum (bot detection, < 2 min = flag)

**Question serving**
- [ ] Randomize option order for MC/scenario questions (prevent position bias)
- [ ] Return `question_count` and `estimated_minutes` with survey metadata
- [ ] Skip logic foundation — `question_conditions` table for Phase 6 — **new migration**

**Deliverables:**
- Survey flow is abuse-resistant
- Anonymous participation works (no login required for members)
- Duplicate responses impossible
- Anonymity is enforced in code, not just promised in a TOS

---

### Week 3 — Scoring pipeline + doctrinal wiring + report generation

**Scoring hardening (synchronous — no Celery)**
- [ ] Wire the Watermark doctrinal framework weights into Q1–Q10 scoring (currently defined but unused)
- [ ] Idempotent scoring — re-scoring a session produces same result, does not create duplicate
- [ ] Auto-trigger individual scoring on session complete via FastAPI `BackgroundTasks` (no manual call, no broker)
- [ ] Church aggregation trigger — auto-run after each new individual score (or batch on schedule)
- [ ] Contradiction flag persistence — store all 7 pairs regardless of flagged status
- [ ] Add `scored_at` and `score_version` to `individual_scores` for auditability — **new migration**

> Note: rule-based scoring of a single session is sub-millisecond and church aggregation of ~40 sessions is trivial. Celery/Redis-broker work is premature at pilot scale and is deferred until measured load requires it.

**PDF reports (served from the app — no S3 at pilot)**
- [ ] Install WeasyPrint + HTML report templates
- [ ] Individual PDF report template — score, pillar breakdown, recommendations, scripture anchors
- [ ] Church PDF report template — executive summary, all pillar charts, archetype, recommendations
- [ ] `POST /reports/individual/{session_id}/export` — generate via `BackgroundTasks` (PDF is the one genuinely slow op)
- [ ] `POST /reports/church/{instance_id}/export` — generate via `BackgroundTasks`
- [ ] `GET /reports/exports/{job_id}/download` — serve completed PDF from local/app storage (migrate to object storage when scale demands)

**Deliverables:**
- Doctrine pillar actually uses the Watermark framework
- Scoring is fully automated (no manual trigger from frontend)
- Both PDF reports generate and download correctly

---

### Week 4 — Qualitative (manual-LLM for pilot) + integration tests + observability

**Qualitative analysis — manual-LLM, not a rule-based build**
- [ ] For pilot, run open-ended responses (Q45, Q60) through the Claude API during debrief prep — anonymized first
- [ ] Capture themes/sentiment by hand into the report; no productized pipeline yet
- [ ] (Productized, in-app NLP stays in Phase 6 — building rule-based keyword/sentiment now is throwaway work that Phase 6 replaces)

**Integration tests (the real gap behind "production-ready")**
- [ ] API integration tests for the key flows: auth (401 on missing/invalid token), invite registration, survey session lifecycle, scoring trigger, report retrieval
- [ ] Role enforcement tested on every protected route
- [ ] Consistent error-shape assertions

**Observability**
- [ ] Sentry integration — error tracking on all exceptions
- [ ] Structured logging — every request logged with church_id, user_id, duration
- [ ] `/health` endpoint expanded — DB ping, Redis ping, uptime
- [ ] Request timing middleware — flag requests over 2s

**Deferred out of Phase 1 (revisit before public launch):**
- Superadmin role + `GET /admin/churches`, `/admin/usage`, `/admin/audit-logs` — not on the path to pilot; build when there are enough churches to administer.

**Deliverables:**
- Backend is genuinely production-ready *and* covered by integration tests
- Qualitative insight available for pilot debriefs without a throwaway NLP build

---

### Phase 1 Definition of Done
- [ ] All endpoints return consistent error shapes `{ detail, code, field? }`
- [ ] All auth-protected endpoints return 401 correctly on missing/invalid token
- [ ] Role enforcement tested on every protected route
- [ ] Transactional email sends and is verified end-to-end
- [ ] Watermark doctrinal framework is applied in Q1–Q10 scoring
- [ ] Anonymity enforced: aggregate-only leadership views + minimum-N floor
- [ ] PDF export works end-to-end for both report types
- [ ] Invite-based onboarding works end-to-end
- [ ] Anonymous survey participation works end-to-end
- [ ] Automated scoring fires without manual trigger
- [ ] Integration tests cover the key flows (in addition to the 43 engine unit tests)

---

## Phase 2 — Frontend Complete
### Duration: 4 weeks
### Goal: The full member and leader experience is polished and shippable

> Change from prior draft: informed-consent screen pulled in from Phase 4 (members and pastors will ask "is it anonymous?" on day one of pilot).

---

### Week 5 — Survey experience polish + consent

**Consent (pulled forward from Phase 4)**
- [ ] Informed-consent + anonymity explanation on the survey start screen (what's collected, that it's anonymous, how aggregates work)

**Survey taking**
- [ ] Auto-save progress to localStorage — reload resumes where left off
- [ ] Exit warning — "You'll lose your progress" if navigating away mid-survey
- [ ] Likert question visual redesign — horizontal scale with labels (not vertical list)
- [ ] Forced prioritization (Q10) — drag-and-drop ranking UI
- [ ] Open-ended questions — character counter, required minimum not enforced (encourages honesty)
- [ ] Question transition animations — smooth slide between questions
- [ ] Estimated time remaining display — updates dynamically based on pace
- [ ] Survey completion screen — brief message before redirect to report

**Mobile**
- [ ] Full mobile audit — test on iOS Safari, Android Chrome
- [ ] Touch targets minimum 44px
- [ ] No horizontal scroll on any screen width ≥ 375px
- [ ] Font sizes readable without zoom on mobile

**Deliverables:**
- Survey experience is genuinely pleasant on mobile
- Members understand the anonymity guarantee before they start
- No drop-off due to UX friction

---

### Week 6 — Individual report + leadership dashboard polish

**Individual report**
- [ ] Score reveal animation on page load (ring animates in)
- [ ] Expandable recommendation cards — diagnosis collapsed by default, expand to see intervention
- [ ] Print/download button — triggers PDF export API
- [ ] Scripture reference links — link to Bible Gateway
- [ ] "Share with pastor" option — generates a pastor-readable summary link (optional, opt-in)
- [ ] Credibility warning displayed with appropriate pastoral framing (not accusatory)
- [ ] No account required to view own report — accessible via session token in URL

**Leadership dashboard**
- [ ] Church ID no longer hardcoded — pulled from `localStorage.church_id` set during onboarding (replaces the hardcoded constant in `Dashboard.tsx`)
- [ ] Actions tab wired to live recommendation API — not static placeholder
- [ ] Pillar detail modal — click any pillar bar to see question-level breakdown and sample responses (respecting the minimum-N floor)
- [ ] Drift risk panel — dedicated section showing which specific questions flagged
- [ ] Qualitative themes panel — clustered open-ended themes (Q45 + Q60)
- [ ] Survey management inline — admin can launch/close surveys from dashboard
- [ ] Export buttons — download church PDF report from dashboard

**Deliverables:**
- Dashboard uses real data, not hardcoded values
- Both report types are fully functional end-to-end

---

### Week 7 — Onboarding + auth flows

**Auth UI**
- [ ] Email verification screen — "Check your email" holding page
- [ ] Email verification landing — `/verify-email?token=...`
- [ ] Forgot password page
- [ ] Reset password page
- [ ] Login error states — wrong password, unverified email, deactivated account
- [ ] Register page — for church admins (leaders use invite link)

**Onboarding**
- [ ] Onboarding flow routes to `/admin` after church creation
- [ ] Admin page shows next steps checklist: (1) Create survey, (2) Launch, (3) Copy invite link, (4) Share with congregation
- [ ] Invite link copy button — one click copies `/survey/{instanceId}?invite={token}` to clipboard
- [ ] Member landing page for invite links — brief explanation of what BHIS is before survey starts

**Member experience**
- [ ] `/join/{inviteToken}` — member landing page with church name, survey description, and Start button
- [ ] No login required for members — session created on survey start via invite token
- [ ] Optional account creation after survey — "Create account to revisit your report"

**Deliverables:**
- A church admin can onboard, launch a survey, and send a link to members in under 10 minutes
- Members can complete the survey without creating an account

---

### Week 8 — QA, performance, accessibility

**QA**
- [ ] End-to-end test: admin onboards → creates survey → launches → member completes → report generated → church aggregated → dashboard shows data
- [ ] Cross-browser: Chrome, Firefox, Safari, Edge
- [ ] Cross-device: desktop, tablet, mobile
- [ ] Error state testing — what happens when API is down, slow, returns 500
- [ ] Empty state testing — dashboard before any responses, report before scoring

**Performance**
- [ ] Dashboard initial load under 2s on 3G (lazy load charts)
- [ ] Survey question transitions under 100ms
- [ ] PDF generation under 10s for both report types
- [ ] API response time targets: auth < 200ms, survey questions < 300ms, scoring < 5s

**Accessibility**
- [ ] All interactive elements keyboard-navigable
- [ ] ARIA labels on all icon-only buttons
- [ ] Color contrast ratio ≥ 4.5:1 on all text
- [ ] Survey usable with screen reader (primary accessibility target)

**Deliverables:**
- Phase 2 complete — full product works end-to-end
- Ready for pilot churches

---

### Phase 2 Definition of Done
- [ ] Complete member flow works without an account (invite link → consent → survey → report)
- [ ] Complete leader flow works (onboard → launch → invite → dashboard → PDF export)
- [ ] Dashboard shows real data from the API throughout
- [ ] Anonymity guarantee visible to members and enforced in every leadership view
- [ ] All pages mobile-responsive
- [ ] Zero console errors in production build
- [ ] All auth flows work (register, verify, login, forgot, reset)

---

## Phase 3 — Pilot Launch
### Duration: 6 weeks
### Goal: 5–10 churches actively using BHIS, producing real diagnostic data

> Change from prior draft: SendGrid is already integrated in Phase 1, so Week 9 covers digest/notification templates and infra only. A **documented doctrinal stance** is required before onboarding non-Watermark-aligned churches.

---

### Week 9 — Production infrastructure

**Deployment**
- [ ] Railway.app deployment — backend service + PostgreSQL + Redis
- [ ] Frontend deployed to Vercel or Railway static
- [ ] Custom domain — `app.bhis.io` (or chosen domain)
- [ ] SSL certificates on all services
- [ ] Environment variable management — secrets not in codebase
- [ ] Database connection pooling — PgBouncer or Railway's built-in
- [ ] Automated database backups — daily, 30-day retention

**Email (provider already integrated in Phase 1 — this is templates + lifecycle)**
- [ ] Email templates: survey invite, report ready, survey completion notification, weekly digest
- [ ] Survey completion notification to church admin — "12 new responses this week"
- [ ] Weekly digest email to leaders — response count, completion rate

**Monitoring**
- [ ] Sentry configured for both backend and frontend
- [ ] Uptime monitoring — Betteruptime or similar, alert on downtime
- [ ] Error rate alerting — Sentry alert if error rate spikes
- [ ] Database query monitoring — identify slow queries before they hit users

**Deliverables:**
- BHIS is live on the internet at a real URL
- Email lifecycle works end-to-end
- Production errors are caught and alerted

---

### Week 10 — Pilot church onboarding

**Documented doctrinal stance (do this BEFORE onboarding a charismatic-adjacent church)**
- [ ] Write a short, defensible statement of what the Doctrinal Integrity pillar scores vs. does not, and why (the framework derives from one church's statement — Watermark)
- [ ] Confirm cessationism is not scored in MVP (already the intent); make this explicit to pilot pastors
- [ ] Have a plan for the feedback if a pastor flags doctrine scoring as biased (this is your highest-likelihood pilot conflict)

**Pilot church selection (target: 5–10 churches)**
- Criteria:
  - Senior pastor personally engaged and willing to participate
  - 150–600 members (enough for statistical relevance, not too large to manage)
  - Bible-teaching evangelical church
  - Ideally: 1 Reformed, 1 non-denom, 1 Baptist, 1 charismatic-adjacent, 1 church plant
  - Located in Dallas, TX area (for in-person debrief if needed) or strong relationship

**Pilot offer**
- Full diagnostic at no cost
- Personal onboarding call with admin (30 min)
- 90-minute debrief call after results are in (Will + pastor)
- Written report interpretation delivered 48 hours after debrief
- Commitment required: complete assessment, provide honest feedback, testimonial if satisfied

**Onboarding each pilot church**
- [ ] Create church in admin panel
- [ ] Create and provision admin user for senior pastor or exec pastor
- [ ] Walk through onboarding flow with them on a call
- [ ] Create survey instance, launch, copy invite link
- [ ] Provide guidance on how to communicate the assessment to their congregation

**Communication template for pastors**
- Draft email/announcement for pastor to send to congregation
- Explanation of BHIS, why they're doing it, what will happen with data (emphasize anonymity)
- Estimated time (10–12 min), anonymous, no wrong answers
- Link + deadline

**Deliverables:**
- 5+ pilot churches onboarded
- A documented doctrinal stance ready to hand any pastor who asks
- Each church has a launched survey and invite link distributed to congregation

---

### Weeks 11–12 — Response collection + live support

**While responses come in:**
- [ ] Dashboard shows real-time response count for pilot admins
- [ ] Admin receives email notification at 10, 25, 50 responses
- [ ] Monitor for technical issues (failed submissions, scoring errors, PDF failures)
- [ ] Respond to pastor questions within 24 hours

**Response targets per church:**
- Minimum: 20 responses (below this, results are directional only — and below the minimum-N floor some breakdowns will be suppressed)
- Target: 40% participation of active adults
- Ideal: 60%+ participation

**If response rate is low:**
- Follow-up announcement template for pastor
- Consider Sunday morning brief mention from the front
- Close survey after 3 weeks if response rate adequate

**Deliverables:**
- Each pilot church has at least 20 completed responses
- Scoring and aggregation completed for all pilot churches
- Pilot dashboards live and showing real data

---

### Weeks 13–14 — Debrief + feedback collection

**Debrief calls (one per church)**
- [ ] Schedule 90-minute call with senior pastor + 1–2 leaders
- [ ] Walk through church report together: health score, archetype, pillar findings
- [ ] Highlight 2–3 most significant findings specifically
- [ ] Work through priority recommendations together
- [ ] Note what resonated, what confused, what felt off
- [ ] Capture feedback on tone, question quality, dashboard clarity, and doctrine scoring fairness

**Feedback structure (collect from each pilot church):**
- Score the overall value of the diagnostic: 1–10
- Which finding was most useful to them?
- Which question(s) were confusing or felt off?
- Did the doctrine scoring feel fair to your tradition?
- What was missing that they wanted to see?
- Would they pay for this? What would they pay?
- Would they recommend it to another pastor?
- Would they do it again in 6 months?

**Product feedback synthesis:**
- [ ] Compile all feedback into themes
- [ ] Identify top 5 product changes required before public launch
- [ ] Identify any doctrinal/question issues raised by pastors
- [ ] Identify any scoring surprises (churches flagged incorrectly)

**Deliverables:**
- All 5+ pilot churches debriefed
- Feedback synthesized into prioritized change list
- At least 3 testimonials or case studies captured
- Pricing signal from pilot churches

---

### Phase 3 Definition of Done
- [ ] 5+ churches have completed the full assessment cycle
- [ ] Debrief calls completed for all pilot churches
- [ ] Feedback synthesized
- [ ] Product issues identified and prioritized
- [ ] At least 1 pilot church ready to convert to paying customer
- [ ] Production system handled pilot load without critical failures

---

## Phase 4 — Pilot Iteration
### Duration: 4 weeks
### Goal: Address the highest-priority issues surfaced in pilot before public launch

> Note: consent language and documented data-handling moved earlier (Phase 2 / Phase 3). Phase 4 now focuses on legal formalization and the second pilot round.

---

### Week 15–16 — Critical fixes from pilot feedback

Prioritize by impact and frequency. Expected issues based on similar products:

**Likely question issues:**
- [ ] 1–3 questions will be confusing or feel loaded — rewrite them
- [ ] Drift questions may feel accusatory — soften framing without losing diagnostic value
- [ ] Q10 forced prioritization may be poorly understood — improve instructions
- [ ] Open-ended prompts may be too abstract — make them more specific

**Likely scoring issues:**
- [ ] One or two archetypes may fire incorrectly for edge case profiles — tighten logic
- [ ] Credibility warning may fire too aggressively — adjust contradiction thresholds
- [ ] Maturity tier boundaries may feel off for certain church cultures — document and calibrate
- [ ] Doctrine scoring may feel biased to a non-Watermark tradition — calibrate or document stance

**Likely dashboard issues:**
- [ ] Pastors may not understand what to do with the data without guidance
- [ ] Recommendation language may be too direct or not direct enough
- [ ] PDF report may have formatting issues on certain church names or long text
- [ ] Mobile dashboard needs additional work

**Likely UX issues:**
- [ ] Survey drop-off at specific question numbers (track completion rates per question)
- [ ] Member confusion about what BHIS is before starting the survey
- [ ] Report landing may feel clinical — warming it up

---

### Week 17–18 — Second pilot round + pre-launch prep

**Second pilot round (2–3 additional churches)**
- [ ] Onboard 2–3 new churches with the updated product
- [ ] Faster debrief cycle (30-minute call instead of 90)
- [ ] Validate that the issues from pilot round 1 are resolved
- [ ] Collect additional testimonials

**Pre-launch checklist:**
- [ ] Legal — Privacy Policy and Terms of Service pages written and live
- [ ] Data handling documentation — what is collected, how it's stored, retention policy (formalize the anonymity model already built in Phase 1)
- [ ] Informed consent language (already live since Phase 2) reviewed by counsel
- [ ] HIPAA not applicable (spiritual data), but CCPA/GDPR considerations documented + data deletion endpoints
- [ ] Pricing page designed and copywritten
- [ ] Landing page (`bhis.io`) — positioning, value prop, how it works, pricing, testimonials
- [ ] Stripe integration scaffolded (billing not yet required, but account created)
- [ ] Support email set up — `support@bhis.io`

**Deliverables:**
- All critical pilot issues resolved
- Second pilot round confirms fixes
- Legal and compliance foundations in place
- Landing page live

---

## Phase 5 — Public Launch
### Duration: 4 weeks
### Goal: Self-serve onboarding for paying churches

---

### Week 19–20 — Billing and self-serve onboarding

**Billing (Stripe)**
- [ ] Stripe Checkout integration — hosted payment page
- [ ] Three pricing tiers:
  - **Free Snapshot** — 10-question mini-assessment, no dashboard, email capture
  - **Full Diagnostic** — $299 one-time, up to 150 respondents, full dashboard + reports
  - **Ongoing** — $79/month, unlimited assessments, trend tracking, benchmarks
- [ ] Webhook handling — `checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`
- [ ] `subscriptions` table — church_id, stripe_customer_id, plan, status, current_period_end — **new migration**
- [ ] Feature gating — `has_active_subscription()` middleware on protected routes
- [ ] Trial period — 14-day trial on Ongoing plan (no credit card required initially, consider)
- [ ] Church billing portal — manage subscription, update payment method, view invoices

**Self-serve onboarding + deferred admin tooling**
- [ ] Public registration — anyone can sign up, create a church, choose a plan
- [ ] Superadmin role + platform admin endpoints (`/admin/churches`, `/admin/usage`, `/admin/audit-logs`) — deferred from Phase 1; now needed to administer a growing base
- [ ] Onboarding checklist displayed on first login (5 steps, progress indicator)
- [ ] In-app tooltips on first dashboard visit — explain each metric
- [ ] Onboarding email sequence — 3 emails over 7 days (welcome, how to launch, tips)
- [ ] Live chat widget (Crisp or Intercom) for support during onboarding

**10-question Free Snapshot**
- [ ] Create mini-assessment template — 2 questions per pillar, highest-signal questions
- [ ] Snapshot report — directional scores only, no full breakdown
- [ ] Upgrade CTA prominently placed on snapshot report
- [ ] Email capture before accessing snapshot results (lead generation)

**Deliverables:**
- Any church can sign up and pay online without talking to anyone
- Free Snapshot working as lead generation tool
- Billing tested end-to-end
- Platform superadmin has visibility into usage

---

### Week 21–22 — Launch preparation + GTM

**Landing page (`bhis.io`)**
- [ ] Hero — clear headline, subheadline, primary CTA ("Get your free church health snapshot")
- [ ] Problem section — what church health tools miss, why self-reported sentiment is insufficient
- [ ] Solution section — how BHIS works (3 steps: assess, diagnose, act)
- [ ] Pillar overview — the 7 dimensions briefly explained
- [ ] Archetypes — show 3–4 example archetypes with descriptions
- [ ] Social proof — pilot church testimonials, pastor quotes
- [ ] Pricing — three tiers clearly displayed
- [ ] FAQ — addresses "Is this just another church survey?", "How is BHIS different from Barna?", "Is it anonymous?", "How long does it take?"
- [ ] Secondary CTA — "Schedule a demo" for larger churches and networks

**Launch sequence**
- [ ] Announce to pilot churches — they're the first advocates
- [ ] Personal outreach to 20 pastors in network — warm introductions
- [ ] Submit to Christian resource aggregators (Church Tech Today, Outreach Magazine newsletter)
- [ ] LinkedIn content — 3-post series: the problem, the solution, the pilot results
- [ ] Consider: launch on ProductHunt for broader awareness

**Deliverables:**
- Public launch live
- First paying customers from self-serve
- GTM motion underway

---

## Phase 6 — Intelligence Layer
### Duration: 8 weeks
### Goal: The product gets smarter — AI-powered qualitative analysis, benchmarking, trend tracking

> Note: this productizes the manual-LLM qualitative work done by hand during the pilot (Phase 1.5 / Week 4). Benchmarking has a cold-start problem — see below.

---

### Weeks 23–26 — AI qualitative analysis

**Productize LLM-powered analysis (manual in pilot, automated here)**
- [ ] Claude API integration for open-ended response analysis
- [ ] Prompt engineering: cluster Q45 responses by theme, extract dominant sentiments
- [ ] Q60 gap theme clustering — group "biggest faith-life gaps" into categories
- [ ] Concern detection — identify responses that signal pastoral crisis, abuse, or urgent need
- [ ] Anonymization layer — strip any identifying information before sending to API
- [ ] Cost controls — batch processing (not per-response), cache results
- [ ] `GET /qualitative/{instance_id}/ai-summary` — returns AI-generated pastoral narrative

**Qualitative dashboard panel**
- [ ] Qualitative tab in leadership dashboard
- [ ] Theme cloud visualization — frequency-weighted
- [ ] Q60 cluster display — "Prayer (31 mentions)", "Evangelism (24 mentions)" etc.
- [ ] Flagged responses panel — responses that triggered concern signals (leadership-only view)
- [ ] AI-generated pastoral narrative — 2–3 paragraph summary of what the congregation is saying

**Concern flagging protocol**
- [ ] Define concern threshold — language suggesting pastoral crisis, self-harm, abuse, spiritual abuse
- [ ] Flagged responses shown only to church admin (not raw text — paraphrased for privacy)
- [ ] Disclaimer: BHIS is not a crisis tool; if urgent need detected, direct to appropriate care
- [ ] Opt-out option for churches who do not want concern flagging enabled

---

### Weeks 27–30 — Benchmarking + trend tracking

> **Cold-start caveat:** benchmarking requires N churches' contributed data. Your first paying customers will see empty or thin benchmarks until the pool fills. Plan messaging around this (e.g., "benchmarks unlock as the network grows") and seed the pool with consenting pilot churches.

**Benchmark database**
- [ ] Aggregate anonymized pillar scores from all churches into benchmark pools
- [ ] Segmentation: by size range, theological profile, denomination
- [ ] `benchmark_snapshots` table — quarterly snapshots of pool averages — **new migration**
- [ ] Dashboard displays church vs. benchmark on every pillar bar
- [ ] Opt-in consent — churches must explicitly agree to contribute to benchmark pool

**Trend tracking (multi-cycle)**
- [ ] `assessment_cycles` table already in schema — activate the full UI
- [ ] Trend chart — health score over all completed cycles
- [ ] Pillar delta indicators — ↑ / ↓ / → since last cycle on each pillar
- [ ] Drift acceleration alert — if drift score increases >10 points cycle-over-cycle, flag
- [ ] Maturity distribution shift — shows congregation moving or stagnating
- [ ] Archetype change notification — "Your church's archetype shifted from X to Y"

**90-day snapshot assessment**
- [ ] Create 10-question snapshot template focused on Discipleship + Spiritual Discipline
- [ ] Snapshot report shows only those two pillars vs. last full assessment
- [ ] Recommended cadence: full assessment every 6 months, snapshot every 90 days
- [ ] Snapshot included in all paid plans

**Deliverables:**
- AI qualitative analysis running on all new assessments
- Benchmarking live for all plans (with cold-start messaging)
- Trend tracking visible in dashboard
- Snapshot assessment working

---

## Phase 7 — Platform Features
### Duration: 8 weeks
### Goal: Serve church networks, denominations, and multi-campus churches

---

### Weeks 31–34 — Multi-church and network features

**Network/denomination accounts**
- [ ] `networks` table — an account that contains multiple churches — **new migration**
- [ ] Network admin role — sees all churches in network, cannot see individual responses
- [ ] Network dashboard — aggregate health across all churches in network
- [ ] Network benchmark — churches compared against each other within the network (anonymized, respecting minimum-N)
- [ ] Network report — PDF summary of all churches in network (for denominational leaders)

**Multi-campus churches**
- [ ] Campus as a sub-unit of a church
- [ ] `campuses` table — church_id, name, city — **new migration**
- [ ] Survey instance can be scoped to a campus
- [ ] Campus vs. campus comparison in leadership dashboard
- [ ] Church-wide aggregate that rolls up all campus data

**Consultant/coach access**
- [ ] Consultant role — external user who can view church dashboards (read-only)
- [ ] Church admin grants consultant access for a specified period
- [ ] Consultant sees full dashboard and reports but cannot modify anything
- [ ] Consultant notes — text field for consultants to annotate church report

---

### Weeks 35–38 — Advanced reporting + customization

**Custom theological profiles (addresses the Watermark-only foundation risk)**
- [ ] `theological_profiles` table — custom weighting for doctrinal questions by tradition — **new migration**
- [ ] Charismatic profile — adjusts weight on Holy Spirit questions, removes cessationism penalty
- [ ] Reformed profile — adds weight on sovereignty/election questions in doctrine section
- [ ] Each profile is opt-in; default is the current evangelical baseline
- [ ] Phase 2 of Watermark foundation — denomination-specific overlay possible

**White-label**
- [ ] Network/denomination accounts can add their logo to reports and dashboard
- [ ] Custom color scheme (within accessibility constraints)
- [ ] White-label domain — `health.yourdenomination.org` pointing to BHIS infrastructure
- [ ] Custom report cover page with denomination branding

**Advanced exports**
- [ ] Raw data export (CSV) — anonymized response data for churches that want their own analysis
- [ ] PowerPoint report — slide deck formatted for elder/board presentation
- [ ] Comparative report — side-by-side two assessment cycles in one PDF
- [ ] Trend report — full history of all cycles in one document

---

## Post-Phase 7 — Future Modules (Backlog)

These are not scheduled but are designed and ready to scope when the time comes.

### Ministry-specific diagnostics
- Small group health module
- Staff/leadership team diagnostic
- Youth ministry module
- Men's/women's ministry module
- New member assimilation diagnostic

### Predictive features
- Attrition risk modeling — identify members likely to disengage in next 90 days
- Discipleship pathway builder — generate personalized growth roadmap per maturity tier
- Sermon series recommendation engine — AI-generated series suggestions based on gap analysis

### Integration layer
- Planning Center integration — attendance data to validate engagement scores
- Pushpay/Tithe.ly integration — giving participation (opt-in, church-controlled)
- Rock RMS integration
- Church community group participation sync

### Expanded assessments
- Pastoral burnout / leadership culture module
- Church board and elder assessment
- Church planter diagnostic
- Biblical counseling readiness module
- Membership covenant health assessment

---

## Key Metrics to Track

### Product health
| Metric | Target |
|---|---|
| Survey completion rate | > 80% |
| Average questions answered before drop-off | > 55 of 60 |
| Time to complete | 10–14 minutes |
| PDF report generation time | < 10 seconds |
| API error rate | < 0.5% |

### Business health
| Metric | Target |
|---|---|
| Pilot churches completing assessment | 100% |
| Pilot NPS | > 70 |
| Conversion rate (Free Snapshot → Paid) | > 15% |
| Monthly churn (Ongoing subscribers) | < 3% |
| Churches using repeat assessments | > 60% at 6 months |

### Doctrinal integrity
| Metric | Target |
|---|---|
| Pastors who raise doctrinal concerns about questions | < 10% |
| Churches who flag a question as theologically off | < 5% per question |
| Archetype accuracy (pastor agrees with classification) | > 80% |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pastors distrust the data | Medium | High | **Phase 1.5 concierge validation**, pilot debriefs, transparent scoring docs, pastoral advisory council |
| Members don't complete survey | Medium | High | Pastoral communication, mobile-first UX, sub-12-minute target |
| Theological bias in questions (Watermark-only foundation) | Medium | High | **Documented doctrinal stance before pilot (Week 10)**, pilot feedback loop, theological profiles in Phase 7 |
| Scoring archetypes misfire | Medium | Medium | 43 engine tests, **Phase 1.5 early calibration**, pilot calibration, feedback form on every report |
| AI qualitative analysis hallucinates | Low | High | Human-in-loop review of AI summaries, disclaimer on AI outputs |
| Church weaponizes data against members | Low | **Critical** | **Anonymity model + minimum-N floor + aggregate-only default enforced in Phase 1**, consent at survey start (Phase 2), privacy-first design, TOS |
| Anonymity model is unclear or breakable | Medium | **Critical** | Architect in Phase 1 (Week 2); members retrieve own report by session token; church cannot link responses to individuals |
| Building auth/PDF/queues around questions that change | Medium | High | **Phase 1.5 validates questions before Phase 1 hardens around them** |
| Single-dev timeline slips | High | Medium | Capacity assumption stated; plan for 1.5–2× calendar; ruthless scope cuts on path to pilot |
| Competitor launches similar product | Low | Medium | Move fast, build the doctrinal depth that takes years to replicate |
| Cessationist questions alienate charismatic churches | Medium | Medium | Already mitigated — cessationism not scored in MVP; stated explicitly to pilot pastors |
| Benchmarking cold-start (no pool for early customers) | High | Medium | Seed pool with consenting pilot churches; message "benchmarks unlock as network grows" |
| GDPR/CCPA compliance gaps | Low | High | Phase 4 legal review, data deletion endpoints, consent language live since Phase 2 |

---

## Immediate Next Actions (This Week)

1. `git push` the scaffold to `wpf002/bhis`
2. **Run Phase 1.5 prep:** line up 1–2 friendly churches (one non-Watermark-aligned) for concierge validation using the existing engine
3. Set up Railway project — backend + PostgreSQL + Redis (can wait until after 1.5 if validating locally)
4. Run `alembic upgrade head` on the target DB
5. Run `python seeds/seed_questions.py` to load 60 questions
6. Register at `sendgrid.com` — free tier is sufficient; integrate in Phase 1 Week 1
7. Reach out to first 3 pilot church candidates — warm email, not cold

---

*This roadmap is a living document. Update it after each phase completion.*
