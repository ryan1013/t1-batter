import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

def detect_mobile():
    try:
        user_agent = st.context.headers["user-agent"]
        mobile_keywords = ["Mobile", "Android", "iPhone", "iPad"]
        return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        return False

is_mobile = detect_mobile()

st.set_page_config(layout="wide", initial_sidebar_state="auto")

if is_mobile:
    st.markdown("""
    <style>
    .mobile-filters-label {
        margin-top: -50px;   /* pulls it up under header */
        margin-left: 0px;   /* aligns after chevron */
        font-weight: 600;
        font-size: 16px;
    }
    </style>

    <div class="mobile-filters-label">
        Filters
    </div>
    """, unsafe_allow_html=True)

st.title("One-Day Cup Batting Dashboard")

def apply_responsive_legend(fig):
    if is_mobile:
        fig.update_layout(
            legend=dict(
                orientation="h",
                y=-0.20,
                x=0.5,
                xanchor="center"
            ),
            margin=dict(l=0, r=0, t=10, b=80)
        )
    else:
        fig.update_layout(
            legend=dict(
                orientation="h",
                y=1.05,
                x=0.5,
                xanchor="center"
            ),
            margin=dict(l=0, r=0, t=40, b=20)
        )

# ---------------- LOAD DATA ---------------- #

@st.cache_data
def load_data():
    df = pd.read_csv("MB50_T1.csv", low_memory=False)

    # Ensure Date is parsed properly
    df['Date'] = pd.to_datetime(
        df['Date'],
        format='%d/%m/%Y',
        errors='coerce'
    )

    # Create Year column safely
    df['Year'] = df['Date'].dt.year

    bowling_type_mapping = {
        'LLB': 'Spin', 'LOB': 'Spin', 'RLB': 'Spin', 'ROB': 'Spin',
        'LF': 'Pace', 'LFM': 'Pace', 'LM': 'Pace',
        'RF': 'Pace', 'RFM': 'Pace', 'RM': 'Pace'
    }

    df['Bowling Type'] = df['Bowler Type'].map(bowling_type_mapping)

    def categorize_over(over):
        if 1 <= over <= 10:
            return 'Powerplay (1-10)'
        elif 11 <= over <= 25:
            return 'Upper Middle (11-25)'
        elif 26 <= over <= 40:
            return 'Lower Middle (26-40)'
        elif 41 <= over <= 50:
            return 'Death (41-50)'
        else:
            return None

    df['Phase'] = df['Over'].apply(categorize_over)

    return df

data = load_data()

# ---------------- VIDEO LINKS ---------------- #

video_links = {
    "KS Castle": {
        "dismissal": "https://vid.ecb.nvplay.net/video-highlights/2026/VPM_260410_PLAYLIST_1080_1_2_3.mp4"
    },
    "R King": {
        "dismissal": "https://vid.ecb.nvplay.net/video-highlights/2026/VPM_260410_PLAYLIST_1080.mp4",
        "boundary": "https://vid.ecb.nvplay.net/video-highlights/2026/VPM_260410_PLAYLIST_1080_1_2.mp4"
    }
}

# ---------------- SIDEBAR FILTERS ---------------- #

st.sidebar.header("Filters")

# ---------------- TEAM SELECTION (MULTI) ---------------- #

teams = sorted(data['Batting Team'].dropna().unique())

default_team = "Kent Women" if "Kent Women" in teams else teams[0]

selected_teams = st.sidebar.multiselect(
    "Batting Team",
    teams,
    default=[default_team]
)

# ---------------- BATTER SELECTION (DEPENDENT ON TEAM) ---------------- #

if selected_teams:
    team_filtered_data = data[data['Batting Team'].isin(selected_teams)]
else:
    team_filtered_data = data.copy()

# Create display format: "Name (RHB)"
team_filtered_data['Batter Display'] = (
    team_filtered_data['Batter'].astype(str) +
    " (" +
    team_filtered_data['Batting Hand'].astype(str) +
    ")"
)

# Remove duplicates
batter_display_df = team_filtered_data[['Batter', 'Batter Display']].drop_duplicates()

