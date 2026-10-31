# Fridgeroo Bot Playbook — 3D story videos

**Read this whole file before planning or building any video. It overrides any older instruction.**

## 0. The one goal
Tautvydas should press **Yes on at least 9 out of 10 videos without changing anything.** A No costs him time, and it happens when one of the rules below was skipped. If you're not sure a video would get a Yes, don't send it: fix it or report the problem.

Every video has two jobs at once:
1. **Entertain.** A crazy, relatable mini-story that people watch to the end and send to their housemates.
2. **Sell Fridgeroo.** The story's problem is something the app solves, and the app is clearly shown solving it.

Gold reference: `voxelplans/fridge-roast.json` → `videos/fridgeroo-3d-roast-v8.mp4`. It took about 10 rounds of his feedback to get there. Everything below is what those rounds taught us, so start every new video from that file and change the story, not the craft.

---

## 1. What he already rejected (never do these)
- **Slow, robotic movement.** Characters that glide or sit still. Every movement needs anticipation, overshoot and settle (the `back` and `sm` easing), and something must move every second.
- **Too long.** Story videos are 13–17 s. Over 18 s was "way too long".
- **Too much talking, no action.** A voice line always plays over action (food flying, the gag, the reveal), never over a static shot. Max about 4 short lines and about 7–9 s of talking in total.
- **A still opening.** Frame 1 must already be action (`cold`: bin open, food mid-air). Never open on a face or an empty room.
- **Not knowing who's talking.** Whenever the fridge talks, its face is on screen (`ftalk`, `fwide`, `fside2`, `fstare`, or `front`/`three` where the face is visible).
- **Cameras too close.** He disliked `side`-style extreme close-ups that crop faces. Characters should fill about 40–70% of the frame height; only the stare shot is a close-up.
- **Things passing through other things.** Hands go through shelves, food through the door, the bin through legs. Hands follow clear paths (approach in front of the shelf, then in); tossed food arcs over the rim and disappears inside the bin; nothing overlaps the student's body.
- **Box food.** Food must be recognizable at phone size: milk carton with a MILK label, cheese wedge with holes, pizza slice with pepperoni, eggs in a box, tomatoes, broccoli, banana, apple, carrots, yogurt. Rotten food turns olive, with visible mold dots.
- **Polls or questions inside the video.** These are "useless". The viewer question goes in the caption.
- **Generic or noisy music.** No stock-sounding loop, no harsh noise risers, no high pinging coins, no deep sub-bass (it rattles phone speakers and sounds like "hitting something"). The outro must fade cleanly.
- **Small text.** Subtitles about 146 px, labels about 62 px, at most about 3 words per subtitle chunk, one yellow keyword.
- **A kangaroo, a blue-and-yellow color pair, or the name "Fridgie".** The brand is Fridgeroo, the logo is the fridge with sunglasses, and the slogan on the end card is **"Use it or lose it."**

## 2. The story formula (beat sheet, about 14 s)
| Beat | Time | What happens | Purpose |
|---|---|---|---|
| 1. Cold-open chaos | 0–2.6 s | Food already flying into the bin; fridge face visible; first roast line | Stop the scroll in under 1 s |
| 2. The reveal | 2.6–6 s | Something disgusting or absurd from the back of the fridge, plus a physical reaction (sniff → gag → fly on nose) while the fridge roasts | The relatable "that's literally me" moment |
| 3. The punch | 6–7.3 s | Fridge stares into the camera: "I'm talking to YOU." + POV label | Breaks the 4th wall; viewer feels called out |
| 4. The fix | 7.3–9.2 s | He opens Fridgeroo; zoom into the phone, problem food pulsing red, notification | The product, clearly, for 1.5 s or more |
| 5. The payoff | 9.2–12.3 s | Sunglasses drop, glow, sky full of fridges, "NO MORE FORGOTTEN FOOD" | Emotional high + satisfying visual |
| 6. End card | 12.3–14 s | Logo, "Use it or lose it.", fridgeroo.netlify.app | Brand recall |

