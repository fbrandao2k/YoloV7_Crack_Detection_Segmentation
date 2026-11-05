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

The commit SHAs above are from before the history rewrite recorded below.

## Outcome — history rewritten on 2026-11-05

The owner revoked the credential in Roboflow before the rewrite, so the old value no
longer works. The rewrite followed the sequence below:

- A fresh mirror was inventoried again; every remote tip matched the inventory.
- `git filter-repo --sensitive-data-removal --replace-text` replaced only the old
  literal, with `YOUR_ROBOFLOW_API_KEY`. Commit counts, authors, dates and messages
  are unchanged, and the file lists at the branch tips are identical.
- Each branch was force-pushed with `--force-with-lease` on its recorded old tip:

| Branch | Old tip | New tip |
| --- | --- | --- |
| main | c66d14ce28ade7b45317fb8912521e9c85d9b1b8 | 129bd5e6244bcae654f60cc66eae5423034a6e04 |
| codex/credential-history-guard | 09a9c74a112dfe2edb4e8dafd37bc2aa9257d1e1 | 6b2fe3df2ee39cf180565725237d225b9b009368 |
| codex/local-inference-review | 27e9373cc02afeed949d9c2bcf75900408000b67 | 26b6c4146088462cd0f7cb15236ccf72d8607820 |

- A fresh clone from GitHub was checked afterwards: no blob or commit message on any
  branch contains the old literal.

Still open: `refs/pull/1/head` and `refs/pull/2/head` belong to GitHub and still point
to the old commits; only GitHub Support can remove them. Because the credential is
revoked, that request is optional. Anyone with a clone made before 2026-11-05 should
re-clone instead of pulling, and must not push the old history back.

## Decision and sequence (as planned on 2026-10-04)

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