# Sort alphabetically by actual Batter name
batter_display_df = batter_display_df.sort_values('Batter')

team_batters_display = batter_display_df['Batter Display'].tolist()

# Default = first alphabetically
default_selection = [team_batters_display[0]] if team_batters_display else []

selected_batters_display = st.sidebar.multiselect(
    "Batter",
    team_batters_display,
    default=default_selection
)

# Convert display back to actual Batter names
selected_batters = [
    name.split(" (")[0]
    for name in selected_batters_display
]

selected_bowling = st.sidebar.multiselect(
    "Bowling Type",
    ["Spin", "Pace"],
    default=["Spin", "Pace"]
)

selected_runs = st.sidebar.multiselect(
    "Runs to Display in Wagon Wheel",
    [1,2,3,4,5,6],
    default=[1,2,3,4,5,6]
)

# ---------------- BEEHIVE FILTER ---------------- #

st.sidebar.subheader("Beehive Filters")

beehive_options = st.sidebar.multiselect(
    "Show in Beehive",
    ["4 Runs", "6 Runs", "Dismissals"],
    default=["4 Runs", "6 Runs", "Dismissals"]
)

# ---------------- YEAR FILTER ---------------- #

years = sorted(data['Year'].dropna().unique())

selected_years = st.sidebar.multiselect(
    "Year",
    years,
    default=years
)

# ---------------- VENUE FILTER ---------------- #

venues = sorted(data['Venue'].dropna().unique())

selected_venues = st.sidebar.multiselect(
    "Venue",
    venues,
    default=venues
)

# ---------------- APPLY FILTERS ---------------- #

filtered = data.copy()

# Filter by selected teams
if selected_teams:
    filtered = filtered[filtered['Batting Team'].isin(selected_teams)]

# Filter by selected batters
if selected_batters:
    filtered = filtered[filtered['Batter'].isin(selected_batters)]

# Filter by bowling type
if selected_bowling:
    filtered = filtered[filtered['Bowling Type'].isin(selected_bowling)]

# Filter by Year
if selected_years:
    filtered = filtered[filtered['Year'].isin(selected_years)]

# Filter by Venue
if selected_venues:
    filtered = filtered[filtered['Venue'].isin(selected_venues)]

year_filtered_df = data.copy()

if selected_years:
    year_filtered_df = year_filtered_df[year_filtered_df['Year'].isin(selected_years)]

# ---------------- TEAM STATS ---------------- #
st.subheader("Team Stats (1st Innings Phase Averages Irrespective of Venue)")

if len(selected_teams) != 1:

    st.info("Select exactly one Batting Team to view phase averages.")

