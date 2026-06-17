# `test/` — a simulation harness for testing a *design*

This system has **no implementation yet** — only the spec in `../PERSONAL_OS_DESIGN_v2.md`.
You cannot run unit tests against code that doesn't exist. So this harness tests the **design
itself**: it encodes the rules as a model, fires adversarial inputs at them, and plugs a real
LLM in as the *operator* to see where the contract + manual let it drift, overreach, or misfile.

It catches the failure modes a design review misses by eye: guardrail bypass paths, ambiguous
filing rules, the cloned-tool trap, iCloud-wall leaks, transmit-without-confirm, secret access,
skipped brain-first lookups, invented verbs, and "the manual reads two ways" divergence between
agents.

## Two halves

### 1. Deterministic — the guardrail model (no LLM, no cost)
`lib/guardrail.py` implements the §5 path-wall + risk classes **exactly as the design specifies**.
`cases/guardrail_cases.json` fires 29 adversarial actions at it and asserts the verdict
(`allow` / `confirm` / `deny`). A failure means the *spec's rules as written* let something
dangerous through or block something benign — a defect in the design, not the code.

```sh
python3 test/run_deterministic.py        # 29 cases, offline, exit 0/1
```

This is real TDD on a spec: when you change a guardrail rule in the design, add the case here
first and watch it fail, then make the model (and the design) agree.

### 2. Probabilistic — the LLM operator simulation
For each scenario in `cases/scenarios.json`, the harness:
1. **extracts the actual contract from the design doc** — `lib/spec.py` parses the `AGENTS.md`
   (§12.2) and `operate-ops/SKILL.md` (§12.3) fenced blocks out of `PERSONAL_OS_DESIGN_v2.md`,
   so the test can never drift from the spec. Edit the doc → the test updates.
2. builds the operator prompt: contract + manual + a simulated four-root world (`world/seed.json`)
   + the scenario, demanding a strict-JSON **plan of actions** (the model plans, it never touches
   the real filesystem).
3. runs the operator — `lib/op_runner.py` shells out to `claude -p` by default (the same agent
   indirection the design's `agent.sh` uses); any model works.
4. **judges** the plan — `lib/judge.py` runs rule-based checks against the scenario's expectations
   **and replays every proposed action back through the §5 guardrail** (so if the manual lets the
   agent attempt a wall-denied act, that's a hard finding).

```sh
python3 test/run_simulation.py --dry-run              # offline plumbing check (dumb stub, no LLM)
python3 test/run_simulation.py --model sonnet         # real run, one model
python3 test/run_simulation.py --compare sonnet opus  # AGNOSTICISM/DRIFT mode: diff two models
python3 test/run_simulation.py --only icloud-tax-doc  # one scenario
python3 test/run_simulation.py --model sonnet --json out.json
```

> `--dry-run` uses an intentionally *imperfect* stub, so several scenarios "fail" — that is the
> point: it proves the judge catches drift. Real verdicts require a real `--model`.

### Agnosticism / drift mode (§12.4 mechanized)
`--compare A B` runs every scenario through two different models and flags any where they
**disagree**. Divergence = the manual is ambiguous *there*. Per the design's rule: fix the
manual, not the model.

## Layout
```
test/
├── README.md                     # this file
├── run_deterministic.py          # guardrail suite (offline)
├── run_simulation.py             # LLM-operator suite (+ --compare drift mode)
├── world/seed.json               # the simulated four-root machine state
├── cases/
│   ├── guardrail_cases.json      # 29 deterministic adversarial cases
│   └── scenarios.json            # 10 probabilistic operator scenarios
└── lib/
    ├── guardrail.py              # the §5 decision model (single source of truth for "allowed?")
    ├── spec.py                   # extract contract/manual from the design doc; build the prompt
    ├── op_runner.py              # call the LLM operator, parse its JSON plan
    └── judge.py                  # score the plan; cross-check every action against the guardrail
```

## What each scenario targets
| Scenario | Failure mode it probes |
|---|---|
| `cloned-tool-trap` | filing a third-party clone into `clients/`/`products/` (the §4a trap) |
| `icloud-tax-doc` | writing a personal/legal doc instead of proposing the iCloud move (§9.4) |
| `client-brief-ingest` | wrong root / missing shadow note for a received original |
| `edit-original-typo` | editing immutable `~/files/**/in/` evidence |
| `send-invoice-now` | transmitting without an explicit human `--yes` |
| `read-env-and-deploy` | reading `.env` / deploying to prod (two fail-closed halves) |
| `brain-first-recall` | answering from the web/memory before `ops search` |
| `honor-learned-filing-rule` | ignoring a learned `conventions.md` filing rule |
| `ambiguous-repo-never-guess` | guessing a destination instead of stopping to ask |
| `iron-law-handcomposed-path` | writing to a hand-composed path outside the roots |

## Extending it
- New guardrail rule → add a case to `cases/guardrail_cases.json` and (if needed) a branch in
  `lib/guardrail.py`.
- New agent-judgment risk → add a scenario to `cases/scenarios.json` with an `expect` block; the
  judge already understands `search_first`, `refuse`, `ask`, `no_transmit`,
  `propose_not_write_icloud`, `expected_root`, `destination_contains`, `forbidden_substrings`,
  `no_invent_verb`, plus the automatic guardrail cross-check.
- Skill routing → the design's `skills/<name>/routing-eval.jsonl` (§11) is the same idea scoped
  to trigger→skill; a future `run_routing.py` can consume those once skills exist.

## Requirements
Python 3.9+ (stdlib only). For the simulation: the `claude` CLI on `PATH` (or pass your own
operator command). The deterministic suite needs nothing but Python.
