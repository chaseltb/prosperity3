import dash
from dash import dcc, html, Input, Output
import base64
import io
import pandas as pd
import json
import plotly.graph_objs as go

app = dash.Dash(__name__)
app.title = "Trading Log Dashboard"


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


def generate_figures(activities_df, trades_df):
    figures = []

    if not activities_df.empty:
        for product in activities_df['product'].unique():
            product_df = activities_df[activities_df['product'] == product]
            product_df = product_df.sort_values('timestamp')
            product_df['SMA_5'] = product_df['mid_price'].rolling(window=5).mean()
            product_df['EMA_5'] = product_df['mid_price'].ewm(span=5, adjust=False).mean()

            price_fig = go.Figure()
            price_fig.add_trace(go.Scatter(x=product_df['timestamp'], y=product_df['mid_price'], name='Mid Price'))
            price_fig.add_trace(go.Scatter(x=product_df['timestamp'], y=product_df['SMA_5'], name='SMA 5'))
            price_fig.add_trace(go.Scatter(x=product_df['timestamp'], y=product_df['EMA_5'], name='EMA 5'))
            price_fig.update_layout(title=f'{product} - Price and Moving Averages', xaxis_title='Timestamp', yaxis_title='Price')

            pnl_fig = go.Figure()
            pnl_fig.add_trace(go.Scatter(x=product_df['timestamp'], y=product_df['profit_and_loss'], name='PnL', mode='lines+markers'))
            pnl_fig.update_layout(title=f'{product} - PnL Over Time', xaxis_title='Timestamp', yaxis_title='PnL')

            figures.append(dcc.Graph(figure=price_fig))
            figures.append(dcc.Graph(figure=pnl_fig))

    if not trades_df.empty:
        for symbol in trades_df['symbol'].unique():
            df = trades_df[trades_df['symbol'] == symbol]
            volume_fig = go.Figure()
            volume_fig.add_trace(go.Bar(x=df['timestamp'], y=df['quantity'], name='Quantity'))
            volume_fig.update_layout(title=f'{symbol} - Trade Volume Over Time', xaxis_title='Timestamp', yaxis_title='Quantity')

            price_fig = go.Figure()
            price_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], name='Trade Price', mode='markers'))
            price_fig.update_layout(title=f'{symbol} - Trade Prices', xaxis_title='Timestamp', yaxis_title='Price')

            figures.append(dcc.Graph(figure=volume_fig))
            figures.append(dcc.Graph(figure=price_fig))

    return figures


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
    html.Div(id='output-data-upload')
])


@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents')
)
def update_output(contents):
    if contents is not None:
        sandbox_logs, activities_df, trades_df = parse_uploaded_file(contents)
        figures = generate_figures(activities_df, trades_df)
        return html.Div(figures)
    return html.Div("Upload a file to see the dashboard.")


if __name__ == '__main__':
    app.run(debug=True)
