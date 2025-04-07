import dash
from dash import dcc, html, Input, Output, State
import base64
import io
import pandas as pd
import json
import plotly.graph_objs as go
import numpy as np
from scipy.optimize import curve_fit

app = dash.Dash(__name__)
app.title = "Trading Log Dashboard"

# Functions to find the best fit
function_map = {
    "line": lambda x, a, b: a * x + b,
    "sine": lambda x, a, b, c: a * np.sin(b * x + c),
    "cosine": lambda x, a, b, c: a * np.cos(b * x + c),
    "quadratic": lambda x, a, b, c: a * x ** 2 + b * x + c,
    "cubic": lambda x, a, b, c, d: a * x ** 3 + b * x ** 2 + c * x + d
}

def parse_uploaded_file(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    text = decoded.decode('utf-8')

    sandbox_logs = []
    activities_data = []
    trade_history = []

    sandbox_raw = []
    activities_raw = []
    trade_raw = ''

    section = None
    for line in text.splitlines():
        if line.strip().startswith("Sandbox logs"):
            section = "sandbox"
            continue
        elif line.strip().startswith("Activities log"):
            section = "activities"
            continue
        elif line.strip().startswith("Trade History"):
            section = "trades"
            continue

        if section == "sandbox":
            sandbox_raw.append(line)
        elif section == "activities":
            activities_raw.append(line)
        elif section == "trades":
            trade_raw += line.strip()

    sandbox_text = '\n'.join(sandbox_raw).strip()
    sandbox_entries = sandbox_text.split('}\n{')
    for i, entry in enumerate(sandbox_entries):
        if not entry.startswith('{'):
            entry = '{' + entry
        if not entry.endswith('}'):
            entry += '}'
        try:
            sandbox_logs.append(json.loads(entry))
        except:
            continue

    activities_text = '\n'.join(activities_raw)
    activities_lines = activities_text.strip().split('\n')
    try:
        activities_df = pd.read_csv(io.StringIO('\n'.join(activities_lines)), sep=';')
    except:
        activities_df = pd.DataFrame()

    try:
        trade_history = json.loads(trade_raw)
        trades_df = pd.DataFrame(trade_history)
    except:
        trades_df = pd.DataFrame()

    return sandbox_logs, activities_df, trades_df


def compute_stats(activities_df, trades_df):
    stats_layout = []

    if not activities_df.empty:
        total_pnl = activities_df['profit_and_loss'].iloc[-1]
        max_drawdown = (activities_df['profit_and_loss'].cummax() - activities_df['profit_and_loss']).max()

        stats_layout.extend([
            html.H3("Metrics Explained"),
            html.Ul([
                html.Li("Mid Price: The average of best bid and ask."),
                html.Li("SMA/EMA: Simple/Exponential Moving Averages used to track short-term trends."),
                html.Li("Max Drawdown: Largest drop from peak to trough in PnL."),
                html.Li("Win Rate: Percent of trades that made profit."),
            ], style={"lineHeight": "1.8em"})
        ])

        stats_layout.extend([
            html.H4(f"Total PnL: {total_pnl:.2f}"),
            html.H4(f"Max Drawdown: {max_drawdown:.2f}"),
        ])

    if not trades_df.empty:
        n_trades = len(trades_df)
        avg_trade_size = trades_df['quantity'].mean()
        wins = trades_df[trades_df['price'].diff().fillna(0) > 0]
        win_rate = len(wins) / n_trades if n_trades > 0 else 0

        stats_layout.extend([
            html.H4(f"Number of Trades: {n_trades}"),
            html.H4(f"Average Trade Size: {avg_trade_size:.2f}"),
            html.H4(f"Win Rate: {win_rate*100:.2f}%")
        ])

    return stats_layout


def generate_figures(activities_df, trades_df):
    figures = []

    # Create a figure for all asset prices
    price_fig = go.Figure()
    if not activities_df.empty:
        for product in activities_df['product'].unique():
            product_df = activities_df[activities_df['product'] == product].sort_values('timestamp')
            price_fig.add_trace(go.Scatter(x=product_df['timestamp'], y=product_df['mid_price'], mode='lines', name=f'{product} Mid Price'))

    price_fig.update_layout(title='Combined Asset Prices', xaxis_title='Timestamp', yaxis_title='Price')
    figures.append(dcc.Graph(figure=price_fig))

    # Create a figure for all trade volumes
    volume_fig = go.Figure()
    if not trades_df.empty:
        for symbol in trades_df['symbol'].unique():
            df = trades_df[trades_df['symbol'] == symbol].sort_values('timestamp')
            volume_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['quantity'], mode='lines', name=f'{symbol} Quantity'))

    volume_fig.update_layout(title='Combined Trade Volumes', xaxis_title='Timestamp', yaxis_title='Volume')
    figures.append(dcc.Graph(figure=volume_fig))

    return figures


