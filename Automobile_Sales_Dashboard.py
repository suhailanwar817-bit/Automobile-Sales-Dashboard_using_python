"""
Automobile Sales Statistics Dashboard
-------------------------------------
Interactive Dash app with two reports:
  1. Yearly Statistics   - choose a year to explore sales and ad spend
  2. Recession Statistics - sales and ad spend during recession periods

Install:  pip install dash pandas plotly
Run:      python automobile_dashboard.py   ->  http://127.0.0.1:8080
"""

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, dcc, html

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
DATA_URL = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "d51iMGfp_t0QpO30Lym-dw/automobile-sales.csv"
)

data = pd.read_csv(DATA_URL)

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

YEAR_LIST = sorted(data["Year"].unique())

REPORT_YEARLY = "Yearly Statistics"
REPORT_RECESSION = "Recession Period Statistics"

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
COLOR_TITLE = "#503D36"
COLOR_CARD_BG = "#F5F2F0"

DROPDOWN_STYLE = {"width": "100%", "fontSize": "18px"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_graph(fig):
    """Wrap a Plotly figure in a consistently styled dcc.Graph."""
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=60, b=40))
    return dcc.Graph(figure=fig, style={"flex": "1", "minWidth": "0"})


def chart_row(*graphs):
    """Place graphs side by side."""
    return html.Div(list(graphs), style={"display": "flex", "gap": "16px", "marginBottom": "16px"})


def kpi_card(title, value):
    """Small summary card."""
    return html.Div(
        [
            html.Div(title, style={"fontSize": "14px", "color": "#6B6B6B"}),
            html.Div(value, style={"fontSize": "26px", "fontWeight": "bold", "color": COLOR_TITLE}),
        ],
        style={
            "flex": "1",
            "padding": "14px 18px",
            "backgroundColor": COLOR_CARD_BG,
            "borderRadius": "8px",
            "textAlign": "center",
        },
    )


def kpi_row(df):
    """Headline numbers for the given slice of data."""
    return html.Div(
        [
            kpi_card("Average Sales", f"{df['Automobile_Sales'].mean():,.0f}"),
            kpi_card("Total Sales", f"{df['Automobile_Sales'].sum():,.0f}"),
            kpi_card("Total Ad Spend", f"${df['Advertising_Expenditure'].sum():,.0f}"),
        ],
        style={"display": "flex", "gap": "16px", "margin": "16px 0"},
    )


def sort_months(df):
    """Sort a frame by calendar month when Month holds standard abbreviations."""
    if set(df["Month"].unique()) <= set(MONTH_ORDER):
        df = df.copy()
        df["Month"] = pd.Categorical(df["Month"], categories=MONTH_ORDER, ordered=True)
        df = df.sort_values("Month")
    return df


# ---------------------------------------------------------------------------
# App and layout
# ---------------------------------------------------------------------------
app = dash.Dash(__name__)
app.title = "Automobile Statistics Dashboard"

app.layout = html.Div(
    [
        html.H1(
            "Automobile Sales Statistics Dashboard",
            style={"textAlign": "center", "color": COLOR_TITLE, "fontSize": 28},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Select Statistics:"),
                        dcc.Dropdown(
                            id="dropdown-statistics",
                            options=[
                                {"label": REPORT_YEARLY, "value": REPORT_YEARLY},
                                {"label": REPORT_RECESSION, "value": REPORT_RECESSION},
                            ],
                            value=REPORT_YEARLY,
                            clearable=False,
                            style=DROPDOWN_STYLE,
                        ),
                    ],
                    style={"flex": "1"},
                ),
                html.Div(
                    [
                        html.Label("Select Year:"),
                        dcc.Dropdown(
                            id="select-year",
                            options=[{"label": int(y), "value": int(y)} for y in YEAR_LIST],
                            value=int(YEAR_LIST[0]),
                            clearable=False,
                            style=DROPDOWN_STYLE,
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "24px", "margin": "0 auto", "maxWidth": "900px"},
        ),
        html.Div(id="output-container", style={"marginTop": "20px"}),
    ],
    style={"padding": "20px", "fontFamily": "Arial, sans-serif"},
)

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@app.callback(
    Output("select-year", "disabled"),
    Input("dropdown-statistics", "value"),
)
def toggle_year_dropdown(selected_statistics):
    """The year picker only applies to the yearly report."""
    return selected_statistics != REPORT_YEARLY


