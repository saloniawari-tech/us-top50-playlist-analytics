import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="US Top 50 Playlist Analytics",
    page_icon="🎵",
    layout="wide"
)

# --------------------------------------------------
# Load cleaned dataset
# --------------------------------------------------

DATA_PATH = "data/processed/us_top50_clean.csv"

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])

# Derived columns
df["duration_minutes"] = df["duration_ms"] / 60000

df["rank_group"] = pd.cut(
    df["position"],
    bins=[0, 10, 20, 50],
    labels=["Top 10", "Top 20", "Top 50"]
)

# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("🎵 United States Top 50 Playlist Analytics")

st.markdown(
    """
    **Historical analysis of playlist performance, song popularity,
    artist visibility, and content attributes.**
    """
)

st.caption(
    f"Dataset: {len(df):,} records | "
    f"{df['date'].min().date()} to {df['date'].max().date()}"
)
# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------

st.sidebar.header("🎛️ Filters")

# Date range
min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Artist filter
artists = sorted(df["artist"].unique())

selected_artists = st.sidebar.multiselect(
    "Artist",
    options=artists,
    default=[]
)

# Song filter
songs = sorted(df["song"].unique())

selected_songs = st.sidebar.multiselect(
    "Song",
    options=songs,
    default=[]
)

# Rank range
rank_range = st.sidebar.slider(
    "Rank range",
    min_value=1,
    max_value=50,
    value=(1, 50)
)

# Album type
album_types = sorted(df["album_type"].unique())

selected_album_types = st.sidebar.multiselect(
    "Album type",
    options=album_types,
    default=album_types
)
# --------------------------------------------------
# Apply Filters
# --------------------------------------------------

filtered_df = df.copy()

# Date filter
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["date"].dt.date >= date_range[0]) &
        (filtered_df["date"].dt.date <= date_range[1])
    ]

# Artist filter
if selected_artists:
    filtered_df = filtered_df[
        filtered_df["artist"].isin(selected_artists)
    ]

# Song filter
if selected_songs:
    filtered_df = filtered_df[
        filtered_df["song"].isin(selected_songs)
    ]

# Rank filter
filtered_df = filtered_df[
    (filtered_df["position"] >= rank_range[0]) &
    (filtered_df["position"] <= rank_range[1])
]

# Album type filter
filtered_df = filtered_df[
    filtered_df["album_type"].isin(selected_album_types)
]
# Show filtered record count

st.info(
    f"Showing {len(filtered_df):,} of {len(df):,} records"
)
# --------------------------------------------------
# Executive Overview
# --------------------------------------------------

st.header("📊 Executive Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Songs",
        filtered_df["song"].nunique()
    )

with col2:
    st.metric(
        "Artists",
        filtered_df["artist"].nunique()
    )

with col3:
    st.metric(
        "Average Popularity",
        f"{filtered_df['popularity'].mean():.2f}"
    )

with col4:
    st.metric(
        "Average Chart Position",
        f"{filtered_df['position'].mean():.2f}"
    )
    # Dataset overview table

st.subheader("Dataset Overview")

overview = pd.DataFrame({
    "Metric": [
        "Records",
        "Unique Songs",
        "Unique Artists",
        "Average Popularity",
        "Average Chart Position"
    ],
    "Value": [
        len(filtered_df),
        filtered_df["song"].nunique(),
        filtered_df["artist"].nunique(),
        round(filtered_df["popularity"].mean(), 2),
        round(filtered_df["position"].mean(), 2)
    ]
})

st.dataframe(overview, use_container_width=True)
# --------------------------------------------------
# Playlist Timeline Explorer
# --------------------------------------------------

st.header("📈 Playlist Timeline Explorer")

daily_chart = (
    filtered_df.groupby("date")
    .agg(
        average_position=("position", "mean"),
        average_popularity=("popularity", "mean")
    )
    .reset_index()
)

