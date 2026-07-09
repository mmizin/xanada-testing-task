---
name: plan-task
description: |
  Guide users through structured planning before implementation. 
  
  Use this whenever the user asks to implement a feature, fix a bug, refactor code, add tests, or make any non-trivial change. The skill will automatically decide task complexity (small/medium/large) and scale the planning rigor accordingly. For trivial one-liners (single file, <10 lines, no behavior changes), planning is skipped with user confirmation. For everything else, you'll gather requirements, validate they're complete, create a formal plan, get approval, and then implement with discipline.
  
  Trigger on phrases like: "implement X", "add feature X", "fix bug X", "refactor X", "write tests for X", "optimize X", "update X", "create X", "integrate X" — essentially any implementation request that isn't obviously a trivial single-line fix.
---

# Plan Before Implementation — Structured Planning Workflow

This skill guides implementation work through a disciplined, approval-based workflow: discover requirements, validate completeness, create a plan, get approval, implement with scope discipline, and verify results.

## Core Principle

Think before implementing. Clarify before planning. Plan before implementing. Never replace missing requirements with assumptions when clarification is possible.

---

## Phase 1: Assess Task Complexity

First, determine whether formal planning is needed.

### When Planning is REQUIRED

All of these conditions are true:
- Affects multiple files
- Changes 10+ lines
- Introduces API changes
- Adds behavior changes
- Modifies architecture
- Affects databases or persistence
- Touches test infrastructure
- Affects other systems or services

**Action:** Proceed to Phase 2 (Discovery).

### When Planning Can Be Skipped (Trivial Change)

ALL of these are true:
- Single file modification
- Less than ~10 changed lines
- No API changes
- No behavior changes
- No architecture changes
- No database changes
- No test changes
- User explicitly approves skipping

**Action:** Confirm with user ("This looks like a trivial change — want to skip planning?"), then proceed directly to implementation if they agree.

---

## Phase 2: Discovery Mode

Gather requirements systematically. Use this framework to ask clarification questions.

### Functional Requirements

Understanding what should happen and how it behaves.

