# The `/site/` class contract — version 1

Every class is a folder at the repository root whose name is the class id, containing a
`site/` directory with a single `class.json`.

    <class-id>/
      site/
        class.json

`class.json` is validated on import. A manifest that fails validation is refused and the
last valid version keeps serving.

## Fields

| Field | Type | Rules |
| --- | --- | --- |
| `schemaVersion` | number | Must be `1`. |
| `id` | string | Lowercase letters, digits, hyphens. 3–48 characters. **Must match the folder name.** Stable forever — renaming it is a migration. |
| `title` | string | ≤ 200 characters. Shown on the catalog card and the lesson page. |
| `icon` | string | ≤ 8 characters. A single glyph. |
| `owner` | string or null | ≤ 200 characters. Who runs this class. |
| `summary` | string | ≤ 2000. One paragraph for the catalog card. |
| `detail` | string | ≤ 2000. The longer description at the top of the lesson page. |
| `outcome` | string | ≤ 2000. What the attendee has at the end. |
| `artifact` | string | ≤ 2000. The thing they take away. |
| `audience` | enum | `Mixed technical and non-technical` · `Advanced technical` · `Non-technical` · `Customers` · `Enterprise` · `Students` |
| `type` | enum | `Workshop` · `Networking` · `Demo day` · `Hackathon` · `Meet and greet` |
| `difficulty` | enum | `easy` · `medium` · `hard` |
| `track` | enum | `community` · `teaching` |
| `minutes` | number | 1–1440. How long the class runs. |
| `setupMinutes` | number or null | 0–1440. Preparation before the room starts. |
| `runner` | enum or null | `avatar` · `interview` · `robot` · `null`. **See below.** |
| `prereqs` | string[] | ≤ 60 items. What an attendee needs before starting. |
| `links` | object | `{ "starterRepo": url-or-null, "deck": url-or-null }`. `https:` only. |
| `slides` | Slide[] | ≤ 200. The deck, in order. |
| `flow` | FlowBlock[] | ≥ 1. The order the room actually runs in. |
| `sections` | Section[] | ≤ 40. Written walkthrough steps. `[]` if the class has none. |
| `troubleshooting` | string[] | ≤ 60 items. What goes wrong and what to do. |

Unknown top-level fields are rejected, so a typo surfaces instead of being silently ignored.
Whole file: 256 KB maximum.

### Slide

    { "n": 1, "kicker": "WELCOME", "title": "…", "bullets": ["…"], "note": "…" }

`n` is the slide's real position in the deck and must be unique. `bullets` ≤ 12 per slide.
`note` is the presenter note shown under the slide.

### FlowBlock

The deck is not always shown uninterrupted. `flow` says what happens in what order.

    { "type": "slides", "title": "Before the interview", "from": 1, "to": 6 }
    { "type": "runner", "title": "Your Flux interview", "note": "…" }

Rules:

- A `slides` block may only cover slide numbers that exist.
- Every slide must be covered by some block, or it would never be shown.
- A `runner` block is only allowed when `runner` is not `null`.

### Section

    { "title": "…", "summary": "…",
      "steps": [ { "id": "…", "title": "…", "instruction": "…", "check": "…" } ] }

`check` is the "done when" line. ≤ 40 steps per section.

## `runner` is the security boundary

`runner` names an interactive experience the **site already implements**:

| Value | What it is |
| --- | --- |
| `avatar` | Build a talking avatar in the browser: Deepgram Flux listens, Claude thinks, Anam renders the face. |
| `interview` | A voice interviewer that designs the attendee's agent and writes the prompt. |
| `robot` | Talk to a cardboard robot over Web Serial: a Deepgram voice agent in Chrome, and a Pico servo that moves the mouth in time with the voice. |
| `null` | Slides and written steps only. |

A class **cannot** introduce a new runner. Anything outside this list is rejected on import.
Adding one requires a reviewed change to the application and a deploy. Nothing in this
repository is ever executed on the server.

## Never in this repository

Rejected on import, and the reason this rule is enforced rather than trusted:

- API keys, tokens, private keys, bearer credentials
- Event dates, invite codes, joining links
- Attendee names, lists, or interview transcripts
- Anything specific to one running of a class

Per-event customisation lives in the site's database, attached to the event. A class update
never overwrites it.

## Example

[`avatar-workshop/site/class.json`](avatar-workshop/site/class.json) is a complete, valid
manifest with a runner, a deck and two written sections.
[`vapi-partner-event/site/class.json`](vapi-partner-event/site/class.json) shows a deck
interrupted by a runner part-way through.
