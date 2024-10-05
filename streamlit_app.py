import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Set up page layout
st.set_page_config(page_title="HRV Dashboard")


# Load data
def load_data():
    data = pd.read_csv("oura_data.csv")
    data["day"] = pd.to_datetime(data["day"])
    data = data[data["day"] <= datetime.datetime(2023, 2, 28)]

    return data


# Load and cache data
data = load_data()

# User Input for the time period
st.sidebar.header("Select Time Period")
days = st.sidebar.selectbox("Choose number of days", [7, 30, 90])

# Filter data for the selected number of days
filtered_data = data.tail(days)

# HRV Overview Calculations
hrv_data = filtered_data[["day", "nocturnal_hrv"]].reset_index(drop=True)
hrv_data.dropna(inplace=True)

avg_hrv = hrv_data["nocturnal_hrv"].mean()
var_hrv = hrv_data["nocturnal_hrv"].var()
peak_hrv = hrv_data["nocturnal_hrv"].max()
low_hrv = hrv_data["nocturnal_hrv"].min()

peak_hrv_day = hrv_data.loc[hrv_data["nocturnal_hrv"].idxmax()]["day"]
low_hrv_day = hrv_data.loc[hrv_data["nocturnal_hrv"].idxmin()]["day"]

# Percent of Days Above/Below Baseline
baseline = avg_hrv
percent_above_baseline = (hrv_data["nocturnal_hrv"] > baseline).mean() * 100
percent_below_baseline = (hrv_data["nocturnal_hrv"] < baseline).mean() * 100

# Display HRV Overview
st.title(f"HRV Dashboard for {days}-Day Period")
st.header("1. HRV Overview")

# Create a dictionary with the overview data
overview_data = {
    "Metric": [
        "Average HRV",
        "Peak HRV",
        "Lowest HRV",
        "HRV Variability",
        "Percent of Days Above Baseline HRV",
        "Percent of Days Below Baseline HRV",
    ],
    "Value": [
        f"{avg_hrv:.2f} ms",
        f"{peak_hrv:.2f} ms on {peak_hrv_day.date()}",
        f"{low_hrv:.2f} ms on {low_hrv_day.date()}",
        f"{var_hrv:.2f} ms",
        f"{percent_above_baseline:.2f}%",
        f"{percent_below_baseline:.2f}%",
    ],
}

# Convert the dictionary to a DataFrame
overview_df = pd.DataFrame(overview_data)

# Display the table
st.dataframe(overview_df, use_container_width=True, hide_index=True)

# Plot HRV Over Time
fig = go.Figure()
fig.add_trace(go.Scatter(x=hrv_data["day"], y=hrv_data["nocturnal_hrv"], mode="lines+markers", name="HRV"))
fig.add_trace(
    go.Scatter(
        x=hrv_data["day"],
        y=[avg_hrv] * len(hrv_data),
        mode="lines",
        name=f"Average HRV: {avg_hrv:.2f} ms",
        line=dict(dash="dash"),
    )
)
fig.update_layout(title=f"HRV Over the Last {days} Days", xaxis_title="Date", yaxis_title="HRV (ms)")
st.plotly_chart(fig)

# HRV Quartile Analysis
st.header("2. HRV Quartile Analysis")
q75, q25 = np.percentile(hrv_data["nocturnal_hrv"], [75, 25])

top_quartile = hrv_data[hrv_data["nocturnal_hrv"] >= q75]
top_quartile["day"] = pd.to_datetime(top_quartile["day"]).dt.strftime("%Y-%m-%d")

bottom_quartile = hrv_data[hrv_data["nocturnal_hrv"] <= q25]
bottom_quartile["day"] = pd.to_datetime(bottom_quartile["day"]).dt.strftime("%Y-%m-%d")

# Display Quartile Results
left_col, right_col = st.columns(2)

with left_col:
    st.write(f"**Top 25% HRV Days**")
    st.write(f"HRV Range: {q75:.2f} ms and above")
    st.dataframe(top_quartile[["day", "nocturnal_hrv"]], use_container_width=True, hide_index=True)

with right_col:
    st.write(f"**Bottom 25% HRV Days**")
    st.write(f"HRV Range: {q25:.2f} ms and below")
    st.dataframe(bottom_quartile[["day", "nocturnal_hrv"]], use_container_width=True, hide_index=True)

# Plot HRV Quartiles using Box Plot
fig = px.box(hrv_data, y="nocturnal_hrv", points="all")
fig.add_hline(y=q75, line_dash="dash", line_color="green", annotation_text=f"Top 25% HRV: {q75:.2f} ms")
fig.add_hline(y=q25, line_dash="dash", line_color="blue", annotation_text=f"Bottom 25% HRV: {q25:.2f} ms")
fig.update_layout(title=f"HRV Distribution for Last {days} Days", yaxis_title="HRV (ms)", showlegend=False)
st.plotly_chart(fig)

