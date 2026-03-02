---
date: 2026-03-02
focus: technology
confidence: 8/10
tags:
  - type/research
  - issue/17
---

# What Makes a Claude Code Skill Maximally Effective

Research into skill authoring best practices to inform the design of skill nodes
for issue 17 (skill graph / `/mantle:add-skill`).

## Three-Tier Loading Architecture

Claude Code loads skills in three tiers:

1. **Tier 1 — Metadata (always loaded).** The `name` and `description` from all
   skills are loaded into the system prompt at startup inside an
   `<available_skills>` section. This operates under a **character budget of 2%
   of the context window** (~15,000–16,000 chars). If too many skills exist,
   some get excluded. Description quality determines whether a skill activates.

2. **Tier 2 — Body (loaded on invocation).** When Claude determines a skill is
   relevant (or the user types `/skill-name`), the full SKILL.md content is
   injected via dual-message injection. Every token competes with conversation
   history and other loaded context.

3. **Tier 3 — Supporting files (loaded on demand).** Reference files, templates,
   and examples consume zero tokens until Claude explicitly reads them.

Skill selection uses **pure LLM reasoning** — no regex, no keyword matching.
Claude reads descriptions and uses native language understanding to match intent.

## Effective Patterns

### 1. High-Quality Descriptions

The description must serve as the triggering mechanism. Write in third person.
Include both what the skill does and when to use it.

Good: "Extract text and tables from PDF files, fill forms, merge documents. Use
when working with PDF files or when the user mentions PDFs, forms, or document
extraction."

Bad: "Helps with documents"

### 2. Imperative, Concise Instructions

Use imperative form. Be aggressively concise. Keep body under 500 lines.

Good (~50 tokens):
```
## Extract PDF text
Use pdfplumber for text extraction:
    import pdfplumber
    with pdfplumber.open("file.pdf") as pdf:
        text = pdf.pages[0].extract_text()
```

Bad (~150 tokens): explaining what PDFs are before showing the code.

### 3. Challenge Every Token

Only add context Claude doesn't already have. Ask: "Would a senior engineer need
this explained?" If not, cut it. Claude is very capable — don't explain standard
libraries, common patterns, or well-known concepts.

### 4. Explain the Why, Not Just the What

"Use UTC timestamps consistently (timezone bugs are the #1 support issue)" is
better than "Use UTC timestamps." The reasoning helps Claude make good judgement
calls in edge cases.

### 5. Concrete Over Abstract

Show code, show examples, show the exact pattern. 2–3 input/output examples
dramatically improve accuracy. Avoid hand-waving.

### 6. Progressive Disclosure

Keep the main content focused. Push detailed reference material to separate files
referenced with clear guidance on when to read them. Keep references one level
deep.

### 7. Decision Criteria

Guide through decision points explicitly: "Creating new content? → Follow
creation workflow. Editing existing? → Follow editing workflow." This prevents
Claude from guessing.

### 8. Persona and Tone Setting

Opening with a persona definition and tone guidance shapes the entire interaction
without consuming many tokens. The existing Mantle skills demonstrate this well.

## Anti-Patterns

1. **Over-explaining what Claude already knows.** Don't explain standard
   libraries, common patterns, or well-known concepts.
2. **Offering too many options.** Provide an opinionated default with an escape
   hatch, not five alternatives.
3. **Vague descriptions.** "Helps with documents" will fail at triggering.
4. **Inconsistent terminology.** Pick one term per concept, use it throughout.
5. **Deeply nested file references.** Claude may only partially follow chains.
6. **Dump-and-run monologues.** Don't present everything at once. Present one
   section, get feedback, move on.
7. **Over-aggressive triggering language.** "CRITICAL: You MUST use this tool
   when..." causes over-triggering. Use natural language.
8. **Time-sensitive information.** Don't write "If before August 2025, use the
   old API."

## Optimal Length and Density

- **Description/metadata:** Under 200 characters for description.
- **Body content sweet spot:** 50–150 lines of dense, high-signal content.
- **Under 100 lines** may not provide enough value. **Over 500 lines** means
  the content should be split.
- **Token cost:** A 150-line skill at ~4 tokens/line ≈ 600 tokens — reasonable.
  A 500-line skill ≈ 2,000 tokens — approaches the point where it noticeably
  reduces available context.
- **Mantle command files range** from 70 lines (idea.md) to 195 lines
  (adopt.md), mostly 90–130 lines.

## Implications for Skill Node Design

### Content Should Be Written for Claude

The skill content gets loaded into Claude's context during implementation. It
should be written as **instructions and knowledge for Claude**, not as a human
tutorial. Dense, opinionated, actionable.

### Recommended Body Structure

1. **Context/Purpose (1–3 sentences).** Why this skill exists and what problem
   it addresses. Orients Claude immediately.
2. **Core Knowledge (main content).** Patterns, conventions, domain knowledge.
   Imperative form. Only info Claude cannot infer.
3. **Examples (if applicable).** Concrete input/output pairs. 2–3 is the sweet
   spot.
4. **Decision Criteria (if applicable).** When to use approach A vs B.
5. **Anti-patterns (brief).** What NOT to do, framed as what TO do instead.
   3–5 bullets max.

### Metadata That Matters

- **description** — Most important field. Determines activation.
- **tags** — Primary discovery mechanism for graph matching.
- **proficiency/confidence** — Helps rank competing skills and calibrate trust.
- **sources** — Provenance for reliability assessment and updates.
- **created/updated** — Freshness signal for rapidly-evolving tools.

## Sources

### Official Anthropic Documentation
- Extend Claude with skills — code.claude.com/docs/en/skills
- Skill authoring best practices — platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Prompting best practices for Claude 4 — platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices
- Equipping agents for the real world — claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills

### Official Repositories
- anthropics/skills GitHub repo — github.com/anthropics/skills
- skill-creator SKILL.md — the meta-skill for creating skills

### Third-Party Analysis
- Claude Agent Skills Deep Dive — leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/
- Claude Code Customization Guide — alexop.dev
