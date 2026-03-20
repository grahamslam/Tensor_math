# Next Session Notes — R(5,5) Extension Analysis

## Running Overnight
`analyze_extension.py` is running with 1 restart, 5K steps per graph.
Task ID: bqdipt8wz (may not survive session restart)
Output: `extension_analysis.json` (written on completion)

## Key Finding So Far
**Graph 41 (0-indexed) in r55_42some.g6 achieved best_ext=2** — both original AND complement.
Only 2 violations away from a 43-vertex R(5,5) avoider.
Both orientations hitting E=2 suggests self-complementary or near-self-complementary structure.

Progress at last check (130/328 graphs):
- 21 → 18 → 15 → **2** (around graph 50) → held at 2 through graph 130

## What To Do When Results Are In

1. Check `extension_analysis.json` for the full distribution
2. Identify the EXACT graph index with E=2 (and any others with E <= 5)
3. For that graph, run heavy targeted SA:
   - `ramsey_targeted.py` approach (incremental violation tracking)
   - But on the 42-bit connection vector, not edge flips
   - Hundreds of restarts, 100K+ steps each
   - If it hits E=0: VERIFY with full count → potentially disproves R(5,5)=43 conjecture
4. Also try: the complement of that graph (might be even better)

## A second scan is also running
Scanning graphs 40-65 with 3 restarts each. Task ID: b2bdqg8ih
This was meant to identify the E=2 graph faster but is also slow.

## Context
- 43 <= R(5,5) <= 46 (current bounds)
- McKay-Radziszowski conjecture: R(5,5) = 43
- 656 known R(5,5,42)-graphs, "none extend to 43" — but we found one gets to E=2
- If ANY extension reaches E=0, it would disprove the conjecture
- This would be a significant mathematical result

## Files
- `r55_42some.g6` — McKay's 328 graphs (complements are the other 328)
- `analysis_656.json` — Phase 1 structural analysis of all 656
- `results.json` — verified avoiders n=37 through n=42
- `docs/R55_search_report.md` — full writeup
