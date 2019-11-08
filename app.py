import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import dash_table
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:JedOxPkdAG12h2u5f7FI@dash-demo.cp4nbyprm5jt.us-east-2.rds.amazonaws.com/strategy')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('Entry time',))

#df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])
#df = df.sort_values('Entry time') # if you are going to calcucate raturns base on the final and initial date, you should sort the data by date
df['YearMonth'] = pd.to_datetime(df['Entry time'].dt.strftime('%b %Y'))

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max(),
                                        initial_visible_month = df['Entry time'].min()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            )
        ]
    )        
])


@app.callback(
    [Output('date-range', 'start_date'),
     Output('date-range', 'end_date')],
    [Input('exchange-select', 'value')])

def update_date(Exchange):
    aux = df[df['Exchange']==Exchange]
    return [aux['Entry time'].min(), aux['Entry time'].max()]

def filter_df(df, Exchange, Margin, start_date, end_date):
    return df[(df['Exchange'] == Exchange) &
     (df['Margin'] == int(Margin)) &
     (df['Entry time'] >= start_date) &
     (df['Entry time'] <= end_date)]

 
def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

@app.callback(
    [
        Output('monthly-chart', 'figure'),
        Output('market-returns', 'children'),
        Output('strat-returns', 'children'),
        Output('strat-vs-market', 'children'),
    ],
    (
        Input('exchange-select', 'value'),    
        Input('leverage-select', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'    

@app.callback(
    Output('table', 'data'),
    (
        Input('exchange-select', 'value'),
        Input('leverage-select', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    Output('pnl-types', 'figure'),
    [
        Input('exchange-select', 'value'),
        Input('leverage-select', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ]
)

def update_bar_plot(exchange, leverage, start_date, end_date):
    data = filter_df(df, exchange, leverage, start_date, end_date)
    return {'data' :[
    go.Bar(name='Short', x=data[data['Trade type']=='Short']['Entry time'].tolist(),
           y = data[data['Trade type']=='Short']['Pnl (incl fees)'].tolist(),
           marker_line_color='black',
           marker_color='black',
           marker_line_width=1.5),
    go.Bar(name='Long', x=data[data['Trade type']=='Long']['Entry time'].tolist(),
           y = data[data['Trade type']=='Long']['Pnl (incl fees)'].tolist(),
           marker_line_color='sandybrown',
           marker_color='sandybrown',
           marker_line_width=1.5)
           ], 'layout': go.Layout(
               title = 'Pnl vs Trade type', 
               width=800,
               height=450,
               margin={'l': 40, 'b': 40, 't': 60, 'r': 10}
           )
               }


@app.callback(
    Output('daily-btc', 'figure'),
    [
        Input('exchange-select', 'value'),
        Input('leverage-select', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ]
)

def update_daily_price_plot(exchange, leverage, start_date, end_date):
    data = filter_df(df, exchange, leverage, start_date, end_date)
    return {'data':
            [go.Scatter(x = data['Entry time'].tolist(),
                        y = data['BTC Price'].tolist(),
                        mode = 'lines',
                        marker_line_color = 'blue'
                        )],
             'layout': go.Layout(
               title = 'BTC price', 
               width=800,
               height=450,
               margin={'l': 40, 'b': 40, 't': 60, 'r': 10}
           )           
                        }

@app.callback(
    Output('balance', 'figure'),
    [
        Input('exchange-select', 'value'),
        Input('leverage-select', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ]
)

def update_balance_plot(exchange, leverage, start_date, end_date):
    data = filter_df(df, exchange, leverage, start_date, end_date)
    return {'data':
            [go.Scatter(x = data['Entry time'].tolist(),
                        y = data['Entry balance'].tolist(),
                        mode = 'lines',
                        marker_line_color = 'blue'
                        )],
             'layout': go.Layout(
               title = 'Balance overtime', 
               width=800,
               height=450,
               margin={'l': 40, 'b': 40, 't': 60, 'r': 10}
           )           
                        }
                        
if __name__ == "__main__":
    app.run_server(debug=True,host= '0.0.0.0')
