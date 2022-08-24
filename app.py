from re import X
from dash import Dash, html, Input, Output, dash_table
from dash import dcc
import dash_bootstrap_components as dbc
from dash import dcc
from datetime import date, datetime, timedelta
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import data
import pytz

def load_table():
    df = dash_table.DataTable(table)
    return df

def load_data(date):
    table = []
    status, text = data.stash_data(date, local=False)
    if status == "Error":
        if  "(NoSuchKey)" in text:
            text = "No data found for this day" 
        return {}, [], text, []
    df = pd.read_csv(text)

    last_row = df.iloc[-1]
    t = last_row["Time"]
    open_prices = df.query("`Time` == @t.T and `Datatype` == 'calculated_open_price'")
    close_prices = df.query("`Time` == @t.T and `Datatype` == 'calculated_close_price'")

    df = df.query("Datatype == 'calculated_pnl'")
    df = df.drop(['Datatype'], axis=1)
    df = df.drop(['Portfolio'], axis=1)
    df.reindex()

    col_names = df.columns[2:]

    for col_name in col_names:
        open_price = open_prices.iloc[0][col_name]
        close_price = close_prices.iloc[0][col_name]
        table.append({
            "symbol" : col_name,
            "opening_price" : open_price,
            "closing_price" : close_price
        })
    
    return df, col_names, status, table


app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])
server = app.server

dt = date.today()
day_of_week = dt.weekday()
if day_of_week == 6:
    dt = dt - timedelta(2)
elif day_of_week == 5:
    dt = dt - timedelta(1)
start_date = str(dt.year) + str(dt.month).zfill(2) + str(dt.day).zfill(2)

df, col_names, status, table = load_data(start_date)
# Add a hash loading spinner
#app.layout = dls.Hash()
app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Div("Trading Time Series", 
                    className="text-center",
                    style={"font-weight": "bold", "font-size": "40px"} 
                ), width=12,
            ),
        ]),
        dbc.Row(
            dbc.Col(
                dbc.Container(className="text-center",children=[
                    dcc.DatePickerSingle(
                        id='date_id',
                        min_date_allowed=date(2022, 1, 1),
                        max_date_allowed=date.today(),
                        initial_visible_month=dt,
                        date=dt
                    )                ]
                ), width=12,
            ),
        ),

    dbc.Row(
            dbc.Col(
                dcc.Loading(
                    children=[dcc.Graph(id="graph")], 
                    color="#119DFF", type="dot", fullscreen=True
            )
        )
    ),
    dbc.Row(
        dbc.Col(html.Div([
            html.P(id = "status",
            children=[status])
            ])
        )
    ),
    html.Div([
        dash_table.DataTable(
            id='data_table'
        )
    ]),
    dcc.Interval(
        id='interval-component',
        interval=2*1000*60, # in milliseconds
        n_intervals=0
    )
                
])

@app.callback(
    Output(component_id="graph", component_property="figure"),
    Output("status", "children"),
    Output("data_table", "data"),
    Input(component_id="date_id", component_property="date"),
    Input(component_id="interval-component", component_property="n_intervals"))

def update_line_chart(value, interval):
    date = value[:4] + value[5:7] + value[8:10]
    print("about to load data for ", date)
    df = None
    #col_names = None
    df, col_names, status, table = load_data(date)   
    if len(df) == 0:
        return {}, status, table
    # change the timestamp into just hh:mm string
    for index in range(0,len(df)): 
        dt_object = datetime.fromtimestamp(df.iat[index,1])
        utc_dt = dt_object.astimezone(pytz.utc)
        localDatetime = utc_dt.astimezone(pytz.timezone('US/Eastern'))
        date_time = localDatetime.strftime("%H:%M")
        df.iat[index,1] = date_time

    print("got data for " + date)
    print(df)
    fig = px.line(df, x="Time", y=col_names, 
            title= "Bob\'s Cool Line Graph")
    fig.update_traces()
    return (fig, status, table)

if __name__ == "__main__":
    app.run_server(debug=True)