# Weekday vs Weekend Recovery
st.header("3. Weekday vs Weekend Recovery")
hrv_data["day_of_week"] = hrv_data["day"].dt.dayofweek
weekdays = hrv_data[hrv_data["day_of_week"] < 5]
weekends = hrv_data[hrv_data["day_of_week"] >= 5]

# Calculate Top Quartile Percentages
weekdays_top_quartile_percent = (weekdays["nocturnal_hrv"] >= q75).mean() * 100
weekends_top_quartile_percent = (weekends["nocturnal_hrv"] >= q75).mean() * 100

# Create a dictionary with the recovery pattern data
recovery_patterns = {
    "Day Type": ["Weekdays", "Weekends"],
    "Percentage in Top 25% HRV": [f"{weekdays_top_quartile_percent:.2f}%", f"{weekends_top_quartile_percent:.2f}%"],
}

# Convert the dictionary to a DataFrame
recovery_patterns_df = pd.DataFrame(recovery_patterns)

# Display the table
st.dataframe(recovery_patterns_df, use_container_width=True, hide_index=True)

# Plot Weekday vs Weekend HRV
fig = go.Figure(
    data=[
        go.Bar(name="Weekdays", x=["Weekdays"], y=[weekdays_top_quartile_percent]),
        go.Bar(name="Weekends", x=["Weekends"], y=[weekends_top_quartile_percent]),
    ]
)
fig.update_layout(title="HRV in Top 25%: Weekday vs Weekend", yaxis_title="Percentage of Days in Top 25%")
st.plotly_chart(fig)

# Advanced HRV and Heart Rate Metrics
st.header("4. Advanced HRV and Heart Rate Metrics")
# Create a box plot with individual points for heart rate
fig = go.Figure()

# Add box plot
fig.add_trace(
    go.Box(
        y=filtered_data["average_heart_rate"],
        name="Heart Rate Distribution",
        boxpoints="all",
        jitter=0.3,
        pointpos=-1.8,
    )
)

# Update layout
fig.update_layout(
    title=f"Heart Rate Distribution and Metrics for Last {days} Days",
    xaxis_title="Metric",
    yaxis_title="Heart Rate (bpm)",
    showlegend=True,
    boxmode="group",
)

# Show the plot
st.plotly_chart(fig)

mean_hr = filtered_data["average_heart_rate"].mean()
max_hr = filtered_data["average_heart_rate"].max()
min_hr = filtered_data["average_heart_rate"].min()

# Create a dictionary with the heart rate metrics
hr_metrics = {
    "Metric": ["Mean HR", "Max HR", "Min HR"],
    "Value": [f"{mean_hr:.2f} bpm", f"{max_hr:.2f} bpm", f"{min_hr:.2f} bpm"],
}

# Convert the dictionary to a DataFrame
hr_df = pd.DataFrame(hr_metrics)

# Display the table
st.dataframe(hr_df, use_container_width=True, hide_index=True)

# Replace the existing "Monthly Trends" section with this:

st.header("5. Monthly Trends (Last 30 Days)")

# Find the earliest date in filtered_data
earliest_date = filtered_data["day"].min()

# Select 30 days before the earliest date in filtered_data
last_30_days = data[(data["day"] >= earliest_date - pd.Timedelta(days=30)) & (data["day"] < earliest_date)].sort_values(
    "day"
)


monthly_avg_hrv = last_30_days["nocturnal_hrv"].mean()
monthly_var_hrv = last_30_days["nocturnal_hrv"].var()

high_hrv_days = last_30_days.loc[last_30_days["nocturnal_hrv"] > baseline, "day"]
low_hrv_days = last_30_days.loc[last_30_days["nocturnal_hrv"] < baseline, "day"]

# Prepare data for overlaying
last_30_days["day_of_month"] = last_30_days["day"].dt.day
filtered_data["day_of_month"] = filtered_data["day"].dt.day

# Create box plots for HRV comparison between previous 30 days and current period
fig = go.Figure()

# Box plot for previous 30 days
fig.add_trace(
    go.Box(
        y=last_30_days["nocturnal_hrv"],
        name="Previous 30 Days",
        boxpoints="all",
        jitter=0.3,
        pointpos=-1.8,
        marker_color="blue",
    )
)

