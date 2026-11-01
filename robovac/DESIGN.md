# Design System: profile README

## Inherited

This surface uses the Robovac widget's world:
[kstack/apps/robovac-widget/DESIGN.md](https://github.com/kadenkobashigawa/kstack/blob/main/apps/robovac-widget/DESIGN.md). That means
its palette (honey oak, cocoa line and wall, linen, chrome), its robot and dock parts (exported from
`vacuum.py` and `app/build/robot-*.svg`, copied into `robovac/parts/`), and its Motion rules:

- the robot turns on the spot, always the short way round;
- its side brushes spin only while it runs;
- its shine and shadow move with it but never turn, so the light holds still;
- it leaves its dock forward and backs in, rear half under the hood (mat drawn under the robot,
  tower over it).

## Decided here

- **Speed:** a slow roll (Kaden, 2026-11-01: "way too fast", then "slow down a little bit more"):
  30 px/s, quarter turns of 1.1 s, 4 s docked; the loop is about 114 s. The dock sits square in
  the corner, its tower 6 px in from the left and bottom borders.
- **Layout (Kaden, 2026-11-01):** GitHub's contribution panel as the profile shows it (headline,
  bordered box, months, Mon/Wed/Fri, Less/More legend), minus the "Learn how we count
  contributions" link. Robovac's dock sits in its place, bottom left, mat facing up; the robot
  leaves straight up into the bottom row, sweeps bottom to top, drives forward down the left edge
  to just short of the dock, turns round and backs in slowly (8 px/s). The grid and
  Less/More row are measured off GitHub's own panel (legend row centred at 181); the box runs
  17 px deeper than GitHub's (to 219) so the dock clears the Fri label. A
  small 11 px counter sits right of the dock on the legend's row.
- **Data:** the calendar visitors actually see, read from github.com/users/<name>/contributions,
  with GitHub's Mon/Wed/Fri and month labels.
- **Graph version:** GitHub's own contribution-cell colors (Primer), so visitors recognise their
  graph. Two files, `dist/robovac-dark.svg` and `dist/robovac-light.svg`, switched by
  `<picture>` and `prefers-color-scheme`. Labels and counter in GitHub's own sans stack, so the panel
  reads as GitHub's; the counter is 11 px, its number 600 weight with tabular figures,
  right-aligned so the words never shift.
- **Reduced motion:** SMIL ignores CSS media queries, so each file has a `-still.svg` twin (robot
  docked, nothing cleaned). The README switches to it with
  `<source media="(prefers-reduced-motion: reduce) and (prefers-color-scheme: …)">`.
- **Known gaps (accepted for now):** the docked robot shows only a sliver past the hood at this
  size; the dock is turned 180° so its baked shading turns with it, barely visible at about 32 px wide.