fig = px.line(
    daily_chart,
    x="date",
    y=["average_position", "average_popularity"],
    title="Daily Average Chart Position and Popularity",
    labels={
        "value": "Score",
        "date": "Date",
        "variable": "Metric"
    }
)

st.plotly_chart(fig, use_container_width=True)
# Daily popularity trend

popularity_trend = (
    filtered_df.groupby("date")["popularity"]
    .mean()
    .reset_index()
)

fig_popularity = px.line(
    popularity_trend,
    x="date",
    y="popularity",
    title="Daily Popularity Trend",
    labels={
        "popularity": "Average Popularity",
        "date": "Date"
    }
)

st.plotly_chart(fig_popularity, use_container_width=True)
# --------------------------------------------------
# Song Ranking Trend
# --------------------------------------------------

st.header("🎵 Song Ranking Trend")

available_songs = sorted(filtered_df["song"].unique())

if available_songs:
    selected_song = st.selectbox(
        "Select a song",
        available_songs
    )

    song_trend = filtered_df[
        filtered_df["song"] == selected_song
    ].sort_values("date")

    fig_song = px.line(
        song_trend,
        x="date",
        y="position",
        title=f"Ranking Trend — {selected_song}",
        markers=True,
        labels={
            "date": "Date",
            "position": "Playlist Position"
        }
    )

    # Rank 1 should appear at the top
    fig_song.update_yaxes(autorange="reversed")

    st.plotly_chart(
        fig_song,
        use_container_width=True
    )
else:
    st.warning("No songs match the selected filters.")

# --------------------------------------------------
# Artist Dominance Leaderboard
# --------------------------------------------------

st.header("👑 Artist Dominance Leaderboard")

artist_leaderboard = (
    filtered_df.groupby("artist")
    .agg(
        playlist_appearances=("song", "count"),
        unique_songs=("song", "nunique"),
        total_chart_days=("date", "nunique"),
        average_position=("position", "mean"),
        average_popularity=("popularity", "mean")
    )
    .reset_index()
)

artist_leaderboard = artist_leaderboard.sort_values(
    "playlist_appearances",
    ascending=False
)

st.dataframe(
    artist_leaderboard.head(15),
    use_container_width=True
)
# Top artists by playlist appearances

top_artists = artist_leaderboard.head(10).sort_values(
    "playlist_appearances"
)

fig_artist = px.bar(
    top_artists,
    x="playlist_appearances",
    y="artist",
    orientation="h",
    title="Top 10 Artists by Playlist Appearances",
    labels={
        "playlist_appearances": "Playlist Appearances",
        "artist": "Artist"
    }
)

st.plotly_chart(
    fig_artist,
    use_container_width=True
)
# --------------------------------------------------
# Popularity vs Rank
# --------------------------------------------------

st.header("⭐ Popularity vs Playlist Rank")

fig_scatter = px.scatter(
    filtered_df,
    x="position",
    y="popularity",
    hover_data=["song", "artist"],
    opacity=0.5,
    title="Popularity vs Playlist Position",
    labels={
        "position": "Playlist Position",
        "popularity": "Popularity Score"
    }
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)
rank_popularity_corr = filtered_df["position"].corr(
    filtered_df["popularity"],
    method="spearman"
)

st.metric(
    "Spearman Rank–Popularity Correlation",
    f"{rank_popularity_corr:.3f}"
)
# --------------------------------------------------
# Explicit vs Non-Explicit Performance
# --------------------------------------------------

st.header("🔞 Explicit vs Non-Explicit Performance")

explicit_performance = (
    filtered_df.groupby("is_explicit")
    .agg(
        track_observations=("song", "count"),
        unique_songs=("song", "nunique"),
        average_position=("position", "mean"),
        average_popularity=("popularity", "mean")
    )
    .reset_index()
)

explicit_performance["content_type"] = explicit_performance[
    "is_explicit"
].map({
    True: "Explicit",
    False: "Non-Explicit"
})

