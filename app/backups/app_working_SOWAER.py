# Import required libraries
import pickle
import copy
import pathlib
import urllib.request
import dash
import math
import datetime as dt
import os 
import pandas as pd
import mysql.connector
from dash import html, dcc, Input, Output, State, ClientsideFunction


os.chdir('G:\\Shared drives\\Carbon Pole\\Carbon Projects and Development\\Alternance Berkehan\\Carbon Management Dashboard\\CarbonManagementDashoard_envisa\\app\\data')
relative_path = os.path.join('sowaer data', 'Sowaer Data excel.xlsx')
df_sowaer = pd.read_excel(relative_path, sheet_name = 'Sheet1')
df_sowaer['Years'] = pd.to_datetime(df_sowaer['Years']).dt.year 

# TODO: If I am going to use the csv file, should consider getting the year
# from a string. It is the last 4 characters in the string.  
# df_sowaer = pd.read_csv(relative_path, encoding = 'ISO-8859-1')
# relative_path = os.path.join('data', 'Sowaer Data.csv')

# Multi-dropdown options
from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Carbon Dashboard"
server = app.server

# Create controls
county_options = [
    {"label": str(COUNTIES[county]), "value": str(county)} for county in COUNTIES
]

well_status_options = [
    {"label": str(WELL_STATUSES[well_status]), "value": str(well_status)}
    for well_status in WELL_STATUSES
]

well_type_options = [
    {"label": str(WELL_TYPES[well_type]), "value": str(well_type)}
    for well_type in WELL_TYPES
]

# Download pickle file
urllib.request.urlretrieve(
    "https://raw.githubusercontent.com/plotly/datasets/master/dash-sample-apps/dash-oil-and-gas/data/points.pkl",
    DATA_PATH.joinpath("points.pkl"),
)
points = pickle.load(open(DATA_PATH.joinpath("points.pkl"), "rb")) 

# Load data
df = pd.read_csv(
    "https://github.com/plotly/datasets/raw/master/dash-sample-apps/dash-oil-and-gas/data/wellspublic.csv",
    low_memory=False,
)
df["Date_Well_Completed"] = pd.to_datetime(df["Date_Well_Completed"])
df = df[df["Date_Well_Completed"] > dt.datetime(1960, 1, 1)]

trim = df[["API_WellNo", "Well_Type", "Well_Name"]]
trim.index = trim["API_WellNo"]
dataset = trim.to_dict(orient="index")

