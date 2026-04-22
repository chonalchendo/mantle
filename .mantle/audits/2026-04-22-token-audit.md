# Mantle command token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

| Rank | Command | Tokens | % of total |
| ---- | ------- | ------:| ----------:|
| 1 | build | 5,119 | 9.7% |
| 2 | implement | 3,746 | 7.1% |
| 3 | add-skill | 2,905 | 5.5% |
| 4 | scout | 2,837 | 5.4% |
| 5 | verify | 2,815 | 5.3% |
| 6 | plan-stories | 2,535 | 4.8% |
| 7 | shape-issue | 2,384 | 4.5% |
| 8 | design-system | 2,378 | 4.5% |
| 9 | brainstorm | 2,298 | 4.4% |
| 10 | research | 2,276 | 4.3% |
| 11 | design-product | 2,080 | 3.9% |
| 12 | adopt | 2,062 | 3.9% |
| 13 | plan-issues | 2,036 | 3.9% |
| 14 | refactor | 1,842 | 3.5% |
| 15 | review | 1,824 | 3.5% |
| 16 | challenge | 1,754 | 3.3% |
| 17 | simplify | 1,665 | 3.2% |
| 18 | add-issue | 1,568 | 3.0% |
| 19 | fix | 1,345 | 2.6% |
| 20 | retrospective | 1,097 | 2.1% |
| 21 | revise-product | 987 | 1.9% |
| 22 | revise-system | 949 | 1.8% |
| 23 | idea | 896 | 1.7% |
| 24 | query | 836 | 1.6% |
| 25 | bug | 830 | 1.6% |
| 26 | distill | 770 | 1.5% |
| 27 | help | 513 | 1.0% |
| 28 | patterns | 183 | 0.3% |
| 29 | inbox | 159 | 0.3% |

**Total:** 52,689 tokens across 29 command(s).

**Top 3 candidates for rewrite:** build.md, implement.md, add-skill.md

## After

| Rank | Command | Before | After | Saved | % saved |
| ---- | ------- | ------:| -----:| -----:| -------:|
| 1 | build | 5,119 | 4,112 | 1,007 | 19.7% |
| 2 | implement | 3,746 | 2,935 | 811 | 21.6% |
| 3 | scout | 2,837 | 2,837 | 0 | 0.0% |
| 4 | verify | 2,815 | 2,815 | 0 | 0.0% |
| 5 | plan-stories | 2,535 | 2,535 | 0 | 0.0% |
| 6 | shape-issue | 2,384 | 2,384 | 0 | 0.0% |
| 7 | design-system | 2,378 | 2,378 | 0 | 0.0% |
| 8 | brainstorm | 2,298 | 2,298 | 0 | 0.0% |
| 9 | add-skill | 2,905 | 2,276 | 629 | 21.7% |
| 10 | research | 2,276 | 2,276 | 0 | 0.0% |
| 11 | design-product | 2,080 | 2,080 | 0 | 0.0% |
| 12 | adopt | 2,062 | 2,062 | 0 | 0.0% |
| 13 | plan-issues | 2,036 | 2,036 | 0 | 0.0% |
| 14 | refactor | 1,842 | 1,842 | 0 | 0.0% |
| 15 | review | 1,824 | 1,824 | 0 | 0.0% |
| 16 | challenge | 1,754 | 1,754 | 0 | 0.0% |
| 17 | simplify | 1,665 | 1,665 | 0 | 0.0% |
| 18 | add-issue | 1,568 | 1,568 | 0 | 0.0% |
| 19 | fix | 1,345 | 1,345 | 0 | 0.0% |
| 20 | retrospective | 1,097 | 1,097 | 0 | 0.0% |
| 21 | revise-product | 987 | 987 | 0 | 0.0% |
| 22 | revise-system | 949 | 949 | 0 | 0.0% |
| 23 | idea | 896 | 896 | 0 | 0.0% |
| 24 | query | 836 | 836 | 0 | 0.0% |
| 25 | bug | 830 | 830 | 0 | 0.0% |
| 26 | distill | 770 | 770 | 0 | 0.0% |
| 27 | help | 513 | 513 | 0 | 0.0% |
| 28 | patterns | 183 | 183 | 0 | 0.0% |
| 29 | inbox | 159 | 159 | 0 | 0.0% |

## Delta summary

- Top-3 commands: 1,818 tokens saved (15.5% reduction).
- Total: 2,447 tokens saved (4.6% reduction).
- Techniques applied: Output Format templates, imperative-fragment rewrite.
- Tokenizer: tiktoken cl100k_base (~97% Claude BPE proxy; rank/delta effectively exact).
