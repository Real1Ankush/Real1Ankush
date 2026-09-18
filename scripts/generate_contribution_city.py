import json
import os
import urllib.request
from datetime import date, timedelta


USERNAME = "Real1Ankush"
OUTPUT = "assets/contribution-city.svg"


# ---------------------------------------------------------
# GitHub GraphQL
# ---------------------------------------------------------

def github_graphql(query, variables):
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError("GITHUB_TOKEN is not available.")

    payload = json.dumps({
        "query": query,
        "variables": variables
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Real1Ankush-Contribution-City"
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))

    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], indent=2))

    return data["data"]


# ---------------------------------------------------------
# Get last year's contribution calendar
# ---------------------------------------------------------

today = date.today()
start_date = today - timedelta(days=365)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""

variables = {
    "login": USERNAME,
    "from": f"{start_date.isoformat()}T00:00:00Z",
    "to": f"{today.isoformat()}T23:59:59Z"
}

data = github_graphql(query, variables)

calendar = data["user"]["contributionsCollection"]["contributionCalendar"]

total_contributions = calendar["totalContributions"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append(day)


# ---------------------------------------------------------
# Colors
# ---------------------------------------------------------

BACKGROUND = "#050816"
GRID = "#10203A"
GRID_BRIGHT = "#183A5E"

TEXT = "#EAF6FF"
MUTED = "#64748B"

CYAN = "#00F5FF"
BLUE = "#2563EB"
PURPLE = "#7C3AED"
PINK = "#EC4899"


def building_color(count, maximum):
    if count <= 0:
        return GRID

    if maximum <= 0:
        return CYAN

    ratio = count / maximum

    if ratio <= 0.25:
        return CYAN

    if ratio <= 0.50:
        return BLUE

    if ratio <= 0.75:
        return PURPLE

    return PINK


def escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------
# SVG dimensions
# ---------------------------------------------------------

WIDTH = 1400
HEIGHT = 760

svg = []

svg.append(
    f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}">

    <defs>

        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#020617"/>
            <stop offset="50%" stop-color="#050816"/>
            <stop offset="100%" stop-color="#0B1025"/>
        </linearGradient>

        <linearGradient id="titleGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#00F5FF"/>
            <stop offset="50%" stop-color="#7C3AED"/>
            <stop offset="100%" stop-color="#EC4899"/>
        </linearGradient>

        <filter id="glowCyan">
            <feGaussianBlur stdDeviation="4" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>

        <filter id="glowPurple">
            <feGaussianBlur stdDeviation="5" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>

        <filter id="glowPink">
            <feGaussianBlur stdDeviation="5" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>

        <pattern
            id="stars"
            width="120"
            height="120"
            patternUnits="userSpaceOnUse">

            <circle cx="15" cy="20" r="1" fill="#334155"/>
            <circle cx="75" cy="45" r="1" fill="#475569"/>
            <circle cx="100" cy="90" r="1" fill="#334155"/>
            <circle cx="40" cy="100" r="1" fill="#475569"/>

        </pattern>

    </defs>

    <!-- BACKGROUND -->

    <rect
        width="100%"
        height="100%"
        fill="url(#bg)"/>

    <rect
        width="100%"
        height="100%"
        fill="url(#stars)"
        opacity="0.35"/>

    <!-- TOP GLOW -->

    <ellipse
        cx="700"
        cy="150"
        rx="520"
        ry="180"
        fill="#2563EB"
        opacity="0.06"/>

    <!-- TITLE -->

    <text
        x="700"
        y="70"
        text-anchor="middle"
        font-family="Arial, Helvetica, sans-serif"
        font-size="30"
        font-weight="700"
        fill="url(#titleGradient)">
        ANKUSH DATTA • CONTRIBUTION CITY
    </text>

    <text
        x="700"
        y="105"
        text-anchor="middle"
        font-family="monospace"
        font-size="15"
        fill="{MUTED}">
        {total_contributions} contributions • last 365 days
    </text>
    '''
)


# ---------------------------------------------------------
# City geometry
# ---------------------------------------------------------

# We use an isometric projection.
ORIGIN_X = 680
ORIGIN_Y = 270

STEP_X = 21
STEP_Y = 10

CELL_W = 18
CELL_H = 10

maximum = max(
    [day["contributionCount"] for day in days] or [1]
)


def project(week, weekday):
    x = ORIGIN_X + week * STEP_X - weekday * STEP_X * 0.52
    y = ORIGIN_Y + week * STEP_Y + weekday * STEP_Y * 0.92

    return x, y


# ---------------------------------------------------------
# City floor
# ---------------------------------------------------------

floor_points = [
    f"{ORIGIN_X - 20},{ORIGIN_Y - 5}",
    f"{ORIGIN_X + 52 * STEP_X + 30},{ORIGIN_Y + 52 * STEP_Y + 5}",
    f"{ORIGIN_X + 52 * STEP_X - 7 * STEP_X * 0.52 + 30},{ORIGIN_Y + 52 * STEP_Y + 7 * STEP_Y * 0.92 + 20}",
    f"{ORIGIN_X - 7 * STEP_X * 0.52 - 20},{ORIGIN_Y + 7 * STEP_Y * 0.92 + 20}"
]

svg.append(
    f'''
    <polygon
        points="{" ".join(floor_points)}"
        fill="#071226"
        stroke="{GRID_BRIGHT}"
        stroke-width="2"
        opacity="0.95"/>
    '''
)


# ---------------------------------------------------------
# Grid lines
# ---------------------------------------------------------

for week in range(54):

    points = []

    for weekday in range(8):

        x, y = project(week, weekday)

        points.append(f"{x:.1f},{y:.1f}")

    svg.append(
        f'''
        <polyline
            points="{" ".join(points)}"
            fill="none"
            stroke="{GRID}"
            stroke-width="1"
            opacity="0.75"/>
        '''
    )


for weekday in range(8):

    points = []

    for week in range(54):

        x, y = project(week, weekday)

        points.append(f"{x:.1f},{y:.1f}")

    svg.append(
        f'''
        <polyline
            points="{" ".join(points)}"
            fill="none"
            stroke="{GRID}"
            stroke-width="1"
            opacity="0.75"/>
        '''
    )


# ---------------------------------------------------------
# Buildings
# ---------------------------------------------------------

for index, day in enumerate(days):

    count = day["contributionCount"]

    week = index // 7
    weekday = day["weekday"]

    x, y = project(week, weekday)

    # No contributions = subtle floor tile.
    if count <= 0:

        tile = [
            f"{x},{y}",
            f"{x + CELL_W},{y + CELL_H}",
            f"{x},{y + CELL_H * 2}",
            f"{x - CELL_W},{y + CELL_H}"
        ]

        svg.append(
            f'''
            <polygon
                points="{" ".join(tile)}"
                fill="#081426"
                stroke="#10233D"
                stroke-width="1"/>
            '''
        )

        continue


    # Building height.
    height = min(
        130,
        14 + count * 12
    )

    color = building_color(
        count,
        maximum
    )


    # Top face.
    top = [
        f"{x},{y - height}",
        f"{x + CELL_W},{y - height + CELL_H}",
        f"{x},{y - height + CELL_H * 2}",
        f"{x - CELL_W},{y - height + CELL_H}"
    ]


    # Left face.
    left = [
        f"{x - CELL_W},{y - height + CELL_H}",
        f"{x},{y - height + CELL_H * 2}",
        f"{x},{y + CELL_H * 2}",
        f"{x - CELL_W},{y + CELL_H}"
    ]


    # Right face.
    right = [
        f"{x},{y - height + CELL_H * 2}",
        f"{x + CELL_W},{y - height + CELL_H}",
        f"{x + CELL_W},{y + CELL_H}",
        f"{x},{y + CELL_H * 2}"
    ]


    glow = ""

    if count >= max(2, maximum * 0.5):
        glow = 'filter="url(#glowPurple)"'


    svg.append(
        f'''
        <polygon
            points="{" ".join(left)}"
            fill="{color}"
            opacity="0.62"/>

        <polygon
            points="{" ".join(right)}"
            fill="{color}"
            opacity="0.85"/>

        <polygon
            points="{" ".join(top)}"
            fill="{color}"
            stroke="#FFFFFF"
            stroke-width="0.7"
            opacity="0.95"
            {glow}/>

        <line
            x1="{x - CELL_W + 3}"
            y1="{y - height + CELL_H + 4}"
            x2="{x - 2}"
            y2="{y - height + CELL_H * 2 - 1}"
            stroke="#FFFFFF"
            stroke-width="1"
            opacity="0.20"/>

        <line
            x1="{x + 2}"
            y1="{y - height + CELL_H * 2 - 1}"
            x2="{x + CELL_W - 3}"
            y2="{y - height + CELL_H + 4}"
            stroke="#FFFFFF"
            stroke-width="1"
            opacity="0.28"/>
        '''
    )


# ---------------------------------------------------------
# Month labels
# ---------------------------------------------------------

months_seen = set()

for index, day in enumerate(days):

    current = day["date"]

    if current.endswith("-01"):

        month = current[:7]

        if month in months_seen:
            continue

        months_seen.add(month)

        week = index // 7
        weekday = day["weekday"]

        x, y = project(week, weekday)

        month_name = current[5:7]

        names = {
            "01": "JAN",
            "02": "FEB",
            "03": "MAR",
            "04": "APR",
            "05": "MAY",
            "06": "JUN",
            "07": "JUL",
            "08": "AUG",
            "09": "SEP",
            "10": "OCT",
            "11": "NOV",
            "12": "DEC"
        }

        label = names.get(month_name, "")

        svg.append(
            f'''
            <text
                x="{x}"
                y="{y - 150}"
                font-family="monospace"
                font-size="12"
                fill="{MUTED}"
                opacity="0.9">
                {label}
            </text>
            '''
        )


# ---------------------------------------------------------
# Legend
# ---------------------------------------------------------

legend_y = 675

svg.append(
    f'''
    <text
        x="70"
        y="{legend_y}"
        font-family="monospace"
        font-size="13"
        fill="{MUTED}">
        ACTIVITY
    </text>
    '''
)


legend = [
    ("LOW", CYAN),
    ("MED", BLUE),
    ("HIGH", PURPLE),
    ("PEAK", PINK)
]

for i, (label, color) in enumerate(legend):

    x = 155 + i * 115

    svg.append(
        f'''
        <rect
            x="{x}"
            y="{legend_y - 13}"
            width="14"
            height="14"
            rx="3"
            fill="{color}"/>

        <text
            x="{x + 21}"
            y="{legend_y}"
            font-family="monospace"
            font-size="11"
            fill="{TEXT}">
            {label}
        </text>
        '''
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

svg.append(
    f'''
    <text
        x="1330"
        y="710"
        text-anchor="end"
        font-family="monospace"
        font-size="12"
        fill="{MUTED}">
        github.com/Real1Ankush
    </text>

    </svg>
    '''
)


# ---------------------------------------------------------
# Write SVG
# ---------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as file:

    file.write("\n".join(svg))


print(
    f"Generated {OUTPUT} "
    f"with {total_contributions} contributions."
)
