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
from dash import html, dcc, Input, Output, State, ClientsideFunction

os.chdir('C:\\Users\\Lenovo\\OneDrive\\Belgeler\\GitHub\\oil_and_gas_envisa\\apps\\dash-oil-and-gas copy')
relative_path = os.path.join('data', 'Sowaer Data excel.xlsx')
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
                        # dcc.RadioItems(
                        #     id="well_status_selector",
                        #     options=[
                        #         {"label": "All ", "value": "all"},
                        #         {"label": "Active only ", "value": "active"},
                        #         {"label": "Customize ", "value": "custom"},
                        #     ],
                        #     value="active",
                        #     labelStyle={"display": "inline-block"},
                        #     className="dcc_control",
                        # ),
                        # dcc.Dropdown(
                        #     id="well_statuses",
                        #     options=well_status_options,
                        #     multi=True,
                        #     value=list(WELL_STATUSES.keys()),
                        #     className="dcc_control",
                        # ),
                        # dcc.Checklist(
                        #     id="lock_selector",
                        #     options=[{"label": "Lock camera", "value": "locked"}],
                        #     className="dcc_control",
                        #     value=[],
                        # ),
                        # dcc.RadioItems(
                        #     id="well_type_selector",
                        #     options=[
                        #         {"label": "All ", "value": "all"},
                        #         {"label": "Productive only ", "value": "productive"},
                        #         {"label": "Customize ", "value": "custom"},
                        #     ],
                        #     value="productive",
                        #     labelStyle={"display": "inline-block"},
                        #     className="dcc_control",
                        # ),
                        # dcc.Dropdown(
                        #     id="well_types",
                        #     options=well_type_options,
                        #     multi=True,
                        #     value=list(WELL_TYPES.keys()),
                        #     className="dcc_control",
                        # ),
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
                        # The small squares summarizing the data 
                        # html.Div(
                        #     [
                        #         html.Div(
                        #             [html.H6(id="well_text"), html.P("No. of Wells")],
                        #             id="wells",
                        #             className="mini_container",
                        #         ),
                        #         html.Div(
                        #             [html.H6(id="gasText"), html.P("Gas")],
                        #             id="gas",
                        #             className="mini_container",
                        #         ),
                        #         html.Div(
                        #             [html.H6(id="oilText"), html.P("Oil")],
                        #             id="oil",
                        #             className="mini_container",
                        #         ),
                        #         html.Div(
                        #             [html.H6(id="waterText"), html.P("Water")],
                        #             id="water",
                        #             className="mini_container",
                        #         ),
                        #     ],
                        #     id="info-container",
                        #     className="row container-display",
                        # ),
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
                    [dcc.Graph(id="individual_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
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

# @app.callback(
#     Output("aggregate_data", "data"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def update_production_text(well_statuses, well_types, year_slider):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)
#     selected = dff["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)
#     return [human_format(sum(gas)), human_format(sum(oil)), human_format(sum(water))]


# Radio -> multi
# @app.callback(
#     Output("well_statuses", "value"), [Input("well_status_selector", "value")]
# )
# def display_status(selector):
#     if selector == "all":
#         return list(WELL_STATUSES.keys())
#     elif selector == "active":
#         return ["AC"]
#     return []


# # Radio -> multi
# @app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
# def display_type(selector):
#     if selector == "all":
#         return list(WELL_TYPES.keys())
#     elif selector == "productive":
#         return ["GD", "GE", "GW", "IG", "IW", "OD", "OE", "OW"]
#     return []


# Slider -> count graph
# @app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
# def update_year_slider(count_graph_selected):

#     if count_graph_selected is None:
#         return [1990, 2010]
    
#     nums = [int(point["pointNumber"]) for point in count_graph_selected["points"]]
#     return [min(nums) + 1960, max(nums) + 1961]


# # Selectors -> well text
# @app.callback(
#     Output("well_text", "children"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def update_well_text(well_statuses, well_types, year_slider):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)
#     return dff.shape[0]


# @app.callback(
#     [
#         Output("gasText", "children"),
#         Output("oilText", "children"),
#         Output("waterText", "children"),
#     ],
#     [Input("aggregate_data", "data")],
# )
# def update_text(data):
#     return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl"

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


# # Selectors -> main graph
# @app.callback(
#     Output("main_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
#     [State("lock_selector", "value"), State("main_graph", "relayoutData")],
# )
# def make_main_figure(well_statuses, well_types, year_slider, selector, main_graph_layout):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     traces = []
#     for well_type, dfff in dff.groupby("Well_Type"):
#         trace = dict(
#             type="scattermapbox",
#             lon=dfff["Surface_Longitude"],
#             lat=dfff["Surface_latitude"],
#             text=dfff["Well_Name"],
#             customdata=dfff["API_WellNo"],
#             name=WELL_TYPES[well_type],
#             marker=dict(size=4, opacity=0.6),
#         )
#         traces.append(trace)

#     # relayoutData is None by default, and {'autosize': True} without relayout action
#     if main_graph_layout is not None and selector is not None and "locked" in selector:
#         if "mapbox.center" in main_graph_layout.keys():
#             lon = float(main_graph_layout["mapbox.center"]["lon"])
#             lat = float(main_graph_layout["mapbox.center"]["lat"])
#             zoom = float(main_graph_layout["mapbox.zoom"])
#             layout["mapbox"]["center"]["lon"] = lon
#             layout["mapbox"]["center"]["lat"] = lat
#             layout["mapbox"]["zoom"] = zoom

#     figure = dict(data=traces, layout=layout)
#     return figure


# Main graph -> individual graph
@app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
def make_individual_figure(main_graph_hover):

    layout_individual = copy.deepcopy(layout)

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
        data = [
            dict(
                type="scatter",
                mode="lines+markers",
                name="Gas Produced (mcf)",
                x=index,
                y=gas,
                line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
                marker=dict(symbol="diamond-open"),
            ),
            dict(
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
        ]
        layout_individual["title"] = dataset[chosen[0]]["Well_Name"]

    figure = dict(data=data, layout=layout_individual)
    return figure


# # Selectors, main graph -> aggregate graph
# @app.callback(
#     Output("aggregate_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#         Input("main_graph", "hoverData"),
#     ],
# )
# def make_aggregate_figure(well_statuses, well_types, year_slider, main_graph_hover):

#     layout_aggregate = copy.deepcopy(layout)

#     if main_graph_hover is None:
#         main_graph_hover = {
#             "points": [
#                 {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
#             ]
#         }

#     chosen = [point["customdata"] for point in main_graph_hover["points"]]
#     well_type = dataset[chosen[0]]["Well_Type"]
#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     selected = dff[dff["Well_Type"] == well_type]["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)

#     data = [
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Gas Produced (mcf)",
#             x=index,
#             y=gas,
#             line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
#         ),
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Oil Produced (bbl)",
#             x=index,
#             y=oil,
#             line=dict(shape="spline", smoothing="2", color="#849E68"),
#         ),
#         dict(
#             type="scatter",
#             mode="lines",
#             name="Water Produced (bbl)",
#             x=index,
#             y=water,
#             line=dict(shape="spline", smoothing="2", color="#59C3C3"),
#         ),
#     ]
#     layout_aggregate["title"] = "Aggregate: " + WELL_TYPES[well_type]

#     figure = dict(data=data, layout=layout_aggregate)
#     return figure


# # Selectors, main graph -> pie graph
# @app.callback(
#     Output("pie_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def make_pie_figure(well_statuses, well_types, year_slider):

#     layout_pie = copy.deepcopy(layout)

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     selected = dff["API_WellNo"].values
#     index, gas, oil, water = produce_aggregate(selected, year_slider)

#     aggregate = dff.groupby(["Well_Type"]).count()

#     data = [
#         dict(
#             type="pie",
#             labels=["Gas", "Oil", "Water"],
#             values=[sum(gas), sum(oil), sum(water)],
#             name="Production Breakdown",
#             text=[
#                 "Total Gas Produced (mcf)",
#                 "Total Oil Produced (bbl)",
#                 "Total Water Produced (bbl)",
#             ],
#             hoverinfo="text+value+percent",
#             textinfo="label+percent+name",
#             hole=0.5,
#             marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
#             domain={"x": [0, 0.45], "y": [0.2, 0.8]},
#         ),
#         dict(
#             type="pie",
#             labels=[WELL_TYPES[i] for i in aggregate.index],
#             values=aggregate["API_WellNo"],
#             name="Well Type Breakdown",
#             hoverinfo="label+text+value+percent",
#             textinfo="label+percent+name",
#             hole=0.5,
#             marker=dict(colors=[WELL_COLORS[i] for i in aggregate.index]),
#             domain={"x": [0.55, 1], "y": [0.2, 0.8]},
#         ),
#     ]
#     layout_pie["title"] = "Production Summary: {} to {}".format(
#         year_slider[0], year_slider[1]
#     )
#     layout_pie["font"] = dict(color="#777777")
#     layout_pie["legend"] = dict(
#         font=dict(color="#CCCCCC", size="10"), orientation="h", bgcolor="rgba(0,0,0,0)"
#     )

#     figure = dict(data=data, layout=layout_pie)
#     return figure


# # Selectors -> count graph
# @app.callback(
#     Output("count_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def make_count_figure(well_statuses, well_types, year_slider):

#     layout_count = copy.deepcopy(layout)

#     dff = filter_dataframe(df, well_statuses, well_types, [1960, 2017])
#     g = dff[["API_WellNo", "Date_Well_Completed"]]
#     g.index = g["Date_Well_Completed"]
#     g = g.resample("A").count()

#     colors = []
#     for i in range(1960, 2018):
#         if i >= int(year_slider[0]) and i < int(year_slider[1]):
#             colors.append("rgb(123, 199, 255)")
#         else:
#             colors.append("rgba(123, 199, 255, 0.2)")

#     data = [
#         dict(
#             type="scatter",
#             mode="markers",
#             x=g.index,
#             y=g["API_WellNo"] / 2,
#             name="All Wells",
#             opacity=0,
#             hoverinfo="skip",
#         ),
#         dict(
#             type="bar",
#             x=g.index,
#             y=g["API_WellNo"],
#             name="All Wells",
#             marker=dict(color=colors),
#         ),
#     ]

#     layout_count["title"] = "Completed Wells/Year"
#     layout_count["dragmode"] = "select"
#     layout_count["showlegend"] = False
#     layout_count["autosize"] = True

#     figure = dict(data=data, layout=layout_count)
#     return figure


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