st.dataframe(
    explicit_performance[
        [
            "content_type",
            "track_observations",
            "unique_songs",
            "average_position",
            "average_popularity"
        ]
    ],
    use_container_width=True
)
# Average popularity by content type

fig_explicit = px.bar(
    explicit_performance,
    x="content_type",
    y="average_popularity",
    title="Average Popularity: Explicit vs Non-Explicit",
    labels={
        "content_type": "Content Type",
        "average_popularity": "Average Popularity"
    }
)

st.plotly_chart(
    fig_explicit,
    use_container_width=True
)
# --------------------------------------------------
# Release Format Performance
# --------------------------------------------------

st.header("💿 Release Format Performance")

release_performance = (
    filtered_df.groupby("album_type")
    .agg(
        track_observations=("song", "count"),
        unique_songs=("song", "nunique"),
        average_position=("position", "mean"),
        average_popularity=("popularity", "mean"),
        average_duration_minutes=("duration_minutes", "mean")
    )
    .reset_index()
)

st.dataframe(
    release_performance,
    use_container_width=True
)
# Average popularity by release format

fig_release = px.bar(
    release_performance,
    x="album_type",
    y="average_popularity",
    title="Average Popularity by Release Format",
    labels={
        "album_type": "Release Format",
        "average_popularity": "Average Popularity"
    }
)

st.plotly_chart(
    fig_release,
    use_container_width=True
)
# --------------------------------------------------
# Song Duration Analysis
# --------------------------------------------------

st.header("⏱️ Song Duration Analysis")

duration_summary = (
    filtered_df.groupby("rank_group")
    .agg(
        average_duration_minutes=("duration_minutes", "mean"),
        median_duration_minutes=("duration_minutes", "median"),
        average_popularity=("popularity", "mean")
    )
    .reset_index()
)

st.dataframe(
    duration_summary,
    use_container_width=True
)
fig_duration = px.scatter(
    filtered_df,
    x="duration_minutes",
    y="popularity",
    hover_data=["song", "artist"],
    opacity=0.5,
    title="Song Duration vs Popularity",
    labels={
        "duration_minutes": "Duration (minutes)",
        "popularity": "Popularity Score"
    }
)

st.plotly_chart(
    fig_duration,
    use_container_width=True
)
# --------------------------------------------------
# Album Size vs Song Success
# --------------------------------------------------

st.header("💿 Album Size vs Song Success")

album_size_data = (
    filtered_df.groupby("total_tracks")
    .agg(
        average_popularity=("popularity", "mean"),
        average_position=("position", "mean"),
        song_observations=("song", "count")
    )
    .reset_index()
)

st.dataframe(
    album_size_data,
    use_container_width=True
)
fig_album_size = px.scatter(
    album_size_data,
    x="total_tracks",
    y="average_popularity",
    size="song_observations",
    hover_data=["average_position"],
    title="Album Size vs Average Song Popularity",
    labels={
        "total_tracks": "Total Tracks in Album",
        "average_popularity": "Average Popularity"
    }
)

st.plotly_chart(
    fig_album_size,
    use_container_width=True
)
# --------------------------------------------------
# Methodology
# --------------------------------------------------

st.header("📋 Methodology")

st.markdown("""
### Data Coverage
The dashboard analyzes historical United States Top 50 playlist
snapshots from May 2024 to November 2025.

### Key Metrics
- **Chart Position:** Daily playlist rank from 1 to 50.
- **Popularity:** Popularity score associated with each track.
- **Chart Days:** Number of days a song appears in the playlist.
- **Average Rank:** Mean playlist position across observations.
- **Artist Presence:** Number of playlist appearances and unique songs.
- **Duration:** Track length converted from milliseconds to minutes.

### Analysis Focus
The dashboard focuses on historical playlist performance,
song popularity, artist visibility, ranking behavior, and
content attributes. It does not perform prediction or
recommendation.
""")