else:

    import math

    team_name = selected_teams[0]

    team_phase_data = year_filtered_df[
    (year_filtered_df['Batting Team'] == team_name) &
    (year_filtered_df['Innings'] == 1)].copy()

    team_innings_count = team_phase_data[
    team_phase_data['Innings'] == 1].groupby(['Match', 'Date', 'Innings']).ngroups

    if len(team_phase_data) > 0:

        if 'Extra Runs' not in team_phase_data.columns:
            team_phase_data['Extra Runs'] = 0

        team_phase_data['Total Runs'] = (
            team_phase_data['Runs'].fillna(0) +
            team_phase_data['Extra Runs'].fillna(0)
        )

        phases = [
            'Powerplay (1-10)',
            'Upper Middle (11-25)',
            'Lower Middle (26-40)',
            'Death (41-50)'
        ]

        phase_data_store = []

        st.caption(f"Sample Size: {team_innings_count} innings")

        # ---------- FIRST PASS: RAW AVERAGES ---------- #

        for phase in phases:

            phase_df = team_phase_data[
                team_phase_data['Phase'] == phase
            ]

            if len(phase_df) == 0:
                continue

            grouped = phase_df.groupby(['Match', 'Date', 'Innings'])

            match_totals = []
            match_wickets = []

            for _, group in grouped:

                total_runs = group['Total Runs'].sum()

                dismissals = group[
                    group['Dismissed Batter'].notna() &
                    (group['Dismissed Batter'].astype(str).str.strip() != "")
                ].shape[0]

                match_totals.append(total_runs)
                match_wickets.append(dismissals)

            raw_avg_runs = sum(match_totals) / len(match_totals)
            raw_avg_wkts = sum(match_wickets) / len(match_wickets)

            phase_data_store.append({
                "phase": phase,
                "raw_runs": raw_avg_runs,
                "raw_wkts": raw_avg_wkts
            })

        # ---------- COUNT .5 OCCURRENCES ---------- #

        half_phases = [
            p for p in phase_data_store
            if p["raw_wkts"] % 1 == 0.5
        ]

        half_count = len(half_phases)
        half_seen = 0

        # ---------- ROUNDING PASS ---------- #

        for p in phase_data_store:

            raw_avg_runs = p["raw_runs"]
            raw_avg_wkts = p["raw_wkts"]

            # Runs normal rounding
            p["rounded_runs"] = round(raw_avg_runs)

            # Wickets special .5 logic
            if raw_avg_wkts % 1 == 0.5:

                half_seen += 1

                if half_count == 4:
                    if half_seen <= 2:
                        avg_wkts = math.floor(raw_avg_wkts)
                    else:
                        avg_wkts = math.ceil(raw_avg_wkts)
                elif half_count == 2:
                    if half_seen == 1:
                        avg_wkts = math.floor(raw_avg_wkts)
                    else:
                        avg_wkts = math.ceil(raw_avg_wkts)
                else:
                    avg_wkts = round(raw_avg_wkts)

            else:
                avg_wkts = round(raw_avg_wkts)

            p["rounded_wkts"] = avg_wkts
            p["rounding_error"] = avg_wkts - raw_avg_wkts

        # ---------- ENFORCE TOTAL ≤ 10 USING ROUNDING ERROR ---------- #

        total_wkts_sum = sum(p["rounded_wkts"] for p in phase_data_store)

        while total_wkts_sum > 10:

            # Select phase with largest positive rounding error
            candidates = [
                p for p in phase_data_store
                if p["rounded_wkts"] > 0
            ]

            if not candidates:
                break

            worst_phase = max(
                candidates,
                key=lambda x: x["rounding_error"]
            )

            worst_phase["rounded_wkts"] -= 1
            worst_phase["rounding_error"] -= 1
            total_wkts_sum -= 1

        # ---------- TOTAL RUNS ---------- #

        total_runs_sum = sum(p["rounded_runs"] for p in phase_data_store)

        # ---------- DISPLAY ---------- #

        phase_results = {}

        for p in phase_data_store:
            phase_results[p["phase"]] = f"{p['rounded_runs']}-{p['rounded_wkts']}"

        phase_results["Total"] = f"{total_runs_sum}-{total_wkts_sum}"

        cols = st.columns(len(phase_results))

        for i, (phase, value) in enumerate(phase_results.items()):
            cols[i].metric(phase, value)

    else:
        st.write("No first innings data available for selected team.")

# ---------------- VENUE STATS ---------------- #

st.subheader("Venue Stats (1st Innings Phase Averages)")

if len(selected_venues) != 1:

    st.info("Select exactly one Venue to view phase averages.")