# Box plot for current period
fig.add_trace(
    go.Box(
        y=filtered_data["nocturnal_hrv"],
        name="Current Period",
        boxpoints="all",
        jitter=0.3,
        pointpos=-1.8,
        marker_color="red",
    )
)

# Update layout
fig.update_layout(title="HRV Comparison: Previous 30 Days vs Current Period", yaxis_title="HRV (ms)", boxmode="group")

# Show the plot
st.plotly_chart(fig)
current_avg_hrv = filtered_data["nocturnal_hrv"].mean()

hrv_difference = current_avg_hrv - monthly_avg_hrv
current_var_hrv = filtered_data["nocturnal_hrv"].var()

# Create a dictionary with the HRV comparison metrics
hrv_comparison = {
    "Metric": [
        "Previous 30-Day Average HRV",
        "Current Period Average HRV",
        "Difference in Average HRV",
        "Previous 30-Day HRV Variability",
        "Current Period HRV Variability",
    ],
    "Value": [
        f"{monthly_avg_hrv:.2f} ms",
        f"{current_avg_hrv:.2f} ms",
        f"{hrv_difference:.2f} ms",
        f"{monthly_var_hrv:.2f} ms",
        f"{current_var_hrv:.2f} ms",
    ],
}

# Convert the dictionary to a DataFrame
hrv_comparison_df = pd.DataFrame(hrv_comparison)

# Display the table
st.dataframe(hrv_comparison_df, use_container_width=True, hide_index=True)

# Create a calendar heatmap for HRV values
fig = px.imshow(
    last_30_days.set_index("day")["nocturnal_hrv"].to_frame().T,
    labels=dict(x="Date", y="", color="HRV"),
    x=last_30_days["day"],
    y=["HRV"],
    color_continuous_scale="RdYlGn",
    title="HRV Calendar Heatmap (Last 30 Days)",
)

fig.update_xaxes(side="top")
fig.update_layout(height=200, yaxis_nticks=1)

st.plotly_chart(fig)

# Low to High HRV Swings
st.header("6. HRV Swings")


biggest_increase = filtered_data["nocturnal_hrv"].diff().max()
biggest_increase_day = filtered_data.loc[filtered_data["nocturnal_hrv"].diff().idxmax()]["day"]

biggest_decrease = filtered_data["nocturnal_hrv"].diff().min()
biggest_decrease_day = filtered_data.loc[filtered_data["nocturnal_hrv"].diff().idxmin()]["day"]

# Calculate daily HRV changes
filtered_data["hrv_change"] = filtered_data["nocturnal_hrv"].diff()

# Create the time series plot
fig = go.Figure()

# Add HRV line
fig.add_trace(
    go.Scatter(
        x=filtered_data["day"],
        y=filtered_data["nocturnal_hrv"],
        mode="lines+markers",
        name="HRV",
        line=dict(color="blue"),
    )
)

# Add HRV change bars
fig.add_trace(
    go.Bar(
        x=filtered_data["day"],
        y=filtered_data["hrv_change"],
        name="HRV Change",
        marker_color=filtered_data["hrv_change"].apply(lambda x: "green" if x > 0 else "red"),
    )
)

# Highlight biggest increase and decrease
fig.add_trace(
    go.Scatter(
        x=[biggest_increase_day],
        y=[filtered_data.loc[filtered_data["day"] == biggest_increase_day, "nocturnal_hrv"].iloc[0]],
        mode="markers",
        marker=dict(size=12, symbol="star", color="green"),
        name="Biggest Increase",
    )
)

fig.add_trace(
    go.Scatter(
        x=[biggest_decrease_day],
        y=[filtered_data.loc[filtered_data["day"] == biggest_decrease_day, "nocturnal_hrv"].iloc[0]],
        mode="markers",
        marker=dict(size=12, symbol="star", color="red"),
        name="Biggest Decrease",
    )
)

# Update layout
fig.update_layout(
    title=f"HRV and Daily Changes Over the Last {days} Days",
    xaxis_title="Date",
    yaxis_title="HRV (ms) / HRV Change",
    legend_title="Legend",
    hovermode="x unified",
)

# Show the plot
st.plotly_chart(fig)

# Create a dictionary with the HRV swing metrics
hrv_swing_metrics = {
    "Metric": ["Biggest Increase in HRV", "Biggest Decrease in HRV"],
    "Value": [f"{biggest_increase:.2f} ms", f"{biggest_decrease:.2f} ms"],
    "Date": [biggest_increase_day.date(), biggest_decrease_day.date()],
}

# Convert the dictionary to a DataFrame
hrv_swing_df = pd.DataFrame(hrv_swing_metrics)

# Display the table
st.dataframe(hrv_swing_df, use_container_width=True, hide_index=True)