# Create global chart template

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        style="open-street-map",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("envisa-logo.png"), 
                            #That's where the following logo is : plotly | entreprise   
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "12px",
                                "margin-left": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "CO2 Emissions Associated With Different Scenarios",
                                    style={"margin-bottom": "26px",
                                           "margin-left": "50px",
                                           },
                                ),
                                # html.H5(
                                #     "Production Overview", style={"margin-top": "0px"}
                                # ),
                            ]
                        )
                    ],
                    className="twelve columns",
                    id="title",
                ),
                html.Div(
                #     [
                #         html.A(
                #             html.Button("Learn More", id="learn-more-button"),
                #             href="https://plot.ly/dash/pricing/",
                #         )
                #     ],
                    [],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            #This means that if one div element is removed, the other elements will be relocated accordingly
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Date Range:",
                            className="control_label",
                        ),
                        # dcc.RangeSlider(
                        #     id="year_slider",
                        #     min=1960,
                        #     max=2020,
                        #     marks={i: "{}".format(i) for i in range(1960, 2021, 10)},
                        #     step=1,
                        #     value=[1990, 2010],
                        #     className="dcc_control",
                        # ),
                        dcc.RangeSlider(
                            id="year_slider_emission",
                            min=2022,
                            max=2050,
                            marks={i: "{}".format(i) for i in range(2022, 2051, 4)},
                            step=1,
                            value=[2022, 2050],
                            className="dcc_control",
                        ),
                        #Dropdowns for airports
                        html.P("Aéroports:", className="control_label"),
                        dcc.Dropdown(
                            id = 'airport dropdown',
                            options = [{
                                'label': airport,
                                'value': airport
                            } for airport in df_sowaer['Aéroport'].unique()],
                            value = df_sowaer['Aéroport'].unique()[0],
                            multi = False,
                            className = "dcc_control",
                            #users should only select one airport
                        ),
                        html.P("Scénarios:", className="control_label"),
                        dcc.Dropdown(
                            id = 'scenario-dropdown',
                            options = [{
                                'label': scenario,
                                'value': scenario
                            } for scenario in df_sowaer["Scénario"].unique()], 
                            value = df_sowaer["Scénario"].unique()[::],
                            multi= True,
                            className = "dcc_control",
                        ), 
                        html.P("Paramètres:", className="control_label"),
                        dcc.RadioItems(
                            id = 'parameter-radioItems',
                            options = [{'label':param, 'value': param} for param in df_sowaer['Parametre'].unique()],
                            value = df_sowaer['Parametre'].unique()[0],
                            className = "dcc_control",
                            inline = False, #Set inline to False for vertical alignment
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [dcc.Graph(id = "emissions_graph")],
                            id = "emissionsGraphContainer", 
                            className = "pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    id="mainGraphContainer",
                    className="pretty_container twelve columns",
                )
            ],
            className = "row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="count_graph")],
                    className="pretty_container seven columns ",
                ),
                html.Div(
                    [dcc.Interval(id="interval_start_bar", interval=1, n_intervals=0),
                        dcc.Graph(id="bar_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                #Introducing dummy interval to trigger the callback without user input
                    [dcc.Interval(id="interval_start", interval=1, n_intervals=0), 
                    dcc.Graph(id="donut_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions
def human_format(num):
    if num == 0:
        return "0"

    magnitude = int(math.log(num, 1000))
    mantissa = str(int(num / (1000 ** magnitude)))
    return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]

def get_source_type_names():
    query = "SELECT DISTINCT source_type_name FROM source"
        # Connect to MySQL database
    my_db = mysql.connector.connect(
        host="localhost",
        user="root",
        port = 8111,
        password = "",
        database = "pltd8468_wp172",
    )
    cursor = my_db.cursor()  # Create a cursor object using buffered=True to fetch multiple results
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    my_db.close()
    return [row[0] for row in result]  # Return list of source type names


def filter_dataframe(df, well_statuses, well_types, year_slider):
    dff = df[
        df["Well_Status"].isin(well_statuses)
        & df["Well_Type"].isin(well_types)
        & (df["Date_Well_Completed"] > dt.datetime(year_slider[0], 1, 1))
        & (df["Date_Well_Completed"] < dt.datetime(year_slider[1], 1, 1))
    ]
    return dff


def produce_individual(api_well_num):
    try:
        points[api_well_num]
    except:
        return None, None, None, None

    index = list(
        range(min(points[api_well_num].keys()), max(points[api_well_num].keys()) + 1)
    )
    gas = []
    oil = []
    water = []

    for year in index:
        try:
            gas.append(points[api_well_num][year]["Gas Produced, MCF"])
        except:
            gas.append(0)
        try:
            oil.append(points[api_well_num][year]["Oil Produced, bbl"])
        except:
            oil.append(0)
        try:
            water.append(points[api_well_num][year]["Water Produced, bbl"])
        except:
            water.append(0)

    return index, gas, oil, water


def produce_aggregate(selected, year_slider):

    index = list(range(max(year_slider[0], 1985), 2016))
    gas = []
    oil = []
    water = []

    for year in index:
        count_gas = 0
        count_oil = 0
        count_water = 0
        for api_well_num in selected:
            try:
                count_gas += points[api_well_num][year]["Gas Produced, MCF"]
            except:
                pass
            try:
                count_oil += points[api_well_num][year]["Oil Produced, bbl"]
            except:
                pass
            try:
                count_water += points[api_well_num][year]["Water Produced, bbl"]
            except:
                pass
        gas.append(count_gas)
        oil.append(count_oil)
        water.append(count_water)

    return index, gas, oil, water


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)

#emissions graph callback
@app.callback(
        Output('emissions_graph', "figure"),
        [
            Input('airport dropdown', 'value'),
            Input('scenario-dropdown', 'value'),
            Input('parameter-radioItems', 'value'),
            Input('year_slider_emission', "value"),
        ]
)
def update_emissions_graph(selected_airport, selected_scenarios, selected_parameter, year_slider_emissions):
    layout_emissions = copy.deepcopy(layout)
    
    # Ensure selected_scenarios is always a list
    if isinstance(selected_scenarios, str):
        selected_scenarios = [selected_scenarios]

    #Sort selected_scenarios based on the initial order of scenairos in the dropdown to 
    #ensure that graphs don't overlap while rendering
    initial_order = list(df_sowaer["Scénario"].unique())
    selected_scenarios = sorted(selected_scenarios, key=lambda x: initial_order.index(x))

    filtered_df_sowaer = df_sowaer[
        (df_sowaer['Aéroport'] == selected_airport) & 
        (df_sowaer["Scénario"].isin(selected_scenarios)) & 
        (df_sowaer['Parametre'] == selected_parameter) & 
        (df_sowaer['Years'] >= year_slider_emissions[0]) & 
        (df_sowaer['Years'] <= year_slider_emissions[1])
        ]

    traces = []
    for scenario in selected_scenarios:
        df_by_scenario = filtered_df_sowaer[filtered_df_sowaer['Scénario'] == scenario]
        traces.append( 
            dict(
                type = "scatter",
                x = df_by_scenario['Years'],
                y = df_by_scenario['Emission'],
                mode = 'lines',
                name = f'{scenario}',
                fill='tozeroy'  # Makes it a non-stacked area graph
            )
        )
    layout_emissions['title'] = {
    'text': f"<b><span style= 'font-size:14px;'>Emissions for selected scenarios at {selected_airport}</span></b>",
    'x': 0.5  # Center the title (optional)
    }

    figure = dict(data = traces, layout = layout_emissions)
    return figure

# Main graph -> bar graph
@app.callback(
        Output("bar_graph", "figure"), 
        [Input("interval_start_bar", 
               component_property= "n_intervals_bar")], #Triggered once on Load
        )
def make_bar_figure(n_intervals_bar):
    layout_bar = copy.deepcopy(layout)

    # Connect to MySQL database
    my_db = mysql.connector.connect(
        host="localhost",
        user="root",
        port = 8111,
        password = "",
        database = "pltd8468_wp172",
    )
    cursor = my_db.cursor()  # Create a cursor object using buffered=True to fetch multiple results
    query = """
        SELECT s.source_type_name, e.emission_value_tCO2e
        FROM emissions e
        JOIN emission_type et ON e.id_emission_type = et.id
        JOIN source s ON et.id_source = s.id
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    my_db.close()

    # Create a DataFrame from the query result
    df = pd.DataFrame(result, columns=["source_type_name","emission_value_tCO2e"])
    # Aggregate emissions data by emission type
    aggregate = df.groupby("source_type_name")["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame

    '''
    if main_graph_hover is None:
        main_graph_hover = {
            "points": [
                {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
            ]
        }

    chosen = [point["customdata"] for point in main_graph_hover["points"]]
    index, gas, oil, water = produce_individual(chosen[0])

    if index is None:
        annotation = dict(
            text="No data available",
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
        )
        layout_individual["annotations"] = [annotation]
        data = []
    else: 
    '''

    data = [
        dict(
            type="bar",
            x = aggregate["source_type_name"],
            y = aggregate["emission_value_tCO2e"],
            marker=dict(color=["#57c7d4", "#f9a825", "#ba68c8", "#81c784", "#ff7043", "#4dd0e1"]),
            ),
"""         dict(
            type="scatter",
            mode="lines+markers",
            name="Oil Produced (bbl)",
            x=index,
            y=oil,
            line=dict(shape="spline", smoothing=2, width=1, color="#a9bb95"),
            marker=dict(symbol="diamond-open"),
        ),
        dict(
            type="scatter",
            mode="lines+markers",
            name="Water Produced (bbl)",
            x=index,
            y=water,
            line=dict(shape="spline", smoothing=2, width=1, color="#92d8d8"),
            marker=dict(symbol="diamond-open"),
        ),
 """    
    ]

    layout_bar["title"] = "Source-wise Emissions"
    layout_bar["xaxis"] = dict(title="Sources")
    layout_bar["yaxis"] = dict(title="Emissions (tCO2e)")

    figure = dict(data=data, layout=layout_bar)
    return figure

# Selectors, main graph -> pie graph
@app.callback(
    Output("donut_graph", "figure"),
    [Input("interval_start", "n_intervals")], #Triggered once on Load
)
def make_donut_figure(n_intervals):
    layout_pie = copy.deepcopy(layout)
    
    # Connect to MySQL database
    my_db = mysql.connector.connect(
        host="localhost",
        user="root",
        port = 8111,
        password = "",
        database = "pltd8468_wp172",
    )
    cursor = my_db.cursor()  # Create a cursor object using buffered=True to fetch multiple results
    
    query = """
        SELECT s.source_type_name, e.emission_value_tCO2e
        FROM emissions e
        JOIN emission_type et ON e.id_emission_type = et.id
        JOIN source s ON et.id_source = s.id
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    my_db.close()

     # Create a DataFrame from the query result
    df = pd.DataFrame(result, columns=["source_type_name","emission_value_tCO2e"])
    # Aggregate emissions data by emission type
    aggregate = df.groupby("source_type_name")["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame

    data = [
        dict(
            type="pie",
            labels=aggregate["source_type_name"],
            values=aggregate["emission_value_tCO2e"],
            name="Emission Breakdown",
            hoverinfo="label+value+percent",
            # textinfo="label+percent+name",
            textinfo = "none",  
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
            domain={"x": [0, 0.75], "y": [0, 1]}, 
            #Positioning of the pie chart
            #domain controls the size and position of the pie chart. Increasing the range
            #(e.g. [0.1,  0.9]) will increase the size of the pie chart
        ),
    ]
    #Layout customization
    layout_pie={
        "title": "Emission Breakdown by Sources:",
        "font": dict(color="#777777"),
        "legend": dict(
            font=dict(color="#333333", size="10"), 
            orientation="v", 
            bgcolor="rgba(0,0,0,0)"
        ),
        "showlegend": True, #Hide the legend
    }

    figure = dict(data=data, layout=layout_pie)
    return figure

# Main
if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