else:

    import math

    venue_name = selected_venues[0]

    venue_phase_data = year_filtered_df[
    (year_filtered_df['Venue'] == venue_name) &
    (year_filtered_df['Innings'] == 1)].copy()

    venue_innings_count = venue_phase_data[
    venue_phase_data['Innings'] == 1].groupby(['Match', 'Date', 'Innings']).ngroups

    st.caption(f"Sample Size: {venue_innings_count} innings")

    if len(venue_phase_data) > 0:

        if 'Extra Runs' not in venue_phase_data.columns:
            venue_phase_data['Extra Runs'] = 0

        venue_phase_data['Total Runs'] = (
            venue_phase_data['Runs'].fillna(0) +
            venue_phase_data['Extra Runs'].fillna(0)
        )

        phases = [
            'Powerplay (1-10)',
            'Upper Middle (11-25)',
            'Lower Middle (26-40)',
            'Death (41-50)'
        ]

        phase_data_store = []

        # ---------- RAW AVERAGES ---------- #

        for phase in phases:

            phase_df = venue_phase_data[
                venue_phase_data['Phase'] == phase
            ]

            if len(phase_df) == 0:
                continue

            grouped = phase_df.groupby(['Match', 'Date', 'Innings'])

            match_totals = []
            match_wickets = []

            for _, group in grouped:

                total_runs = group['Total Runs'].sum()

                dismissals = group[
                    group['Dismissed Batter'].notna() &
                    (group['Dismissed Batter'].astype(str).str.strip() != "")
                ].shape[0]

                match_totals.append(total_runs)
                match_wickets.append(dismissals)

            raw_avg_runs = sum(match_totals) / len(match_totals)
            raw_avg_wkts = sum(match_wickets) / len(match_wickets)

            phase_data_store.append({
                "phase": phase,
                "raw_runs": raw_avg_runs,
                "raw_wkts": raw_avg_wkts
            })

        # ---------- COUNT .5 OCCURRENCES ---------- #

        half_phases = [
            p for p in phase_data_store
            if p["raw_wkts"] % 1 == 0.5
        ]

        half_count = len(half_phases)
        half_seen = 0

        # ---------- ROUNDING PASS ---------- #

        for p in phase_data_store:

            raw_avg_runs = p["raw_runs"]
            raw_avg_wkts = p["raw_wkts"]

            p["rounded_runs"] = round(raw_avg_runs)

            if raw_avg_wkts % 1 == 0.5:

                half_seen += 1

                if half_count == 4:
                    if half_seen <= 2:
                        avg_wkts = math.floor(raw_avg_wkts)
                    else:
                        avg_wkts = math.ceil(raw_avg_wkts)
                elif half_count == 2:
                    if half_seen == 1:
                        avg_wkts = math.floor(raw_avg_wkts)
                    else:
                        avg_wkts = math.ceil(raw_avg_wkts)
                else:
                    avg_wkts = round(raw_avg_wkts)

            else:
                avg_wkts = round(raw_avg_wkts)

            p["rounded_wkts"] = avg_wkts
            p["rounding_error"] = avg_wkts - raw_avg_wkts

        # ---------- ENFORCE TOTAL ≤ 10 ---------- #

        total_wkts_sum = sum(p["rounded_wkts"] for p in phase_data_store)

        while total_wkts_sum > 10:

            candidates = [
                p for p in phase_data_store
                if p["rounded_wkts"] > 0
            ]

            if not candidates:
                break

            worst_phase = max(
                candidates,
                key=lambda x: x["rounding_error"]
            )

            worst_phase["rounded_wkts"] -= 1
            worst_phase["rounding_error"] -= 1
            total_wkts_sum -= 1

        # ---------- TOTAL RUNS ---------- #

        total_runs_sum = sum(p["rounded_runs"] for p in phase_data_store)

        # ---------- DISPLAY ---------- #

        phase_results = {}

        for p in phase_data_store:
            phase_results[p["phase"]] = f"{p['rounded_runs']}-{p['rounded_wkts']}"

        phase_results["Total"] = f"{total_runs_sum}-{total_wkts_sum}"

        cols = st.columns(len(phase_results))

        for i, (phase, value) in enumerate(phase_results.items()):
            cols[i].metric(phase, value)

    else:
        st.write("No first innings data available for selected venue.")

# ---------------- KPI SECTION ---------------- #

st.subheader("Batter Stats")

batter_innings_count = filtered[
    filtered['Batter'].isin(selected_batters)
].groupby(['Match', 'Date', 'Innings']).ngroups

st.caption(f"Sample Size: {batter_innings_count} innings")

total_runs = filtered['Runs'].sum()

# Balls faced (exclude wides only)
balls_faced = filtered[
    ~filtered['Extra'].astype(str).str.contains("Wide", case=False, na=False)
].shape[0]

if len(selected_batters) == 1:
    # Batter-specific dismissal count
    dismissals_count = filtered[
        filtered['Dismissed Batter'].astype(str).str.strip() ==
        selected_batters[0].strip()
    ].shape[0]
