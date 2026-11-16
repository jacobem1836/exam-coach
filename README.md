# exam-coach

An AI study method for university exams, plus a script that downloads your Echo360 lecture transcripts.

It takes a course's slides and lecture transcripts and turns them into:

1. a coverage check (what's in the material, what's missing),
2. a readable study guide (the idea, a table, a worked example, and how it's asked in the exam),
3. a day-by-day plan with an exit gate for every block,
4. teach-first review sessions with fresh questions,
5. a miss list, where a miss clears only once you get it right on a later day,
6. a timed mock exam with a root-cause pass on what went wrong, and
7. a 2–3 page cheat sheet for the morning of the exam.

It works with any AI assistant that can read and write files (Claude Code, Codex, Cursor, Gemini CLI, and others). The method is all in [`SKILL.md`](SKILL.md).

## Setup

**Claude Code:** copy the folder into your skills directory, then say "help me study for my exam".

```
git clone https://github.com/jacobem1836/exam-coach ~/.claude/skills/exam-coach
```

**Codex, Cursor, Gemini CLI, and others:** put `SKILL.md` in your study folder and add a line to that folder's `AGENTS.md` (or `GEMINI.md`, or your rules file): `Follow SKILL.md for exam prep.`

**Chat-only assistants:** paste `SKILL.md` at the start of each session, along with your `progress.md` and `misses.md`.

## Getting your transcripts from Echo360

`echo360_download.py` downloads every lecture transcript (`.vtt`) for a course. It uses only the Python standard library, so there's nothing to install.

1. Log in to Echo360 in your browser (usually through your university's LMS).
2. Export your cookies for the Echo360 site in Netscape `cookies.txt` format. Any "export cookies.txt" browser extension works.
3. Open the course in Echo360 and copy the URL. It looks like `https://echo360.net.au/section/<section-id>/home`.
4. Run:

```
python3 echo360_download.py --cookies cookies.txt --out MYCOURSE/transcripts MYCOURSE=https://echo360.net.au/section/<section-id>/home
```

Pass several `COURSE=URL` pairs to download more than one course. Add `--list` to see the lessons without downloading. Re-running skips transcripts you already have. If you get HTTP 401 or 403, your cookies have expired, so log in and export them again.

**Your cookies file is your login. Never commit or share it.** The `.gitignore` here already excludes `cookies.txt`.

Only download recordings you have access to, and check your university's rules on using them.

## Licence

MIT