**Ask:**
- What is the expected behavior after this change?
- What are the specific user flows or API flows affected?
- What business rules apply?
- What validation rules should be enforced?
- What should happen on failure? (error handling, recovery)
- What are the success criteria? (how do you know it's done?)
- What acceptance criteria must be met?
- What edge cases or boundary conditions exist?
- What negative scenarios might occur? (invalid input, missing data, etc.)

### Integration Requirements

Identify all systems this change touches.

**Ask:**
- Which APIs are affected? (internal or external)
- Are there database schema or data changes?
- Does this affect authentication or authorization?
- Does this change interact with existing services?
- Are there queue, cache, or async systems involved?
- Are there third-party integrations?
- What UI components are affected (if any)?
- What data flows between systems?

**For this project specifically, always ask about:**
- API client changes (e.g., new endpoints, modified contracts)
- Database fixtures or test data changes
- New test data files needed in `src/test_data/`

### Non-Functional Requirements

Performance, security, reliability, and operations.

**Ask:**
- Are there performance expectations?
- Are there security or compliance requirements?
- What about availability or reliability?
- Do we need logging, metrics, or tracing?
- Are there monitoring or alerting needs?

### Technical Constraints

Existing patterns and standards.

**Ask:**
- What architecture patterns must be followed?
- What coding standards or conventions apply?
- Are there approved libraries or frameworks?
- Are there deployment or infrastructure constraints?
- What does the codebase already do? (avoid reinventing)

### Discovery Complete Checklist

Planning may proceed only when ALL are true:

- [ ] Functional requirements understood
- [ ] Major edge cases identified
- [ ] Success criteria defined
- [ ] Integration points identified
- [ ] Scope is clear (what's IN, what's OUT)
- [ ] Unknown assumptions minimized
- [ ] User confirms requirements are sufficient

If any checkbox is unchecked, continue asking questions. Do not proceed to planning with incomplete requirements.

---

## Phase 3: Planning Mode

After requirements are complete, create a formal plan.

### Plan Template

Create a plan file at: `.claude/plans/<YYYY-MM-DD>-<task-slug>/plan.md`

Example: `.claude/plans/2026-06-27-add-rate-limit-retry/plan.md`

**Use this exact structure:**

```markdown
# [Task Title]

## Objective
[One paragraph: what problem is being solved?]

## Requirements Summary
[Bullet points summarizing discovered requirements]

## Assumptions
[List any remaining assumptions]

## Architecture / Design
[Describe the high-level approach]
[Design decisions and reasoning]
[Architectural impacts (if any)]

## Files to Be Modified
[List files to create, modify, or remove]

### Create
- `path/to/new/file.py`

### Modify
- `path/to/existing/file.py`

### Remove
- `path/to/deprecated/file.py`

## Implementation Steps
[Numbered step-by-step plan]

1. Step one
2. Step two
...

## Edge Cases & Boundary Conditions
[Document tricky scenarios and how they're handled]

## Integration Impact Analysis
[Describe impacts on: API contracts, database, fixtures, test data, other services]

## Test Strategy
[Describe unit tests, integration tests, e2e/UI tests if applicable]
[Identify existing tests that need updates]
[Identify regression risks]

## Non-Functional Impact
[Performance, security, reliability, scalability, observability]

## Risks & Mitigation
[Identify implementation risks and mitigation strategies]

## Alternatives Considered
[Why was this approach chosen over alternatives?]

## Approval Status
[ ] User approval obtained
```

### Planning Complete Checklist

Planning is complete only when ALL are true:

- [ ] Objective documented
- [ ] Requirements summarized
- [ ] Assumptions listed
- [ ] Architecture described
- [ ] Files identified (create/modify/remove)
- [ ] Implementation steps documented
- [ ] Edge cases documented
- [ ] Integration impact analyzed
- [ ] Test strategy defined
- [ ] Risks documented

---

## Phase 4: Review & Approval

Present the plan to the user.

**Action:** Display the plan file and ask: "Does this look right? Any changes before we proceed?"

**Valid approvals include:**
- "approved"
- "looks good"
- "proceed"
- "implement"
- Explicit confirmation equivalent to the above

**If user wants changes:**
- Update the plan
- Present the updated version
- Request approval again

**Do not begin implementation without explicit approval.**

---

## Phase 5: Implementation

Only after approval, implement according to the plan.

### Implementation Discipline Rules

Enforce these rules to prevent scope creep:

- **Implement only the approved scope.** Do not add features beyond the plan.
- **Do not introduce unrelated refactoring.** Focus on the task at hand.
- **Do not fix unrelated bugs.** Document them; fix in separate PRs.
- **Do not expand the feature without approval.** If scope changes, stop, explain, update the plan, and request approval again.
- **If a significantly better solution is discovered during implementation:**
  - Stop work
  - Explain the new approach
  - Update the plan
  - Request approval again

### Implementation Checklist

As you implement:

- [ ] Follow the step-by-step plan
- [ ] Create/modify/remove files as specified
- [ ] Maintain code style and conventions
- [ ] Add necessary tests (per test strategy)
- [ ] Update test data files if needed
- [ ] Document assumptions in code comments (if non-obvious)

---

## Phase 6: Verification

After implementation, verify the work is complete and correct.

### Verification Checklist

Before claiming completion, verify ALL of these:

- [ ] Code review (run `/code-review` or equivalent)
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E/UI tests pass (if applicable)
- [ ] Linting passes
- [ ] Formatting correct
- [ ] Acceptance criteria met
- [ ] Edge cases tested
- [ ] No regressions in existing tests

---

## Task Scaling: Planning Rigor by Complexity

Adapt the planning rigor based on task size.

### Small Task (1-2 files, 20-50 lines)

- Brief discovery (key questions only)
- Short plan (1-2 page equivalent)
- Quick approval
- Implementation
- Verification

**Effort:** ~15-30 minutes planning time

### Medium Task (3-5 files, 50-200 lines)

- Full discovery (all question categories)
- Standard plan (4-5 page equivalent)
- Detailed approval review
- Implementation with discipline
- Full verification

**Effort:** ~30-60 minutes planning time

### Large Task (6+ files, 200+ lines, architectural changes)

- Exhaustive discovery (deep dive on all aspects)
- Comprehensive plan (6+ pages)
- Architecture discussion (may include ADR)
- Risk analysis
- Detailed approval review
- Implementation with checkpoints
- Full verification + regression testing

**Effort:** ~1-2 hours planning time

---

## Special Case: Returning to Discovery

If during implementation or planning you discover:

- New business requirements
- Existing assumptions becoming invalid
- Integration constraints changing
- User changing scope
- Technical investigation revealing incorrect assumptions

**Action:**
1. Stop work
2. Return to Discovery Mode
3. Ask new clarification questions
4. Update the plan
5. Present updated plan to user
6. Obtain approval again
7. Resume implementation

---

## Summary

This workflow enforces discipline:

1. **Discover** — Gather complete requirements
2. **Plan** — Create a formal, reviewed plan
3. **Approve** — Get explicit user approval
4. **Implement** — Build according to plan with scope discipline
5. **Verify** — Ensure quality and completeness

This prevents rework, reduces misalignment, and catches issues early.
