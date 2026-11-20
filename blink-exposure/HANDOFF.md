# Blink Exposure: project handoff

A single-file HTML/JS guided exposure session for sensorimotor OCD, focused on noticing one's own blinking.
Built in an earlier Claude Code chat; this note carries everything a new chat needs to continue.

## Live page
- Published artifact (private to the owner): https://claude.ai/artifact/4VEjq7bhp7CSTJw6PPWdbL
- To update it from a new chat: `Artifact` action `read` on that URL first, then publish with `url` set to it.
  `artifact-source.html` here is the exact source of the current version (version 5).
- `artifact-source.html` has no doctype/head on purpose (the artifact host adds the skeleton).

## Files
| File | What it is |
|---|---|
| `artifact-source.html` | Source of the published page, Kokoro audio embedded (~0.9 MB) |
| `blink-exposure-standalone.html` | Full HTML document, no audio; has the `<!--KOKORO_AUDIO-->` slot. Input to the generator |
| `blink-exposure-kokoro.html` | Standalone file with Kokoro audio embedded; works offline on phone or laptop |
| `make_kokoro_voice.py` | Reads the standalone file, speaks every script sentence with Kokoro (kokoro-onnx), injects the clips as base64 MP3 |
| `kokoro-preview.mp3` | 7 s sample of the voice |

Regenerate audio: `python -m pip install kokoro-onnx soundfile numpy` then
`python make_kokoro_voice.py blink-exposure-standalone.html [--voice af_heart] [--speed 0.9]`.
Models (~330 MB) download to `kokoro_models/` from the kokoro-onnx GitHub release (git-ignored).
To rebuild the artifact source: take the `<script>window.KOKORO_AUDIO=...</script>` tag from the generated file and
put it in place of `<!--KOKORO_AUDIO-->` in the skeleton-less source (strip the doctype/head wrapper from the standalone).
The standalone file = the artifact source (without audio) wrapped in a doctype + head with charset, viewport
(`viewport-fit=cover`), safe-area padding on `:root`, `body{margin:0}` and `[hidden]{display:none!important}`.

## User's requirements (original brief)
- 2-minute guided exposure (options 1/2/3 min, repeatable), ERP + ACT-style acceptance; brief citations in a top comment
  (Foa, Yadin & Lichner 2012; Craske et al. 2014 inhibitory learning; Twohig et al. 2010 ACT for OCD).
- SUDS 0-10 before and after; saved with date in localStorage; simple trend over sessions.
- Voice guidance, calm pace, mute option, on-screen text as backup.
- Slow simple focal animation, no flashing.
- Script: 1) deliberate attention to blinking/eye sensations; 2) invite, label "noticing blinking", allow urge without
  acting; 3) widen to body/sounds with blinking kept in background (not as escape); 4) close without reassurance.
- No reassurance language, no promises of a cure. One-line note: supports, not replaces, a clinician trained in ERP.

## Decisions made along the way
- Focal shape is a slow, irregular, layered blob, deliberately NOT a breath pacer (so it can't become a calming ritual).
- Session screen: proportional phase track (Notice 25%, Allow 35%, Widen 28%, Close 12%), per-phase label inside the
  shape, caption highlights the sentence being spoken, controls dim after 4 s idle, ending early needs a second tap
  (makes leaving deliberate, ERP-consistent), side-by-side layout on wide screens, respects reduced motion.
- Voice: user found device (Web Speech) voices "horrendous". Now uses pre-rendered Kokoro `af_heart` at speed 0.9,
  one clip per sentence, with page-controlled pauses (Pace: Slow / Calm / Natural). Web Speech remains as fallback,
  with ranked voices and a picker. User said Kokoro is "better".
- Script sentences are split client-side with `/[^.!?]+[.!?]*/g`; the generator uses the same split. Editing script
  text requires regenerating audio (missing clips fall back to device voices).

## Open item: connecting the user's PC
- The user wants this chat able to work on their Windows PC.
- Remote Control lists computer `FFL-8CC6214KQ7`, folder `Claude Projects` (C:\Users\New\Documents\Claude Projects),
  but it shows as `not_available`: the PC does not offer it to cloud sessions. Likely cause: Claude desktop app on
  Windows needs updating (then fully quit and reopen); otherwise the feature may not be enabled for the account yet.
- Next step in the new chat: call `list_computer_folders`; if the folder is usable, `request_computer_folder` with the
  exact environment_id / computer_name / folder from that list, and copy these files into that folder.

## Possible next steps the user may want
- Try other Kokoro voices (bf_emma, bm_george, am_michael) or speed.
- Further design polish of setup/results screens.
