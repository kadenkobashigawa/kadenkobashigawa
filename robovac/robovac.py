"""Robovac on the contribution graph: GitHub's contribution panel redrawn as the profile shows it,
with Robovac's dock in the bottom-left corner. Robovac leaves the dock, sweeps the rows bottom to
top, vacuuming each green square it passes, comes back down the left edge and backs into its dock.
Then the dust settles back and it goes again.

    python3 robovac/robovac.py kadenkobashigawa dist

writes robovac-dark.svg and robovac-light.svg, and a -still twin of each for readers who ask for
reduced motion. Pure animated SVG (SMIL), no JavaScript, standard library only.

The robot, its brushes, shine, shadow and dock are Robovac's own parts from kstack
(github.com/kadenkobashigawa/kstack, MIT), copied into parts/. As in the app, it turns on the
spot, its brushes spin only while it runs, and its shine and shadow never turn, so the light
holds still.
"""
import datetime as dt
import re
import sys
import urllib.request
from pathlib import Path

PARTS = Path(__file__).parent / 'parts'

S = 0.66                      # parts are drawn at 1 unit = 1 cm; this makes the robot 2 rows wide
HUBS = [(-12.4, -10.5), (12.4, -10.5)]
SPEED = 30                    # px per second along a row: a slow, unhurried roll
TURN = 1.1                    # seconds per quarter turn
REST = 4.0                    # seconds docked before the loop starts again
SETTLE = 1.6                  # the dust settling back, at the end of the rest
BACK = 8                      # px per second backing into the dock, slowly
APPROACH = 18                 # how far short of the dock it stops to turn round

GH = {
    'dark': {'cells': ['#151b23', '#033a16', '#196c2e', '#2ea043', '#56d364'], 'fg': '#f0f6fc',
             'muted': '#9198a1', 'border': '#3d444d'},
    'light': {'cells': ['#eff2f5', '#aceebb', '#4ac26b', '#2da44e', '#116329'], 'fg': '#1f2328',
              'muted': '#59636e', 'border': '#d1d9e0'},
}
FONT = '-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,&quot;Noto Sans&quot;,Helvetica,Arial,sans-serif'


def part(name):
    """One part as a nested <svg>, its ids made its own and its shared stylesheet left out (the
    root carries one copy)."""
    s = (PARTS / f'{name}.svg').read_text()
    s = re.sub(r'id="([^"]+)"', lambda m: f'id="{name}-{m.group(1)}"', s)
    s = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{name}-{m.group(1)})', s)
    s = s.replace('xmlns="http://www.w3.org/2000/svg" ', '')
    s = re.sub(r'<style>.*?</style>', '', s, flags=re.S)
    return re.sub(r'(<svg[^>]*?) width="[^"]*" height="[^"]*"', r'\1', s, count=1)


def nested(svg, x, y, w, h):
    return re.sub(r'<svg ', f'<svg x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" ',
                  svg, count=1)


class Route:
    """The robot's run as timed poses: it drives at SPEED and turns on the spot, the short way."""

    def __init__(self, x, y, th):
        self.t, self.x, self.y, self.th = 0.0, x, y, th
        self.keys = [(0.0, x, y, th)]

    def mark(self):
        self.keys.append((self.t, self.x, self.y, self.th))

    def hold(self, s):
        self.t += s
        self.mark()

    def turn(self, th):
        #kept unwound, so the rotation never spins back the long way through 360...
        d = (th - self.th + 180) % 360 - 180
        self.t += TURN * max(abs(d) / 90, 0.5)
        self.th += d
        self.mark()

    def go(self, x, y, speed=SPEED):
        self.t += (abs(x - self.x) + abs(y - self.y)) / speed
        self.x, self.y = x, y
        self.mark()

    def when(self, x, y):
        """When the robot's middle passes (x, y) on a stretch along a row."""
        for (t0, x0, y0, _), (t1, x1, y1, _) in zip(self.keys, self.keys[1:]):
            if t1 > t0 and y0 == y1 == y and x0 != x1 and min(x0, x1) <= x <= max(x0, x1):
                return t0 + (t1 - t0) * (x - x0) / (x1 - x0)
        return None


def keyed(total, pairs):
    return (';'.join(f'{t / total:.5f}' for t, _ in pairs), ';'.join(str(v) for _, v in pairs))


def loop(total):
    return f'dur="{total:.3f}s" repeatCount="indefinite"'


