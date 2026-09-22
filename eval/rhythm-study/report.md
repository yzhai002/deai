# Rhythm study (2026-09-23)

Tests the §7 uniform-sentence-length hypothesis in English, un-pointed: the rewrite agent's prompt named no pattern and no rhythm, so any effect comes from the skill's own mark-the-tells step.

## Design

- **Inputs**: 4 deliberately uniform texts (5-8 words per sentence, 8 sentences each; the rhythm detector fires once per text). No lexical tells in the inputs, so the study isolates rhythm.
- **Rewrite**: 1 subagent read SKILL.md and ran the full workflow. Its own summary reported acting on §7 and §8 (repeated sentence openings) without being told.
- **Judging**: 1 blind judge on randomized A/B pairs. The judge counted sentence lengths itself, and its A/B labels check out against the files.

## Results

| Metric | Inputs | Rewrites |
|---|---|---|
| Uniform rhythm runs | 4 | **0** |

Sentence-length distributions (words per sentence):

- u1: [6, 6, 6, 5, 5, 6, 5, 6] → [12, 12, 5, 18]
- u2: [6, 6, 6, 6, 6, 5, 5, 5] → [13, 17, 5, 10]
- u3: [6, 6, 7, 7, 7, 6, 7, 6] → [18, 13, 7, 14]
- u4: [8, 7, 7, 7, 6, 7, 6, 7] → [16, 7, 7, 6, 19]

The judge preferred the rewrite 4/4, with evidence centered on rhythm: the originals read as "a metronome, each sentence a bare subject-verb-object tick," and the subject-echo stitching ("The queue sorts... the queue") was called out as the mechanical move. Remaining criticism of the rewrites: mild transition crutches and one dangling absolute.

## Conclusion

§7 works in English without prompting: the mark-the-tells step finds the uniform run on its own, and the rewrite breaks it while keeping every fact (verified by the rewriter's fact summaries; inputs carried no numbers). Combined with the un-pointed Chinese re-run (deai-zh eval/rhythm-study-2/), the pointing-bias concern from the first Chinese rhythm study is closed.

Discounts: single-family judge, 4 samples, inputs written for this study (not naturally occurring AI text).

## Files

```
eval/rhythm-study/inputs/     4 uniform inputs
eval/rhythm-study/rewrites/   4 rewrites
eval/rhythm-study/pairs/      randomized A/B pairs
eval/rhythm-study/mapping.json  position map (not shown to the judge)
```