else:
    # Team / multi-batter dismissal count
    dismissals_count = filtered[
        filtered['Dismissed Batter'].notna() &
        (filtered['Dismissed Batter'].astype(str).str.strip() != "")
    ].shape[0]

if dismissals_count > 0:
    batting_average = round(total_runs / dismissals_count, 2)
else:
    batting_average = "∞"

if balls_faced > 0:
    strike_rate = round((total_runs / balls_faced) * 100, 2)
else:
    strike_rate = 0

boundary_runs = filtered[filtered['Runs'].isin([4,6])]['Runs'].sum()

if total_runs > 0:
    boundary_percentage = round((boundary_runs / total_runs) * 100, 2)
else:
    boundary_percentage = 0

# Scoring Shot %
scoring_shots = filtered[
    (~filtered['Extra'].astype(str).str.contains("Wide", case=False, na=False)) &
    (filtered['Runs'] > 0)
].shape[0]

if balls_faced > 0:
    scoring_shot_percentage = round((scoring_shots / balls_faced) * 100, 2)
else:
    scoring_shot_percentage = 0

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

col1.metric("Runs", total_runs)
col2.metric("Balls Faced", balls_faced)
col3.metric("Dismissals", dismissals_count)
col4.metric("Average", batting_average)
col5.metric("Strike Rate", strike_rate)
col6.metric("Scoring Shot %", scoring_shot_percentage)
col7.metric("Boundary Runs %", boundary_percentage)

# ---------------- FEET MOVEMENT ---------------- #

st.subheader("Feet Movement (% of Runs)")

if len(filtered) > 0:

    feet_df = filtered.copy()

    # Only consider scoring shots
    feet_df = feet_df[feet_df['Runs'] > 0].copy()

    # Clean and prioritise Feet values
    def clean_feet(value):

        value = str(value).strip().lower()

        # PRIORITY 1
        if "down the track" in value:
            return "Down the Track"

        # PRIORITY 2
        if "backs away" in value:
            return "Backs Away"

        # Exact recognised categories
        if value == "no movement":
            return "No Movement"

        if value == "front foot":
            return "Front Foot"

        if value == "back foot":
            return "Back Foot"

        # Everything else
        return "Other"

    feet_df['Feet Category'] = feet_df['Feet'].apply(clean_feet)

    # Aggregate runs
    runs_by_feet = feet_df.groupby('Feet Category')['Runs'].sum()

    total_runs_feet = runs_by_feet.sum()

    categories = [
        "No Movement",
        "Front Foot",
        "Back Foot",
        "Down the Track",
        "Backs Away",
        "Other"
    ]

    if total_runs_feet > 0:

        cols = st.columns(len(categories))

        for i, cat in enumerate(categories):

            run_value = runs_by_feet.get(cat, 0)
            percentage = round((run_value / total_runs_feet) * 100, 1)

            cols[i].metric(cat, f"{percentage}%")

    else:
        st.write("No scoring data available.")

else:
    st.write("No data available.")

# ---------------- FANCY SHOT ---------------- #

st.subheader("Shots")

if len(filtered) > 0:

    shot_df = filtered.copy()

    # Only scoring shots
    shot_df = shot_df[shot_df['Runs'] > 0].copy()

    # Drop NaN shots
    shot_df = shot_df.dropna(subset=['Shot']).copy()

    shot_df['Shot'] = shot_df['Shot'].astype(str).str.strip().str.lower()

    def classify_shot(value):

        # Priority order matters
        if "reverse sweep" in value:
            return "Reverse Sweep"

        if "slog sweep" in value:
            return "Slog Sweep"

        if "scoop" in value:
            return "Scoop"

        # Plain sweep (but not slog/reverse which are already captured)
        if "sweep" in value:
            return "Sweep"

        if "hook" in value:
            return "Hook"

        return None

    shot_df['Fancy Shot Category'] = shot_df['Shot'].apply(classify_shot)

    fancy_runs = shot_df.dropna(subset=['Fancy Shot Category']) \
                        .groupby('Fancy Shot Category')['Runs'] \
                        .sum()

    total_runs = shot_df['Runs'].sum()

    categories = [
        "Scoop",
        "Sweep",
        "Slog Sweep",
        "Reverse Sweep",
        "Hook"
    ]

    cols = st.columns(len(categories))

    for i, shot in enumerate(categories):

        run_value = fancy_runs.get(shot, 0)

        if total_runs > 0:
            percentage = round((run_value / total_runs) * 100, 1)
        else:
            percentage = 0

        if percentage > 2:
            display_text = f"✅"
        else:
            display_text = f"❌"

        cols[i].metric(shot, f"{display_text}")

