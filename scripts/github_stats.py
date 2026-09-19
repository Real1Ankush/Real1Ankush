import json
import os
import urllib.request
from collections import defaultdict


USERNAME = "Real1Ankush"
OUTPUT_FILE = "assets/github-stats.svg"


# =========================================================
# GitHub GraphQL
# =========================================================

QUERY = """
query($login: String!) {
  user(login: $login) {

    name
    login
    followers {
      totalCount
    }
    following {
      totalCount
    }

    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      totalContributions
      totalRepositoriesWithContributedCommits

      contributionCalendar {
        totalContributions
      }
    }

    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
      isFork: false
    ) {
      totalCount

      nodes {
        name
        stargazerCount

        languages(
          first: 10
          orderBy: {
            field: SIZE
            direction: DESC
          }
        ) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""


def github_query():

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN environment variable is missing."
        )

    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME
        }
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Real1Ankush-GitHub-Stats"
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    if "errors" in result:

        raise RuntimeError(
            json.dumps(
                result["errors"],
                indent=2
            )
        )

    return result["data"]["user"]


# =========================================================
# Fetch GitHub data
# =========================================================

user = github_query()

contributions = user["contributionsCollection"]

repositories = user["repositories"]["nodes"]


# =========================================================
# Stats
# =========================================================

total_stars = sum(
    repo["stargazerCount"]
    for repo in repositories
)

total_commits = contributions[
    "totalCommitContributions"
]

total_prs = contributions[
    "totalPullRequestContributions"
]

total_issues = contributions[
    "totalIssueContributions"
]

total_reviews = contributions[
    "totalPullRequestReviewContributions"
]

total_repositories = contributions[
    "totalRepositoryContributions"
]

total_contributions = contributions[
    "totalContributions"
]

contributed_repositories = contributions[
    "totalRepositoriesWithContributedCommits"
]


# =========================================================
# Language statistics
# =========================================================

language_sizes = defaultdict(int)

language_colors = {}

for repo in repositories:

    languages = repo.get("languages")

    if not languages:
        continue

    for edge in languages["edges"]:

        language = edge["node"]["name"]

        size = edge["size"]

        language_sizes[language] += size

        if edge["node"].get("color"):

            language_colors[language] = (
                edge["node"]["color"]
            )


total_language_size = sum(
    language_sizes.values()
)


language_data = []

if total_language_size > 0:

    for language, size in language_sizes.items():

        percentage = (
            size / total_language_size
        ) * 100

        language_data.append(
            (
                language,
                percentage,
                language_colors.get(
                    language,
                    "#00D4FF"
                )
            )
        )


language_data.sort(
    key=lambda item: item[1],
    reverse=True
)


# Keep top 5 and group the rest
TOP_LANGUAGES = 5

if len(language_data) > TOP_LANGUAGES:

    top = language_data[:TOP_LANGUAGES]

    other_percentage = sum(
        item[1]
        for item in language_data[TOP_LANGUAGES:]
    )

    language_data = top + [
        (
            "Other",
            other_percentage,
            "#64748B"
        )
    ]


# =========================================================
# SVG helpers
# =========================================================

def escape(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# =========================================================
# Activity score
# =========================================================
#
# This is only a visual "activity index".
# It is NOT an official GitHub score.
#

activity_score = min(
    99,
    max(
        1,
        round(
            (
                total_commits * 0.15
                + total_prs * 2
                + total_issues * 1.5
                + total_reviews * 1.5
                + total_repositories * 4
                + total_stars * 2
            )
        )
    )
)


# =========================================================
# SVG
# =========================================================

WIDTH = 1200
HEIGHT = 430

CARD_WIDTH = 560
CARD_HEIGHT = 350

LEFT_X = 25
RIGHT_X = 615
TOP_Y = 40

BACKGROUND = "#0D1117"
CARD = "#11111F"
BORDER = "#64748B"

WHITE = "#F8FAFC"
TEXT = "#D8DEE9"
MUTED = "#64748B"

CYAN = "#00D4FF"
PURPLE = "#A855F7"
PINK = "#FF4F9A"


svg = []

svg.append(
    f'''<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<defs>

    <linearGradient
        id="borderGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="1">

        <stop
            offset="0%"
            stop-color="{CYAN}"/>

        <stop
            offset="50%"
            stop-color="{PURPLE}"/>

        <stop
            offset="100%"
            stop-color="{PINK}"/>

    </linearGradient>

    <linearGradient
        id="titleGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="0">

        <stop
            offset="0%"
            stop-color="{CYAN}"/>

        <stop
            offset="100%"
            stop-color="{PINK}"/>

    </linearGradient>

    <filter id="glow">

        <feGaussianBlur
            stdDeviation="4"
            result="blur"/>

        <feMerge>

            <feMergeNode
                in="blur"/>

            <feMergeNode
                in="SourceGraphic"/>

        </feMerge>

    </filter>

</defs>


<!-- Background -->

<rect
    width="100%"
    height="100%"
    fill="{BACKGROUND}"/>


<!-- ================================================= -->
<!-- LEFT CARD -->
<!-- ================================================= -->

<rect
    x="{LEFT_X}"
    y="{TOP_Y}"
    width="{CARD_WIDTH}"
    height="{CARD_HEIGHT}"
    rx="12"
    fill="{CARD}"
    stroke="url(#borderGradient)"
    stroke-width="2"/>


<!-- Title -->

<text
    x="{LEFT_X + 25}"
    y="{TOP_Y + 45}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="21"
    font-weight="700"
    fill="url(#titleGradient)">

    {escape(USERNAME)}'s GitHub Stats

</text>


<!-- Stats -->

<text
    x="{LEFT_X + 30}"
    y="{TOP_Y + 90}"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="{TEXT}">

    ☆  Total Stars:

</text>

<text
    x="{LEFT_X + 315}"
    y="{TOP_Y + 90}"
    font-family="monospace"
    font-size="17"
    font-weight="700"
    fill="{CYAN}">

    {total_stars}

</text>


<text
    x="{LEFT_X + 30}"
    y="{TOP_Y + 130}"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="{TEXT}">

    ◷  Total Commits:

</text>

<text
    x="{LEFT_X + 315}"
    y="{TOP_Y + 130}"
    font-family="monospace"
    font-size="17"
    font-weight="700"
    fill="{CYAN}">

    {total_commits}

</text>


<text
    x="{LEFT_X + 30}"
    y="{TOP_Y + 170}"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="{TEXT}">

    ⇅  Total PRs:

</text>

<text
    x="{LEFT_X + 315}"
    y="{TOP_Y + 170}"
    font-family="monospace"
    font-size="17"
    font-weight="700"
    fill="{CYAN}">

    {total_prs}

</text>


<text
    x="{LEFT_X + 30}"
    y="{TOP_Y + 210}"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="{TEXT}">

    ⚙  Total Issues:

</text>

<text
    x="{LEFT_X + 315}"
    y="{TOP_Y + 210}"
    font-family="monospace"
    font-size="17"
    font-weight="700"
    fill="{CYAN}">

    {total_issues}

</text>


<text
    x="{LEFT_X + 30}"
    y="{TOP_Y + 250}"
    font-family="Arial, sans-serif"
    font-size="16"
    fill="{TEXT}">

    ◈  Contributed to:

</text>

<text
    x="{LEFT_X + 315}"
    y="{TOP_Y + 250}"
    font-family="monospace"
    font-size="17"
    font-weight="700"
    fill="{CYAN}">

    {contributed_repositories}

</text>


<!-- Activity ring -->

<circle
    cx="{LEFT_X + 440}"
    cy="{TOP_Y + 175}"
    r="55"
    fill="none"
    stroke="#24243A"
    stroke-width="9"/>

<circle
    cx="{LEFT_X + 440}"
    cy="{TOP_Y + 175}"
    r="55"
    fill="none"
    stroke="{PINK}"
    stroke-width="9"
    stroke-linecap="round"
    stroke-dasharray="250 100"
    transform="rotate(-90 {LEFT_X + 440} {TOP_Y + 175})"
    filter="url(#glow)"/>


<text
    x="{LEFT_X + 440}"
    y="{TOP_Y + 170}"
    text-anchor="middle"
    font-family="Arial, sans-serif"
    font-size="25"
    font-weight="700"
    fill="{WHITE}">

    {activity_score}

</text>


<text
    x="{LEFT_X + 440}"
    y="{TOP_Y + 195}"
    text-anchor="middle"
    font-family="monospace"
    font-size="10"
    fill="{MUTED}">

    ACTIVITY

</text>


<!-- ================================================= -->
<!-- RIGHT CARD -->
<!-- ================================================= -->

<rect
    x="{RIGHT_X}"
    y="{TOP_Y}"
    width="{CARD_WIDTH}"
    height="{CARD_HEIGHT}"
    rx="12"
    fill="{CARD}"
    stroke="url(#borderGradient)"
    stroke-width="2"/>


<text
    x="{RIGHT_X + 25}"
    y="{TOP_Y + 45}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="21"
    font-weight="700"
    fill="url(#titleGradient)">

    Most Used Languages

</text>
'''
)


# =========================================================
# Language bars
# =========================================================

bar_x = RIGHT_X + 25
bar_y = TOP_Y + 78

bar_width = 500
bar_height = 10

current_x = bar_x


for language, percentage, color in language_data:

    segment_width = (
        bar_width
        * percentage
        / 100
    )

    svg.append(
        f'''
        <rect
            x="{current_x:.2f}"
            y="{bar_y}"
            width="{segment_width:.2f}"
            height="{bar_height}"
            fill="{color}"/>
        '''
    )

    current_x += segment_width


# =========================================================
# Language labels
# =========================================================

label_start_y = TOP_Y + 125

for index, (
    language,
    percentage,
    color
) in enumerate(language_data):

    column = index % 2

    row = index // 2

    x = RIGHT_X + 25 + column * 245

    y = label_start_y + row * 43

    svg.append(
        f'''
        <circle
            cx="{x + 5}"
            cy="{y - 5}"
            r="5"
            fill="{color}"/>

        <text
            x="{x + 18}"
            y="{y}"
            font-family="Arial, sans-serif"
            font-size="14"
            fill="{TEXT}">

            {escape(language)}

        </text>

        <text
            x="{x + 180}"
            y="{y}"
            text-anchor="end"
            font-family="monospace"
            font-size="13"
            font-weight="700"
            fill="{WHITE}">

            {percentage:.2f}%

        </text>
        '''
    )


# =========================================================
# Bottom contribution info
# =========================================================

svg.append(
    f'''
    <text
        x="{RIGHT_X + 25}"
        y="{TOP_Y + 315}"
        font-family="monospace"
        font-size="12"
        fill="{MUTED}">

        {total_contributions} contributions • {total_reviews} PR reviews

    </text>

    <text
        x="{WIDTH - 25}"
        y="{HEIGHT - 10}"
        text-anchor="end"
        font-family="monospace"
        font-size="10"
        fill="{MUTED}">

        github.com/{USERNAME}

    </text>

</svg>
'''
)


# =========================================================
# Save
# =========================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write("\n".join(svg))


print(
    f"Generated {OUTPUT_FILE}"
)

print(
    f"Stars: {total_stars}"
)

print(
    f"Commits: {total_commits}"
)

print(
    f"PRs: {total_prs}"
)

print(
    f"Issues: {total_issues}"
)

print(
    f"Contributed repositories: "
    f"{contributed_repositories}"
)

print(
    f"Languages: {language_data}"
)
