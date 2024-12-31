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
import plotly.graph_objects as go
#plotly.express requires less code and is easier to use for simple plots, 
#while plotly.graph_objects provides more flexibility for customization.
import mysql.connector
from dash import html, dcc, Input, Output, State, ClientsideFunction
from flask_caching import Cache

os.chdir('G:\\Shared drives\\Carbon Pole\\Carbon Projects and Development\\Alternance Berkehan\\Carbon Management Dashboard\\CarbonManagementDashoard_envisa\\app')

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Carbon Dashboard"
server = app.server

def connect_to_database(query):
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
    column_names = [desc[0] for desc in cursor.description]
    result = cursor.fetchall()
    cursor.close()
    my_db.close()
    return result, column_names
    #This process takes time because it requires connection to a database and fetching data
first_query = """ 
SELECT e.*, et.*, s.*, a.name AS airport_name, sc.*, sco.scope_name, co.source_name AS co2_emission_source_name
    FROM emissions e
    JOIN emission_type et ON e.id_emission_type = et.id
    JOIN source s ON et.id_source = s.id
    JOIN airport a ON e.id_airport = a.id
    JOIN sub_categories sc ON s.id_sub_categories = sc.id
    JOIN co2e_emission_sources co ON sc.id_co2e_emission_sources = co.id
    JOIN scope sco ON co.id_scope = sco.id;
"""
[all_data, header_names] = connect_to_database(first_query)
all_data_df = pd.DataFrame(all_data, columns=header_names)
print(all_data_df.head())

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
        html.Div(#This div contains the header with three columns
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
                    [

                    ],
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
                        html.Div(#This div is the first row with 12 columns
                            [
                                html.Div(#This div is the left column with four columns                                                             
                                    [
                                        html.Div(#This div is the filters column with four columns
                                            [
                                                html.P(
                                                    "Date Range:",
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id = 'year dropdown',
                                                    options = [{
                                                        'label': year,
                                                        'value': year
                                                    } for year in all_data_df['year'].unique()],
                                                    value = all_data_df['year'].unique()[0],
                                                    multi = False,
                                                    className = "dcc_control",
                                                ),                                                
                                                #Dropdowns for airports
                                                html.P("Aéroports:", className="control_label"),
                                                dcc.Dropdown(
                                                    id = 'airport dropdown',
                                                    options = [{
                                                        'label': airport,
                                                        'value': airport
                                                    } for airport in all_data_df['airport_name'].unique()],
                                                    value = all_data_df['airport_name'].unique()[0],
                                                    multi = False,
                                                    className = "dcc_control",
                                                    #users should only select one airport
                                                ),
                                                html.P("Sub categories:", className="control_label"),
                                                dcc.Dropdown(
                                                    id = 'sub_category-dropdown',
                                                    options = [{
                                                        'label': sub_category,
                                                        'value': sub_category
                                                    } for sub_category in all_data_df['sub_category_name'].unique()], 
                                                    value = all_data_df["sub_category_name"].unique()[::],
                                                    multi= True,
                                                    className = "dcc_control",
                                                ), 
                                                html.P("Scope:", className="control_label"),
                                                dcc.RadioItems(
                                                    id = 'scope-radioItems',
                                                    options = [{'label':scope, 'value': scope} for scope in all_data_df['scope_name'].unique()],
                                                    value = all_data_df['scope_name'].unique()[0],
                                                    className = "dcc_control",
                                                    inline = False, #Set inline to False for vertical alignment
                                                ),
                                            ],
                                            className="pretty_container",
                                            id="cross-filter-options",#left column
                                        ),
                                    ],
                                    id="left-column",
                                    className="four columns",
                                ),
                                html.Div(#This div contains the right column with eight columns
                                [
                                    html.Div(#This div is the right-top row with eight columns
                                        [
                                            html.Div(
                                                [dcc.Interval(id="interval_start_totalCO2", interval=10, n_intervals=0),
                                                    html.H6(id="totalCO2"), html.P("Total Carbon Emissions")],
                                                id="wells",
                                                className="mini_container",
                                            ),
                                            html.Div(
                                                [dcc.Interval(id="interval_start_carbonPassanger", interval=10, n_intervals=0),
                                                    html.H6(id="carbonPassanger"), html.P("Carbon Footprint per Passenger(kgCO2e/TU)")],
                                                id="gas",
                                                className="mini_container",
                                            ),
                                            html.Div(
                                                [dcc.Interval(id="interval_start_carbonIntensity", interval=10, n_intervals=0),
                                                    html.H6(id="carbonIntensity"), html.P("Airport Carbon Intensity(kgCO2e/TU)")],
                                                id="oil",
                                                className="mini_container",
                                            ),
                                            html.Div(
                                                [dcc.Interval(id="interval_start_energyConsumption", interval=10, n_intervals=0),
                                                    html.H6(id="energyConsumption"), html.P("Total Energy Consumption(MJ)")],
                                                id="water",
                                                className="mini_container",
                                            ),
                                            html.Div(
                                                [dcc.Interval(id="interval_start_productivityRatio", interval=10, n_intervals=0),
                                                    html.H6(id="productivityRatio"), html.P("Productivity Ratio(Pax/kgCO2e)")],
                                                id="productivity",
                                                #TODO: Create and modify productivity in css files
                                                className="mini_container",
                                            ),
                                        ],
                                        id="info-container",
                                        className="row container-display",
                                    ),
                                    html.Div(#This div is the right-bottom row with eight columns
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
                        html.Div(#This div contains the main graph with twelve columns
                            [
                                html.Div(
                                    [dcc.Graph(id="main_graph")],
                                    id="mainGraphContainer",
                                    className="pretty_container twelve columns",
                                )
                            ],
                            className = "row flex-display",
                        ),
                        html.Div(#This div contains bar and count graphs with twelve columns
                            [
                                html.Div(
                                    [dcc.Graph(id="count_graph")],
                                    className="pretty_container seven columns ",
                                ),
                                html.Div(
                                    [dcc.Interval(id="interval_start_bar", interval=10, n_intervals=0),
                                    dcc.Dropdown(
                                    id = 'co2_emission_source-dropdown',
                                    options = [{
                                        'label': co2_emission_source,
                                        'value': co2_emission_source
                                    } for co2_emission_source in all_data_df['co2_emission_source_name'].unique()], 
                                    value = all_data_df["co2_emission_source_name"].unique()[::],
                                    multi= True,
                                    className = "dcc_control",
                                    ), 
                                    dcc.Graph(id="bar_graph"),                            
                                    ],
                                    className="pretty_container five columns",
                                ),
                            ],
                            className="row flex-display",
                        ),
                        html.Div(#This div contains donut and aggregate graphs with twelve columns
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
                style={"display": "flex", "flex-direction": "column"}, #This applies to whole page
                ),
            ],
        ),
    ],
)

#TODO: Delete if not necessary
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

#TODO: Create callbacks, delete if not necessary
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)

#Mini container callbacks
@app.callback(
    Output("totalCO2", "children"),
    Output("carbonPassanger", "children"),
    Output("carbonIntensity", "children"),
    Output("energyConsumption", "children"),
    Output("productivityRatio", "children"),

    [Input("interval_start_totalCO2", "n_intervals"),
     Input("interval_start_carbonPassanger", "n_intervals"),
     Input("interval_start_carbonIntensity", "n_intervals"),
     Input("interval_start_energyConsumption", "n_intervals"),
     Input("interval_start_productivityRatio", "n_intervals"),
     ]
)
def update_metrics(n1, n2, n3, n4, n5):
    query1 = """
        SELECT SUM(emission_value_tCO2e) as totalCO2
        FROM emissions e
        JOIN emission_type et ON e.id_emission_type = et.id
        JOIN source s ON et.id_source = s.id
    """
    result = connect_to_database(query1)
    
    #Create a DataFrame from the query result
    df = pd.DataFrame(result, columns=["totalCO2"])
    totalCO2 = df["totalCO2"][0]
    # Round up to the nearest ceiling and append "tCO2"
    totalCO2 = f"{math.ceil(totalCO2)} tCO2"
    return totalCO2, 0, 0, 0, 0

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

#TODO: add year selection to the callback. 
#      Add if to filter by co2 emission source
#      Add if to filter by airport 
#Bar graph
#It was individual graph before
@app.callback(
        Output("bar_graph", "figure"), 
        [Input("airport dropdown", "value"),
         Input("co2_emission_source-dropdown", "value"),
         Input("year_dropdown", "value"),]
        )
def make_bar_figure(selected_airport, selected_co2_emission_source, selected_year):
    layout_bar = copy.deepcopy(layout)

    query = """
        SELECT s.source_type_name, e.emission_value_tCO2e
        FROM emissions e
        JOIN emission_type et ON e.id_emission_type = et.id
        JOIN source s ON et.id_source = s.id
    """
    result= connect_to_database(query)
    # Create a DataFrame from the query result
    df = pd.DataFrame(result, columns=["source_type_name","emission_value_tCO2e"])
    
    # Aggregate emissions data by emission type
    aggregate = df.groupby("source_type_name")["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame
    
    # Exclude the first bar by slicing the DataFrame
    aggregate = aggregate.iloc[1:]  # Excludes the first row
    
    #NOTE: It is better to use block comments instead of git changes becase it 
    #is easier to go back and forth while trying new things.
    data = [
        dict(
            type="bar",
            x = aggregate["source_type_name"],
            y = aggregate["emission_value_tCO2e"],
            hoverinfo = "x",
            name = "Emissions",
            # marker=dict(color=["#57c7d4", "#f9a825", "#ba68c8", "#81c784", "#ff7043", "#4dd0e1"]
            #             [: len(aggregate)])  # Ensure the color array matches the data length,
            #Colors are assigned to each bar in the bar chart
        )   
    ]
         
    layout_bar = {
        "title": "Source-wise Emissions",
        "xaxis": dict(
            title= "Sources",
            tickangle= -45,
            showticklabels= False,)
        ,
        "yaxis": {
            "title": "Emissions (tCO2e)"
        },
        "margin": dict(l=70, r=40, t=60, b=50) #Adjust margins
        }
    
    figure = dict(data=data, layout=layout_bar)
    return figure

#TODO: add year selection to the callback. 
#      Add if to filter by co2 emission source
#      Add if to filter by airport #Donut graph
@app.callback(
    Output("donut_graph", "figure"),
    [Input("interval_start", "n_intervals")], #Triggered once on Load
)
def make_donut_figure(n_intervals):
    layout_pie = copy.deepcopy(layout)
    
    query = """
        SELECT s.source_type_name, e.emission_value_tCO2e
        FROM emissions e
        JOIN emission_type et ON e.id_emission_type = et.id
        JOIN source s ON et.id_source = s.id
    """
    result = connect_to_database(query)
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
        "showlegend": True, #Hide or the legend
    }

    figure = dict(data=data, layout=layout_pie)
    return figure

# Main
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})
#TODO: Integrate caching into this code
