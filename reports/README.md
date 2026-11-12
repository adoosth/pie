# Reports for light green

A word may enter **fully explained, with adjustments** only through this folder
and `data/adjusted.yaml`. Two files are required for every move:

- one in `laws/` for each law or etymon this project changed — what the
  literature says, what we propose, which words the change touches, and what it
  costs in every language the transition reaches (a candidate is accepted only
  if nothing loses and something gains; `tools/council.py` measures it);
- one in `words/` for the word itself — its record, the derivation, why the
  change is necessary rather than convenient, its meaning, and every word it
  competes with.

Then the word is listed in `data/adjusted.yaml` under `words:` with its `lang`
and `word`, and every changed rule under `rules:` with `id`, `transition` and
the report's path. Explicit approval is the last step; without it the word
stays yellow and the reason says *needs approval of our modification*.

Templates:

`laws/<rule-id>.md`
```markdown
# <rule id> — <one-line claim>
Literature: <what the standard account says, with the source key from
            data/sources.yaml>.
Proposal:   <the change, exactly>.
Touched:    <words in every descendant language the law reaches>.
Cost:       <what the change breaks, with the measured numbers>.
Verdict:    <the Council's measurement and the decision>.
```

`words/<lang>-<word>.md`
```markdown
# <word> (<language>)
Record:    <ancestry, cognate set, gloss, sources>.
Path:      <the derivation and the rule that needed the adjustment>.
Why:       <why the record is right and the change is the smaller error>.
Approved:  <date and the approving note>.
```