@app.callback(
    Output("output-container", "children"),
    Input("dropdown-statistics", "value"),
    Input("select-year", "value"),
)
def update_output_container(selected_statistics, selected_year):
    if selected_statistics == REPORT_RECESSION:
        return recession_report()
    if selected_statistics == REPORT_YEARLY and selected_year is not None:
        return yearly_report(selected_year)
    return html.P("Please select a report type.", style={"textAlign": "center"})


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def recession_report():
    rec = data[data["Recession"] == 1]
    if rec.empty:
        return html.P("No recession data available.", style={"textAlign": "center"})

    # 1. Average sales per year during recessions
    yearly_avg = rec.groupby("Year")["Automobile_Sales"].mean().reset_index()
    chart1 = make_graph(px.line(
        yearly_avg, x="Year", y="Automobile_Sales", markers=True,
        title="Average Automobile Sales during Recession Periods",
        labels={"Automobile_Sales": "Average Sales"},
    ))

    # 2. Average sales by vehicle type
    by_type = rec.groupby("Vehicle_Type")["Automobile_Sales"].mean().reset_index()
    chart2 = make_graph(px.bar(
        by_type, x="Vehicle_Type", y="Automobile_Sales",
        title="Average Vehicles Sold by Vehicle Type during Recession",
        labels={"Automobile_Sales": "Average Sales", "Vehicle_Type": "Vehicle Type"},
    ))

    # 3. Advertising spend share by vehicle type
    ad_share = rec.groupby("Vehicle_Type")["Advertising_Expenditure"].sum().reset_index()
    chart3 = make_graph(px.pie(
        ad_share, values="Advertising_Expenditure", names="Vehicle_Type",
        title="Advertising Expenditure Share by Vehicle Type during Recession",
    ))

    # 4. Unemployment rate vs. sales by vehicle type
    unemp = (rec.groupby(["unemployment_rate", "Vehicle_Type"])["Automobile_Sales"]
                .mean().reset_index())
    chart4 = make_graph(px.bar(
        unemp, x="unemployment_rate", y="Automobile_Sales", color="Vehicle_Type",
        title="Effect of Unemployment Rate on Vehicle Type and Sales",
        labels={"unemployment_rate": "Unemployment Rate",
                "Automobile_Sales": "Average Sales"},
    ))

    return [kpi_row(rec), chart_row(chart1, chart2), chart_row(chart3, chart4)]


def yearly_report(year):
    year_df = data[data["Year"] == year]
    if year_df.empty:
        return html.P(f"No data available for {year}.", style={"textAlign": "center"})

    # 1. Average sales across all years (context for the selected year)
    all_years = data.groupby("Year")["Automobile_Sales"].mean().reset_index()
    chart1 = make_graph(px.line(
        all_years, x="Year", y="Automobile_Sales", markers=True,
        title="Yearly Average Automobile Sales (All Years)",
        labels={"Automobile_Sales": "Average Sales"},
    ))

    # 2. Monthly sales for the selected year, in calendar order
    monthly = year_df.groupby("Month")["Automobile_Sales"].sum().reset_index()
    monthly = sort_months(monthly)
    chart2 = make_graph(px.line(
        monthly, x="Month", y="Automobile_Sales", markers=True,
        title=f"Total Monthly Automobile Sales in {year}",
        labels={"Automobile_Sales": "Total Sales"},
    ))

    # 3. Average sales by vehicle type in the selected year
    by_type = year_df.groupby("Vehicle_Type")["Automobile_Sales"].mean().reset_index()
    chart3 = make_graph(px.bar(
        by_type, x="Vehicle_Type", y="Automobile_Sales",
        title=f"Average Vehicles Sold by Vehicle Type in {year}",
        labels={"Automobile_Sales": "Average Sales", "Vehicle_Type": "Vehicle Type"},
    ))

    # 4. Advertising spend by vehicle type in the selected year
    ad_spend = year_df.groupby("Vehicle_Type")["Advertising_Expenditure"].sum().reset_index()
    chart4 = make_graph(px.pie(
        ad_spend, values="Advertising_Expenditure", names="Vehicle_Type",
        title=f"Advertising Expenditure by Vehicle Type in {year}",
    ))

    return [kpi_row(year_df), chart_row(chart1, chart2), chart_row(chart3, chart4)]


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8888)