else:
    st.write("No data available.")

# ---------------- WAGON WHEEL ---------------- #

st.subheader("Wagon Wheel")

wagon = filtered[
    (filtered['Runs'].isin(selected_runs)) &
    (filtered['Runs'] > 0) &
    filtered['FieldX'].notna() &
    filtered['FieldY'].notna()
]

if len(wagon) > 0:

    center_x = 175
    center_y = 175

    run_colors = {
        1: "#00FFFF",
        2: "#0057FF",
        3: "#FF00FF",
        4: "#00C800",
        5: "#FFA500",
        6: "#FF0000"
    }

    fig = go.Figure()

    try:
        img = Image.open("wagon_background.png")
        field_scale = 1
        fig.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=-180 * field_scale,
                y=180 * field_scale,
                sizex=360 * field_scale,
                sizey=360 * field_scale,
                sizing="stretch",
                layer="below"
            )
        )
    except:
        pass

    for _, row in wagon.iterrows():

        x = row['FieldX'] - center_x
        y = center_y - row['FieldY']
        run_val = row['Runs']
        color = run_colors.get(run_val, "grey")

        origin_offset = 25  # positive = move upwards

        fig.add_trace(go.Scatter(
            x=[0, x],
            y=[origin_offset, y + origin_offset],
            mode="lines",
            line=dict(color=color, width=4),
            showlegend=False
        ))

    for r, c in run_colors.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color=c, width=4),
            name=f"{r} Run"
        ))

    fig.update_layout(
        xaxis=dict(range=[-180,180], visible=False),
        yaxis=dict(range=[-180,180], visible=False),
        height=750,
        legend=dict(
            orientation="h",
            y=1.05,
            x=0.5,
            xanchor="center"
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    fig.update_yaxes(scaleanchor="x")

    fig.update_layout(dragmode=False)

    apply_responsive_legend(fig)

    st.plotly_chart(
    fig,
    use_container_width=True,
    key="wagon_wheel",
    config={
        "scrollZoom": False,
        "doubleClick": "reset",
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "select2d",
            "lasso2d"
        ]
    }
)

else:
    st.write("No scoring shots available.")

# ---------------- DISMISSAL PIE ---------------- #

st.subheader("Dismissal Breakdown")

dismissals = filtered[
    filtered['Dismissed Batter'].isin(selected_batters)
]

if len(dismissals) > 0:

    counts = dismissals['Wicket'].value_counts()

    fig_pie = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        textinfo="label+value",
        textposition="inside",
        hole=0.35,
        textfont=dict(size=22, family="Arial Black", color="black")
    ))

    fig_pie.update_layout(
        height=550,
        legend=dict(
            orientation="v",
            y=0.5,
            yanchor="middle",
            x=1.02
        ),
        margin=dict(l=20, r=150, t=20, b=20)
    )

    fig_pie.update_layout(dragmode=False)

    apply_responsive_legend(fig_pie)

    st.plotly_chart(
    fig_pie,
    use_container_width=True,
    key="dismissal_pie",
    config={
        "scrollZoom": False,
        "doubleClick": "reset",
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "select2d",
            "lasso2d"
        ]
    }
)

else:
    st.write("No dismissals recorded.")

# ---------------- CATCH MAP ---------------- #

st.subheader("Catch Map (Caught Only)")

caught = filtered[
    (filtered['Wicket'] == "Caught") &
    filtered['FieldX'].notna() &
    filtered['FieldY'].notna()
]