# The layout
app.layout = html.Div([
    html.H1("Trading Algorithm Log Dashboard"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Log File (.txt)')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-data-upload'),

    html.Div([
        html.Label("Select Fit Function:"),
        dcc.Dropdown(
            id="function-selector",
            options=[{"label": k.capitalize(), "value": k} for k in function_map.keys()],
            value="line"
        ),
        html.Label("Custom Function (use x):"),
        dcc.Input(id="custom-function-input", type="text", placeholder="Enter function e.g. 2*x + 1", style={"width": "100%"})
    ], style={"width": "90%", "margin": "auto", "marginBottom": "20px"}),
    html.Div(id="fit-parameters", style={"marginBottom": "20px"}),

    dcc.Graph(id="combined-price-graph"),
    html.Div(id="individual-graphs")
])


@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents')
)
def update_output(contents):
    if contents is not None:
        sandbox_logs, activities_df, trades_df = parse_uploaded_file(contents)
        stats = compute_stats(activities_df, trades_df)
        figures = generate_figures(activities_df, trades_df)
        return html.Div(stats + figures)
    return html.Div("Upload a file to see the dashboard.")


@app.callback(
    Output("custom-function-input", "value"),
    Input("function-selector", "value")
)
def update_textbox_from_dropdown(selected):
    default_expressions = {
        "line": "a*x + b",
        "sine": "a*np.sin(b*x + c)",
        "cosine": "a*np.cos(b*x + c)",
        "quadratic": "a*x**2 + b*x + c",
        "cubic": "a*x**3 + b*x**2 + c*x + d"
    }
    return default_expressions.get(selected, "")

@app.callback(
    Output("combined-price-graph", "figure"),
    Output("individual-graphs", "children"),
    Output("fit-parameters", "children"),
    Input('upload-data', 'contents'),
    Input("function-selector", "value"),
    State("custom-function-input", "value")
)
def update_graphs(contents, selected_func, custom_expr):
    # Check if contents are provided; if not, return empty outputs
    if not contents:
        return go.Figure(), [], ""

    # Parse the uploaded file to extract dataframes
    sandbox_logs, activities_df, trades_df = parse_uploaded_file(contents)

    # If the activities dataframe is empty, return empty outputs
    if activities_df.empty:
        return go.Figure(), [], ""

    # Initialize a list to hold individual graphs and a string for fit parameters
    graphs = []
    fit_params_text = ""

    # Iterate over each unique product in the activities dataframe
    for product in activities_df['product'].unique():
        # Filter and sort data for the current product
        product_data = activities_df[activities_df['product'] == product].copy()
        product_data = product_data.sort_values("timestamp")

        # Calculate a 10-period Simple Moving Average (SMA)
        product_data["SMA_10"] = product_data["mid_price"].rolling(window=10).mean()

        # Prepare x and y data for curve fitting
        x = np.arange(len(product_data))
        y = product_data["mid_price"].values

        try:
            # Select the fitting function based on user input
            fit_func = function_map[selected_func]
            # Provide initial guesses for the fitting parameters
            initial_guess = [1] * (len(fit_func.__code__.co_varnames) - 1)
            # Curve fitting to find optimal parameters
            popt, _ = curve_fit(fit_func, x, y, p0=initial_guess, maxfev=10000)
            fit_y = fit_func(x, *popt)
            fit_params_text = f"Fit Parameters for {selected_func}: {popt}"
        except Exception as e:
            fit_y = np.zeros_like(x)
            print(f"Error in curve fitting: {e}")

        fig_ind = go.Figure()
        # Add mid price, SMA, and line of best fit to the figure
        fig_ind.add_trace(go.Scatter(x=product_data["timestamp"], y=product_data["mid_price"], mode="lines", name="Mid Price"))
        fig_ind.add_trace(go.Scatter(x=product_data["timestamp"], y=product_data["SMA_10"], mode="lines", name="SMA 10"))
        fig_ind.add_trace(go.Scatter(x=product_data["timestamp"], y=fit_y, mode="lines", name=f"Fit: {selected_func}"))

        # Evaluate and plot the custom function if provided
        if custom_expr:
            try:
                # Evaluate custom expression using eval
                expr_y = eval(custom_expr, {"x": x, "np": np})
                fig_ind.add_trace(go.Scatter(x=product_data["timestamp"], y=expr_y, mode="lines", name="Custom Function"))
            except Exception as e:
                print(f"Error in custom function evaluation: {e}")

        # Append the individual analysis graph to list
        graphs.append(html.Div([
            html.H4(f"{product} Analysis"),
            dcc.Graph(figure=fig_ind)
        ]))

    return go.Figure(), graphs, fit_params_text


if __name__ == '__main__':
    app.run(debug=True)