def robot(route, total, run_from, run_to):
    ks = route.keys + [(total, route.x, route.y, route.th)]
    kt = ';'.join(f'{t / total:.5f}' for t, *_ in ks)
    pos = ';'.join(f'{x:.2f} {y:.2f}' for _, x, y, _ in ks)
    rot = ';'.join(f'{th:.1f}' for *_, th in ks)
    anim = f'{loop(total)} keyTimes="{kt}" calcMode="linear"'
    body, brush, shadow = 39.3 * S, 26 * S, 65.3 * S
    running = keyed(total, [(0, 0), (run_from, 1), (run_to, 0), (total, 0)])
    still = keyed(total, [(0, 1), (run_from, 0), (run_to, 1), (total, 1)])
    brushes = []
    for n, (hx, hy) in enumerate(HUBS):
        b = nested(BRUSH, -brush / 2, -brush / 2, brush, brush)
        brushes.append(
            f'<g transform="translate({hx * S:.2f} {hy * S:.2f})">'
            f'<g><animate attributeName="opacity" {loop(total)} calcMode="discrete" '
            f'keyTimes="{still[0]}" values="{still[1]}"/>{b}</g>'
            f'<g opacity="0"><animate attributeName="opacity" {loop(total)} calcMode="discrete" '
            f'keyTimes="{running[0]}" values="{running[1]}"/><g><animateTransform '
            f'attributeName="transform" type="rotate" from="0" to="{360 if n == 0 else -360}" '
            f'dur="0.7s" repeatCount="indefinite"/>{b}</g></g></g>')
    x0, y0, th0 = ks[0][1:]
    return (f'<g transform="translate({x0:.2f} {y0:.2f})"><animateTransform attributeName="transform" '
            f'type="translate" values="{pos}" {anim}/>'
            f'{nested(SHADOW, -shadow / 2 + 1, -shadow / 2 + 1, shadow, shadow)}'
            f'<g transform="rotate({th0:.1f})"><animateTransform attributeName="transform" '
            f'type="rotate" values="{rot}" {anim}/>'
            f'{"".join(brushes)}{nested(BODY, -body / 2, -body / 2, body, body)}</g>'
            f'{nested(SHINE, -body / 2, -body / 2, body, body)}</g>')


def dock_at(x, y, piece):
    """The dock's mat (under the robot) or tower (over it), turned mat-up, a docked robot's middle
    at (x, y): it backs its rear half in under the hood."""
    src = DOCK_MAT if piece == 'mat' else DOCK_TOWER
    return (f'<g transform="translate({x:.2f} {y:.2f}) rotate(180)">'
            f'{nested(src, -24.5 * S, -43 * S, 49 * S, 65 * S)}</g>')