if len(caught) > 0:

    fig_catch = go.Figure()

    try:
        img = Image.open("wagon_background.png")
        fig_catch.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=-180,
                y=180,
                sizex=360,
                sizey=360,
                sizing="stretch",
                layer="below"
            )
        )
    except:
        pass

    x_vals = caught['FieldX'] - 175
    y_vals = 175 - caught['FieldY']

    fig_catch.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            symbol="x",
            size=14,
            color="black",
            line=dict(width=2)
        )
    ))

    fig_catch.update_layout(
        xaxis=dict(range=[-180,180], visible=False),
        yaxis=dict(range=[-180,180], visible=False),
        height=700,
        showlegend=False
    )

    fig_catch.update_yaxes(scaleanchor="x")

    fig_catch.update_layout(dragmode=False)

    apply_responsive_legend(fig_catch)

    st.plotly_chart(
    fig_catch,
    use_container_width=True,
    key="catchmap",
    config={
        "scrollZoom": False,
        "doubleClick": "reset",
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "select2d",
            "lasso2d"
        ]
    }
)

else:
    st.write("No caught dismissals.")

# ---------------- BEEHIVE ---------------- #

st.subheader("Beehive")

beehive_data = filtered[
    filtered['Analyst Arrival Line'].notna() &
    filtered['Analyst Arrival Height'].notna()
].copy()

if len(beehive_data) > 0:

    fig = go.Figure()

    img = Image.open("beehive_background.jpg")

    x_min_m = -1.83
    x_max_m = 1.83
    y_min_m = 0
    y_max_m = 2.0

    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=x_min_m,
            y=y_max_m,
            sizex=(x_max_m - x_min_m),
            sizey=(y_max_m - y_min_m),
            sizing="stretch",
            layer="below"
        )
    )

    if "4 Runs" in beehive_options:
        fig.add_trace(go.Scatter(
            x=beehive_data[beehive_data['Runs'] == 4]['Analyst Arrival Line'],
            y=beehive_data[beehive_data['Runs'] == 4]['Analyst Arrival Height'],
            mode="markers",
            marker=dict(size=9, color="green",
                        line=dict(width=1, color="black")),
            name="4 Runs"
        ))

    if "6 Runs" in beehive_options:
        fig.add_trace(go.Scatter(
            x=beehive_data[beehive_data['Runs'] == 6]['Analyst Arrival Line'],
            y=beehive_data[beehive_data['Runs'] == 6]['Analyst Arrival Height'],
            mode="markers",
            marker=dict(size=11, color="red",
                        line=dict(width=1, color="black")),
            name="6 Runs"
        ))

    if "Dismissals" in beehive_options:
        fig.add_trace(go.Scatter(
            x=beehive_data[
                beehive_data['Dismissed Batter'].isin(selected_batters)
            ]['Analyst Arrival Line'],
            y=beehive_data[
                beehive_data['Dismissed Batter'].isin(selected_batters)
            ]['Analyst Arrival Height'],
            mode="markers",
            marker=dict(
                symbol="x",
                size=14,
                color="black",
                line=dict(width=2)
            ),
            name="Dismissal"
        ))

    fig.update_layout(
        height=700,
        xaxis=dict(range=[x_min_m, x_max_m], visible=False),
        yaxis=dict(range=[y_min_m, y_max_m], visible=False),
    )

    fig.update_yaxes(scaleanchor="x")
    fig.update_layout(dragmode=False)

    apply_responsive_legend(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="beehive",
        config={
            "scrollZoom": False,
            "doubleClick": "reset",
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "zoom2d",
                "select2d",
                "lasso2d"
            ]
        }
    )

else:
    st.write("No delivery data available.")

# ---------------- VIDEO SECTION ---------------- #

st.subheader("Videos (Filters not applicable to this section)")

if len(selected_batters) == 1:
    batter_name = selected_batters[0]

    if batter_name in video_links:

        batter_videos = video_links[batter_name]

        if "dismissal" in batter_videos:
            st.markdown("**Dismissal Clips**")
            st.video(batter_videos["dismissal"])

        if "boundary" in batter_videos:
            st.markdown("**Boundary Clips**")
            st.video(batter_videos["boundary"])

    else:
        st.write("No video links available for selected batter.")

else:
    st.write("Select a single batter to view video highlights.")