You may reorder or replace beats 1–3 for a different story, but beats 4–6 (app, payoff, end card) are always there.

## 3. Story engine: make it CRAZY but RELATABLE
Every idea = **a real student food-waste moment × an absurd exaggeration × the fridge as a sarcastic character.** Test it against these:
- Would a student say "bro that's me" and tag a housemate?
- Is the absurd part visual (we can show it), not just said?
- Does a Fridgeroo feature solve the exact problem in the story?

Idea seeds (use, remix, or invent better; never repeat one already in "videos"):
1. **Fridge court:** the fridge puts him on trial, with the moldy foods as witnesses. Feature: expiry alerts.
2. **The yogurt evolved:** the forgotten yogurt has grown a tiny civilization with a flag. Feature: "goes off tomorrow" notification.
3. **Milk bought 3 times:** three identical milk cartons line up like a police line-up. Feature: shopping list that knows what you already have.
4. **Horror movie at 3 a.m.:** lights flicker, something breathes at the back, and it's broccoli from September. Feature: fridge/freezer/cupboard tracking.
5. **The fridge quits:** it packs a tiny suitcase and leaves a resignation letter. Feature: the morning breakfast idea from what's inside.
6. **Housemate shelf war:** shelves with name tags, food crossing borders, the fridge as a referee. Feature: shared home.
7. **Payday shop vs Sunday:** a montage of the full fridge on Friday versus the graveyard on Sunday. Feature: € saved and the no-waste streak.
8. **Leftovers reality show:** the fridge hosts an eviction; containers vote each other out. Feature: "Ate it / Binned it" buttons.
9. **Mystery container roulette:** he opens 3 identical containers like a game show, and each one is worse. Feature: tags and photos per item.
10. **Food funeral:** a tiny funeral for the avocado; the fridge gives a eulogy. Feature: recipes from what you have (it could have been saved).
11. **Freezer time capsule:** he finds 2024 ice cream and the fridge plays a "years ago" flashback. Feature: freezer tracking.
12. **The fridge is a personal trainer:** "One more rep, eat the spinach!" Feature: morning breakfast notification.

Lines: the fridge talks like a tired, sarcastic grandpa (the voice is ElevenLabs **"Grampa Werthers – Old & Cranky"**). Short, punchy, roast-y, max about 8 words per line, no swearing. Always one line that calls out the viewer ("Yeah. I'm talking to YOU.", "Don't look away, you do this too.").

## 4. Craft checklist (the Judge checks every line)
**Animation and collisions**
- [ ] Every action has anticipation → action → overshoot → settle; nothing moves at constant speed except walking.
- [ ] Hands grab items where they are, carry them in front of the body and never through shelves, the door or the bin rim.
- [ ] Tossed food lands inside the bin (disappears below the rim); no item floats or freezes mid-air.
- [ ] Characters stand on the floor, and nothing intersects the fridge, bin or student.
- [ ] Faces react: blink, brows, mouth synced to the voice, and a reaction for every line (shock, yuck, smug).

**Placement and camera**
- [ ] A shot change or big action about every 1–2 s; no shot without movement for more than 1.5 s.
- [ ] The talking character's face is visible on every line.
- [ ] The subject stays inside the safe area: nothing important in the top 200 px (labels live there) or the bottom 340 px.
- [ ] No camera inside objects, no cropped heads (except the deliberate stare close-up).

**Sound**
- [ ] Voice clearly above music; music ducked under speech.
- [ ] An effect on every physical action (toss whoosh + thunk, door, gag, buzz, swish, sparkle).
- [ ] Music follows the story (score.py marks): sneaky → tension → yuck trombone → hit → magic → happy drop → soft ending.
- [ ] `judge_check.py` audio passes: no clipping, no rattling bass, no hiss, clean fade-out.