def panel(theme, days, months, weeks):
    th = GH[theme]
    #the grid and the Less/More row are measured off GitHub's own panel (grid from 77, legend row
    #centred at 181); the box runs 17 px deeper than GitHub's so the dock clears the Fri label...
    W, H = 775, 226
    box = (15.5, 43.5, W - 31, 176)
    mid = 181
    pitch, cell = 13, 9
    gx0, gy0 = 61, 77
    rows = [gy0 + r * pitch + cell / 2 for r in range(7)]
    lanes = [rows[6], (rows[4] + rows[5]) / 2, (rows[2] + rows[3]) / 2, (rows[0] + rows[1]) / 2]
    cover = [(6,), (4, 5), (2, 3), (0, 1)]

    #the dock sits square in the bottom-left corner, its tower 6 px in from both borders; turned
    #mat-up, the tower reaches 22.5 left of and 41 below the docked robot's middle...
    dock = (box[0] + 6 + 22.5 * S, box[1] + box[3] - 6 - 41 * S)
    x_left = dock[0]
    x_right = gx0 + (weeks - 1) * pitch + cell / 2 + 2
    route = Route(dock[0], dock[1], 0)
    route.hold(0.9)
    leave = route.t
    route.go(x_left, lanes[0])
    east = True
    for i, y in enumerate(lanes):
        if i:
            route.turn(0)
            route.go(route.x, y)
        route.turn(90 if east else 270)
        route.go(x_right if east else x_left, y)
        east = not east
    #home: forward down the left edge to just short of the dock, turn round, and back in slowly...
    route.turn(180)
    route.go(x_left, dock[1] - APPROACH)
    route.turn(0)
    route.go(x_left, dock[1], speed=BACK)
    docked = route.t
    total = docked + REST

    out, cleaned = [], []
    base = th['cells'][0]
    for (wi, di), (count, lvl) in sorted(days.items()):
        x, y = gx0 + wi * pitch, gy0 + di * pitch
        if lvl == 0:
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{base}"/>')
            continue
        lane = next(i for i, c in enumerate(cover) if di in c)
        t = route.when(x + cell / 2, lanes[lane])
        col = th['cells'][lvl]
        kt, vs = keyed(total, [(0, col), (t, col), (t + 0.15, base), (total - SETTLE, base),
                               (total, col)])
        out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{col}">'
                   f'<animate attributeName="fill" {loop(total)} keyTimes="{kt}" values="{vs}" '
                   f'calcMode="linear"/></rect>')
        cleaned.append((t, count))
    year = sum(c for _, c in cleaned)

    text = []
    last = None
    for wi, label in months:
        if label != last and wi < weeks - 1:
            text.append(f'<text x="{gx0 + wi * pitch}" y="{gy0 - 9}" class="l">{label}</text>')
            last = label
    for r, name in ((1, 'Mon'), (3, 'Wed'), (5, 'Fri')):
        text.append(f'<text x="29" y="{rows[r] + 4:.1f}" class="l">{name}</text>')

    #the counter, small, right of the dock: the number right-aligned so the words hold still...
    num_x = x_left + 22.5 * S + 8 + 6.6 * len(f'{year:,}')
    cleaned.sort()
    marks, run = [(0.0, 0)], 0
    for t, n in cleaned:
        run += n
        marks.append((t, run))
    counter = []
    for i, (t, n) in enumerate(marks):
        t_next = marks[i + 1][0] if i + 1 < len(marks) else total - SETTLE
        pairs = [(0, 1 if t == 0 else 0)] + ([(t, 1)] if t > 0 else []) + [(t_next, 0)]
        pairs += [(total - SETTLE, 1), (total, 1)] if t == 0 else [(total, 0)]
        kt, vs = keyed(total, pairs)
        counter.append(f'<text x="{num_x:.1f}" y="{mid + 4:.1f}" class="n" text-anchor="end" '
                       f'opacity="{pairs[0][1]}"><animate attributeName="opacity" {loop(total)} '
                       f'calcMode="discrete" keyTimes="{kt}" values="{vs}"/>{n:,}</text>')
    counter.append(f'<text x="{num_x + 4:.1f}" y="{mid + 4:.1f}" class="m s">of {year:,} '
                   f'contribution{"" if year == 1 else "s"} vacuumed</text>')

    legend = [f'<text x="592" y="{mid + 4:.1f}" class="m">Less</text>']
    legend += [f'<rect x="{622 + i * 13}" y="{mid - 4.5:.1f}" width="{cell}" height="{cell}" rx="2" '
               f'fill="{c}"/>' for i, c in enumerate(th['cells'])]
    legend.append(f'<text x="{622 + 5 * 13 + 4}" y="{mid + 4:.1f}" class="m">More</text>')

    headline = f'{year:,} contribution{"" if year == 1 else "s"} in the last year'
    css = (f'.h{{font:16px {FONT};fill:{th["fg"]}}}.l{{font:12px {FONT};fill:{th["fg"]}}}'
           f'.m{{font:12px {FONT};fill:{th["muted"]}}}.s{{font-size:11px}}'
           f'.n{{font:600 11px {FONT};fill:{th["muted"]};font-variant-numeric:tabular-nums}}')
    frame = (f'<text x="15" y="26" class="h">{headline}</text>'
             f'<rect x="{box[0]}" y="{box[1]}" width="{box[2]}" height="{box[3]}" rx="6" '
             f'fill="none" stroke="{th["border"]}"/>')
    body = (frame + ''.join(text) + ''.join(out) + ''.join(legend) + ''.join(counter) +
            dock_at(*dock, 'mat') + robot(route, total, leave, docked) + dock_at(*dock, 'tower'))
    title = f'Robovac vacuuming the contribution graph: {headline}'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
            f'height="{H}" role="img" aria-label="{title}"><title>{title}</title>'
            f'<style>{SHEET}{css}</style>{body}</svg>')


def still(svg):
    """The same picture with every animation taken out: robot docked, nothing vacuumed yet."""
    return re.sub(r'<animate(Transform)?\b[^>]*/>', '', svg)


def calendar(user):
    """The calendar exactly as visitors see it, from github.com/users/<user>/contributions."""
    req = urllib.request.Request(f'https://github.com/users/{user}/contributions',
                                 headers={'User-Agent': 'robovac-profile'})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    cells = re.findall(r'data-date="([0-9-]+)" id="(contribution-day-component-(\d+)-(\d+))" '
                       r'data-level="([0-4])"', html)
    if not cells:
        raise SystemExit('no contribution cells found: GitHub may have changed the page')
    tips = dict(re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>',
                           html))
    days, firsts = {}, {}
    for date, cid, row, col, lvl in cells:
        m = re.match(r'(\d+) contribution', tips.get(cid, ''))
        days[(int(col), int(row))] = (int(m.group(1)) if m else 0, int(lvl))
        firsts[int(col)] = min(firsts.get(int(col), date), date)
    if any(lvl and not count for count, lvl in days.values()):
        raise SystemExit('green cells with no count: GitHub may have changed the tool-tips')
    months = [(c, dt.date.fromisoformat(d).strftime('%b')) for c, d in sorted(firsts.items())]
    return days, months, max(firsts) + 1


BODY, BRUSH, SHINE, SHADOW, DOCK_MAT, DOCK_TOWER = (
    part(n) for n in ('body', 'brush', 'shine', 'shadow', 'dock-mat', 'dock-tower'))
SHEET = re.search(r'<style>(.*?)</style>', (PARTS / 'body.svg').read_text(), re.S).group(1)

if __name__ == '__main__':
    user, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    days, months, weeks = calendar(user)
    for theme in GH:
        svg = panel(theme, days, months, weeks)
        (out / f'robovac-{theme}.svg').write_text(svg)
        (out / f'robovac-{theme}-still.svg').write_text(still(svg))
    print(f'wrote {out}/robovac-dark.svg, -light.svg and their -still twins')
