# ADR 0008: prepare tomorrow

- **Date**: 2026-10-12
- **Status**: accepted

## Context

A need confirmed in use as early as 8 September 2026, after a week on
`0.10.1`: being able to prepare the next day's list before the 04:00
rollover. The evening before, you already know what will open the day;
today you have to keep it in mind or dictate it into the reserve, where
it mixes with everything else.

The need runs into two things set very early:

- `CLAUDE.md` §1 describes a method "without planning or categories"
- `docs/internal/SPECIFICATION.md` §2.5 knows only one active day, and
  the day rollover replaces it with an empty day, filled only with
  recurring items

`docs/internal/ROADMAP.md` had therefore frozen 7.3 until a dedicated
scoping session, held with VertOurs on 12 October 2026.

## Decision

A **Tomorrow** view joins the sidebar. It holds the list prepared for the
next day and shows, read-only, the recurring items that will be due that
day.

**Tomorrow is not a date.** It is the next day that will start. After
several days without opening the application, the prepared list still
becomes the day's list: it is not lost, not carried to a past date, and
not archived on its own. This follows directly from §2.5, where
intermediate days do not exist: there is only one next day, the one that
opens.

**At the day rollover**, step 6 of §2.5 still injects the new day's
recurring items first. A step 7 is added: the prepared tasks then enter
the day, in their order, as if they had been dictated at the start of the
day. They receive their numbers at that moment, after the recurring
items, and the Tomorrow list empties.

**In Tomorrow**, one can add, rename, reorder, delete, mark as priority
and draw from the reserve. Drawing remains a move, with `source_id` kept
(§2.5): a task drawn from the reserve into Tomorrow will return to the
reserve at the following rollover if it is not done, through the usual
mechanism. Nothing is struck in Tomorrow, and no task there carries a
number: numbers only exist within a day (§2.4).

**Moving a task from the day to Tomorrow**: a row menu entry and
drag-and-drop onto the Tomorrow entry of the sidebar, like the return to
the reserve (§2.5). Same restrictions: neither a struck task nor a task
from a recurring item. Allowed on a frozen list, and with no trace in the
day: the task is neither archived nor logged, and its number is never
reassigned.

**The reverse gesture exists**: bringing a task from Tomorrow back into
the day, through the row menu or by dragging it onto the day entry.
Refused on a frozen list, like drawing from the reserve. Moving to
Tomorrow has no undo; without this gesture, a mistaken move would cost
two gestures through the reserve. Added when the detail points were
validated, on 12 October 2026.

**No automatic carry-over.** A task not struck at the end of the day
still follows §2.5: back to the reserve, or dropped for a recurring
item. Moving to Tomorrow remains an explicit gesture.

## Why this is not planning

What §1 rules out is the calendar: tasks attached to dates, a schedule to
keep, a list that judges. Tomorrow carries no date and looks only one day
ahead: it is the start-of-day dictation, done the evening before. It
creates no category, no deadline and no possible delay, since whatever
was not done does not stay in Tomorrow: the list empties at every
rollover.

## Alternatives rejected

- **A weekly or monthly calendar.** Rejected: it is exactly the planning
  that §1 excludes, and it would impose dated tasks, hence delays, which
  §2.3 forbids commenting on but which a calendar shows by construction.
  Noted as a v3 candidate in "Repoussé volontairement", to see whether
  Tomorrow is enough.
- **A setting for automatic carry-over** of unstruck tasks to the next
  day, instead of the return to the reserve. Rejected for now: the
  carry-over would be silent, and a task pushed back every evening
  without deciding to ends up as a perpetual list, which the reserve
  avoids by taking tasks out of the day. Carry-over remains an explicit
  gesture. To be reassessed after two weeks of using Tomorrow.
- **Dated tasks in the reserve**, which would move over at the day
  rollover. Rejected: the reserve is the undated master list (§2.5), and
  a date per item would let the calendar in through the back door.

## Consequences

- §2.5 gains a step 7 at the day rollover, after the recurring items are
  injected, and the "no data is lost" guarantee also covers the prepared
  list
- The data format must carry the Tomorrow list: a 3 → 4 migration, tested
  like the previous ones
- A second list without numbers exists next to the day: the rule "number
  assigned on addition" (§2.4) becomes "number assigned on entering the
  day", with no change for tasks dictated during the day
- The counts of §2.6 do not see Tomorrow: a prepared task is only counted
  once it has entered a day, and a task moved out of the day leaves no
  trace there, like a return to the reserve
- The detail points (shortcuts, place in the sidebar, deletion and undo
  in Tomorrow, recurring items shown, format) are settled in
  `docs/internal/SPECIFICATION.md` before any code, as required by
  `docs/internal/ROADMAP.md`

## Addendum (2026-10-29)

The automatic carry-over setting, rejected "for now" above, is abandoned:
VertOurs's decision on 29 October 2026, without waiting for the planned
two weeks of use. Moving to Tomorrow remains an explicit gesture, and an
unstruck task still follows §2.5.