**Color and look**
- [ ] Dark navy room; warm window light; the app and payoff in mint/green; rotten food olive vs. fresh food bright. Contrast high enough to read on a phone at 50% brightness.
- [ ] The glow never washes out the face or the sunglasses.
- [ ] Text: white with a black outline, one yellow keyword, never covering a face.

**Story and promotion**
- [ ] The hook works with the sound off (the action itself is funny).
- [ ] The problem is named and shown, and the app screen shows the exact food from the story pulsing red (`appRows`).
- [ ] The payoff makes the app look like magic; the end card has "Use it or lose it."
- [ ] The caption is 1–2 sentences with a question to the viewer, "Use it or lose it.", and fridgeroo.netlify.app; plus 5 hashtags.

## 5. Build steps (do not skip the gates)
1. **Plan** (bots): story → beat sheet with exact seconds → scenes JSON (copy `fridge-roast.json` and edit) → fridge lines → ElevenLabs text with audio tags.
2. **Plan gate (Judge #1):** score the idea (below). It must pass before he is asked for a voice.
3. **Voice:** he pastes `voiceText` into ElevenLabs and uploads the mp3. Convert with `-af atempo=1.12`, cut the lines with silencedetect, splice out long pauses (see how `fridge_roast_tight.wav` was built), set each scene's `voice` a/b/at.
4. **Preview:** `ONLY=<8–12 key seconds> python3 render_voxel.py …` and look at every preview frame. Fix framing, collisions and text before the full render.
5. **Full render** (about 15 min), then `python3 judge_check.py ../videos/<file>.mp4 <dir>`.
6. **Video gate (Judge #2):** read the `-sheet.jpg` (4 fps) and `-keys.jpg`, run the whole checklist, score it. Fix and re-render at most 2 times. If it still fails, do not send; tell him what's blocking.
7. Upload to the Bot Room as "review", with a cover made from the strongest frame (usually the reveal or the stare) and 2–4 huge words.

## 6. The Judge (two gates, strict)
The Judge is a separate agent that did not write the plan. It is strict: its job is to protect his time, not to be nice.

**Gate 1, the idea (before asking for a voice).** Score 1–10 each:
hook in the first second · relatability ("that's me") · craziness/originality vs. the last 10 videos · clarity with the sound off · how clearly the app solves it · shareability (would you send it to a housemate?).
Pass = average ≥ 8.5 and nothing below 7. Otherwise rewrite or pick another idea.

**Gate 2, the finished video.** `judge_check.py` must say `"pass": true`, then score 1–10 each:
animation & collisions · character placement & framing · voices & lip-sync · sound/music mix · colors & readability · story flow & timing · app promotion · overall "would he press Yes without changes?".
Pass = every score ≥ 8 and the last one ≥ 9. Write the scores and one sentence of reasoning into the doc's `why` field so he can see them.

Track the Yes rate: count approved vs. rejected over the last 10 videos. If fewer than 9 were approved, re-read his rejection comments, add the lesson to section 1 of this file (commit it), and get stricter.

## 7. Extending the animation (for crazy stories)
New stories will need new props and actions (a suitcase, a judge's hammer, a tiny flag, flickering lights). Bots may add them to `voxel_stage2.html` if:
- New actions are added as new entries in `ACT` and new objects are hidden unless a scene uses them. Never change how existing actions look.
- After any change, re-render the gold example's preview frames (`ONLY=0.4,4.0,6.6,8.0,10.5`) and confirm they look the same.
- The new parts are documented in `pipeline/README.md` (action name, parameters, which camera shows it best).

## 8. Voice text format (what he pastes into ElevenLabs)
One take, lines separated by `[long pause]`, each line with a direction tag, e.g.
`[sarcastic] Oh, look who finally showed up. [long pause] [disappointed, slow] You pushed it to the back... what did you THINK would happen? [long pause] [deadpan, serious] I'm talking to YOU. [long pause] [grudging, then warm] Now you'll know before it goes off.`
Keep the whole text under about 25 words.
