# Credential history audit — 2026-10-04 UTC

A mirror of all advertised refs contained one prior literal Roboflow credential.
The credential was compared locally in memory, never printed or tested against Roboflow.
All reachable blobs were checked for that literal. Current branch tips are clean.
This is not a guarantee about unadvertised refs, forks, caches, or external clones.

Affected blob: `e50ad38938505888754bef1f8ef1413ff8fa82af`
Path: `Crack_SegmentationV8.ipynb`
Commits whose trees contain it:
- `2bc484fab98fd41ae977ca4e548483c363d193a0`
- `d5734312279ef2b659dd5a97845f74bab5e3c95e`

Affected refs at audit time:
| Ref | Tip |
| --- | --- |
| refs/heads/main | ef2ffa54fee749d722fa77161c1ad43206fdd625 |
| refs/heads/codex/local-inference-review | 27e9373cc02afeed949d9c2bcf75900408000b67 |
| refs/pull/1/head | 27e9373cc02afeed949d9c2bcf75900408000b67 |

No tags were advertised. Adding this prevention change introduces another descendant
ref; refresh the inventory immediately before any rewrite.

## Decision and sequence — not executed

Revoke the exposed credential in Roboflow first and provision a replacement for
legitimate consumers through environment variables or a hidden prompt. GitHub
cannot revoke a Roboflow credential. Rotation status and validity are unverified.
A coordinated rewrite is recommended to remove the retained literal, but rotation
is the primary security remediation. Rewriting cannot erase other people's copies.

1. Obtain explicit approval for the destructive rewrite; pause writes and coordinate
   with collaborators. Keep a restricted backup, since it contains the old credential.
2. Clone a fresh mirror and inventory every advertised ref again:
   `git clone --mirror https://github.com/fbrandao2k/YoloV7_Crack_Detection_Segmentation.git clean.git`
3. Use `git-filter-repo` >= 2.47. Extract the old literal from the identified notebook
   blob locally into a mode-0600 replacement file outside the repository, using a
   script rather than a shell literal, command argument, log, or pasted value.
   Format: `literal:<old value>==>REMOVED_ROBOFLOW_CREDENTIAL`.
4. In the fresh mirror run:
   `git filter-repo --sensitive-data-removal --replace-text /secure/roboflow-replacements.txt`
   Do not use a path-removal filter: preserve the notebook and its other content.
5. Check every rewritten reachable blob for the old literal using the in-memory
   audit again. Confirm no matches, inspect commit/ref maps, notebook JSON validity,
   and the prevention check. Record every changed ref and old/new SHA before pushing.
6. Restore origin if removed by filter-repo. After checking remote tips still match
   the frozen inventory, push each changed branch using explicit `--force-with-lease`
   with its recorded old SHA. Include any newly created branches; handle tags only
   if the refreshed inventory contains them. Never blindly push `--mirror`.
7. GitHub owns `refs/pull/*`; users cannot force-update them. Review filter-repo's
   changed-ref report and contact GitHub Support about PR refs/cached views if
   eligible. GitHub may decline cleanup when revocation sufficiently mitigates risk.
8. Collaborators should reclone or follow filter-repo's sensitive-data cleanup
   guidance; avoid merging old history back. Clean forks separately. Dispose of
   the replacement file and restricted backups according to retention policy.

Reference: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

## Prevention

Run `python scripts/check_secrets.py` from the repository root before committing.
CI runs the same check on pushes and pull requests, scanning tracked text and
notebook cells/outputs for literal API-key assignments and API-key URL parameters.
It prints only paths and cell numbers. This targeted guard is not a general secret
scanner and cannot block the initial upload. Configure the CI check as required in
branch rules to block merges; enable GitHub secret scanning/push protection where
available. Never save notebook outputs containing credentials. Keep `.env` ignored.
