# Korean task data issues (dev 629 and 643)

Two Korean tasks of the exposed dev range (600..699) do not say what the English task and the goal say. Both are *corrections* (family
`compound.corr_dest`: "put X on A, no, actually on B"). The Korean text of a task is a paraphrase made by a model from the Korean template
(`paraphrase_model.ko`, prompt `k2`), checked by a back-translation judge. In these two the paraphrase changed the meaning, and the judge accepted it.
This note only records the errors. The data, the goals and the scoring are not changed here (frozen for experiment D and the rounds that follow).

## hl-dev-000629 (round 0 of the paraphrase)

| | text |
|---|---|
| English (task text) | Please put the blue snack bag on the wall shelf, no, actually on the desk, and grab the socks for me. Once you're finished, go back to the charging dock. |
| Korean template | 파란 과자 좀 벽 선반에, 아 아니다, 책상에 갖다 놔 주세요. 그리고 양말 좀 가져다줄래요? 다 끝나면 가서 충전하세요. |
| Korean (task text) | 벽 선반에 파란 과자 좀 놓아 주시겠어요? 아니면 책상에 두어도 돼요. 그리고 양말도 좀 가져다 주실 수 있을까요? 모두 끝나면 충전해 주세요. |
| back-translation stored | Could you please put the blue cookies on the wall shelf? Or you can leave them on the desk. And could you also bring me some socks? After everything is done, please charge them. |

Goal: snack on the desk, socks delivered to the user, docked.

* The correction became an alternative. "아 아니다" (oh no, I mean) turned into "아니면" (or): the shelf is asked first and the desk is offered as a
  second choice ("or you may leave them on the desk"). A reader that follows the Korean text may put the snack on the shelf, and the goal (desk) is then
  not met. The English text and the goal have no such choice.
* The wording is an indirect request ("could you ...?"), so the first place sounds like the main wish, the opposite of a correction that takes the first
  place back.
* The last sentence lost "go back to the dock": "충전해 주세요" is "please charge (it)", with no object and no place. The goal needs the dock (`docked`).
  The back-translation even reads it as "charge them" (the snack or socks), which a reader can take as a task on the objects.

Effect: a correct Korean reading is not unique, so a failed run on this task says little about the KO reader; the EN and KO scores of this task are not
paired on the same request.

## hl-dev-000643 (round 2 of the paraphrase)

| | text |
|---|---|
| English (task text) | Put the cup in the kitchen sink, no, actually on the desk, and then bring the white towel here, please. |
| Korean template | 컵을 개수대에, 아 아니다, 책상에 갖다 놔 주고, 하얀 수건을 가져다줄 수 있어요? |
| Korean (task text) | 컵은 책상에, 아니야 개수대에 두시고, 하얀 수건 좀 가져다 줄 수 있을까요? |
| back-translation stored | Please put the cup on the desk, no, on the sink, and could you bring me a white towel? |

Goal: cup on the desk, towel delivered to the user.

* The translation is reversed. The template says sink first, then desk (final place: desk). The paraphrase says desk first, then sink (final place:
  sink). The two places swapped around the correction word "아니야", so the final place is the one the goal does not want.
* The stored back-translation shows the reversal ("on the desk, no, on the sink"). The judge still passed it; the difference between the back-translation
  and the English text is a swap of two places, which a character-level score (chrF 75) hardly sees.

Effect: a KO reader that reads the text correctly puts the cup in the sink and fails the goal. The failure is a data error, not a reading error; it counts
against the KO cell and widens the EN to KO gap by this one task. A reader that "fixes" the order to match the English would be right for the wrong reason.

## What would fix it (not done here)

* Judge the back-translation of a correction task by its final place (the last place named before the end of the correction), not by a character score
  alone. A swap of two places or a correction turned into a choice is then a hard reject.
* Re-generate the two paraphrases, or keep the Korean template (which is right in both tasks) for the correction family.

Scope: a data note for the people who own the task data. No data file, goal or scoring rule was edited for it; the counts in experiment D are as they were.
