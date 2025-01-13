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
SELECT e.*, et.*, s.*, a.name AS airport_name, sc.*, sco.scope_name, co.CO2_Emission_Source_Name AS 'CO2 Emission Source Name'
    FROM emissions e
    JOIN emission_type et ON e.id_emission_type = et.id
    JOIN source s ON et.id_source = s.id
    JOIN airport a ON e.id_airport = a.id
    JOIN sub_categories sc ON s.id_sub_categories = sc.id
    JOIN co2e_emission_sources co ON sc.id_co2e_emission_sources = co.id
    JOIN scope sco ON co.id_scope = sco.id;
"""
#That way, we can use the same query for different graphs instead of performing different queries for each graph
[all_data, header_names] = connect_to_database(first_query)
all_data_df = pd.DataFrame(all_data, columns=header_names)
# print(all_data_df.head())
# print(all_data_df.columns)

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
                                    #TODO: Change the title
                                    "Carbon Management Dashboard",
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
                                                    "Select a year:",
                                                    className="control_label",
                                                ),
                                                dcc.Dropdown(
                                                    id = 'year_dropdown',
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
                                                    id = 'airport_dropdown',
                                                    options = [{
                                                        'label': airport,
                                                        'value': airport
                                                    } for airport in all_data_df['airport_name'].unique()],
                                                    value = all_data_df['airport_name'].unique()[0],
                                                    multi = False,
                                                    className = "dcc_control",
                                                    #users should only select one airport
                                                ),
                                                html.P("Filter by:", className="control_label"),
                                                dcc.Dropdown(
                                                    id = 'filtering_dropdown',
                                                    options = [{
                                                        'label': filtering,
                                                        'value': filtering
                                                    } for filtering in ['Emission Type', 'Source Type', 'Sub Categories', 'CO2 Emission Source Name']],
                                                    value = 'Source Type',
                                                    multi= False,
                                                    className = "dcc_control",
                                                ), 
                                                html.P("Scope:", className="control_label"),
                                                #TODO: Turn this into the other kind of radio items
                                                dcc.Checklist(
                                                    id = 'scope-checklist',
                                                    options = [{'label':scope, 'value': scope} for scope in all_data_df['scope_name'].unique()],
                                                    value = [all_data_df['scope_name'].unique()[0]],
                                                    className = "dcc_control",
                                                    inline = True, #Set inline to False for vertical alignment
                                                    style = {
                                                        'display': 'flex',
                                                        'width': '100%',
                                                        },
                                                    labelStyle={
                                                        'marginRight': '40px',
                                                        'marginBottom': '5px', #Optional for vertical alignment
                                                        },
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
                                    html.Div(#This div is the right-top row, mini containers, eight columns
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
                                            # html.Div(
                                            #     [dcc.Interval(id="interval_start_productivityRatio", interval=10, n_intervals=0),
                                            #         html.H6(id="productivityRatio"), html.P("Productivity Ratio(Pax/kgCO2e)")],
                                            #     id="productivity",
                                            #     #TODO: Create and modify productivity in css files
                                            #     className="mini_container",
                                            # ),
                                        ],
                                        id="info-container",
                                        className="row container-display",
                                    ),
                                    html.Div(#This div is the right-bottom row, bar graph, eight columns
                                        [dcc.Graph(id = "bar_graph")],
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
                        html.Div(#This div contains donut and scatter graphs with twelve columns
                            [
                                html.Div(
                                #Introducing dummy interval to trigger the callback without user input
                                    [dcc.Graph(id="donut_graph")],
                                    className="pretty_container seven columns",
                                ),
                                html.Div(
                                    [
                                        dcc.Graph(id="scatter_graph"),
                                        dcc.Dropdown(
                                        id = 'filter_values_dropdown',
                                        options = [],
                                        # value = all_data_df['year'].unique()[0],
                                        multi = True,
                                        className = "dcc_control",
                                        ),                                                                                     
                                    ],
                                    className="pretty_container five columns",
                                ),
                            ],
                            className="row flex-display",
                            ),
                        html.Div(#This div contains emissions and count graphs with twelve columns
                            [
                                html.Div(
                                    [dcc.Graph(id="main_bar_graph")],
                                    className="pretty_container seven columns ",
                                ),
                                html.Div(
                                    [dcc.Graph(id="emissions_graph")],
                                    className="pretty_container five columns",
                                ),
                            ],
                            className="row flex-display",
                        ),
                        html.Div(#This div contains the big main graph with twelve columns
                            [
                                html.Div(
                                    [dcc.Graph(id="count_graph")],
                                    id="mainGraphContainer",
                                    className="pretty_container twelve columns",
                                )
                            ],
                            className = "row flex-display",
                        ),
                    ],
                id="mainContainer",
                style={"display": "flex", "flex-direction": "column"}, #This applies to whole page
                ),
            ],
        ),
    ],
)

#Get the unique values for the selected column filter and update the dropdown options under scatter plot dropdown
@app.callback(
    [Output('filter_values_dropdown', 'options'),
     Output('filter_values_dropdown', 'value')],
    Input('filtering_dropdown', 'value'),
)
def update_filter_options(selected_filtering):
    unique_values = all_data_df[selected_filtering].unique()
    default_value = unique_values[0]
    return [{'label': str(value), 'value': str(value)} for value in unique_values], default_value

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
    # Output("productivityRatio", "children"),

    [Input("interval_start_totalCO2", "n_intervals"),
     Input("interval_start_carbonPassanger", "n_intervals"),
     Input("interval_start_carbonIntensity", "n_intervals"),
     Input("interval_start_energyConsumption", "n_intervals"),
    #  Input("interval_start_productivityRatio", "n_intervals"),
     ]
)
def update_metrics(n1, n2, n3, n4): #Make sure to update the number of these arguments
    global all_data_df  # Ensure all_data_df is accessible in the callback

    # Check if the DataFrame contains the required column
    if 'emission_value_tCO2e' in all_data_df.columns:
        totalCO2 = all_data_df['emission_value_tCO2e'].sum()
        totalCO2 = f"{math.ceil(totalCO2)} tCO2"  # Round up to the nearest ceiling and append "tCO2"
    else:
        totalCO2 = "0 tCO2"

    return totalCO2, 0, 0, 0 #Should update the number of these return values 

#Bar graph
@app.callback(
        Output("bar_graph", "figure"), 
        [Input("airport_dropdown", "value"),
         Input("year_dropdown", "value"),
         Input("filtering_dropdown", "value"),
         Input("scope-checklist", "value")]
        )
def make_bar_figure(selected_airport, selected_year, selected_filter, selected_scope):
    layout_bar = copy.deepcopy(layout)

    filteredDf = all_data_df[ ["airport_name", "year", "scope_name", selected_filter,"emission_value_tCO2e"] ]
    
    #Filter the data based on the filters selected by the user
    filteredDf = filteredDf[
        (filteredDf["year"] == selected_year) & 
        (filteredDf["airport_name"] == selected_airport) &
        (filteredDf["scope_name"].isin(selected_scope)) #Use isin() for array comparison
    ]

    # Aggregate emissions data by emission type
    filteredDf = filteredDf.groupby(selected_filter)["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame
    
    #NOTE: It is better to use block comments instead of git changes becase it 
    #is easier to go back and forth while trying new things.
    data = [
        dict(
            type="bar",
            x = [row[selected_filter]], #Single value for x axis
            y = [row["emission_value_tCO2e"]], #Corresponding emission value
            name = row[selected_filter],#Legend and hoverinfo
            hoverinfo="name",
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
            #TODO: Solve the hoverinfo problem

            showlegend = True,
        ) for _, row in filteredDf.iterrows()   
    ]

    #TODO: Make this title dynamic
    layout_bar["title"] = "Source-wise Emissions"
    layout_bar["font"] = dict(color="#777777")
    layout_bar["xaxis"] = dict(
                        title= "Sources",
                        tickangle= -45,
                        showticklabels= False,
                        )
    layout_bar["yaxis"] = {
                        "title": "Emissions (tCO2e)",
                        "title_standoff": 300 
                        }
    layout_bar["margin"] = dict(l=120, r=40, t=60, b=50) #Adjust margins for centering the graph
    layout_bar["legend"] = dict(
                        title = "sources",
                        font=dict(color="#333333", size="10"), 
                        orientation="v", 
                        bgcolor="rgba(0,0,0,0)"
                        )        
    
    figure = dict(data=data, layout=layout_bar)
    return figure

#Donut graph
@app.callback(
    Output("donut_graph", "figure"),
        [Input("airport_dropdown", "value"),
         Input("year_dropdown", "value"),
         Input("filtering_dropdown", "value"),
         Input("scope-checklist", "value")]
        )
def make_donut_figure(selected_airport, selected_year, selected_filter, selected_scope):
    layout_pie = copy.deepcopy(layout)
    
    filteredDf = all_data_df[ ["airport_name", "year", "scope_name", selected_filter,"emission_value_tCO2e"] ]

    #Filter the data based on the filters selected by the user
    filteredDf = filteredDf[
        (filteredDf["year"] == selected_year) & 
        (filteredDf["airport_name"] == selected_airport ) &
        (filteredDf["scope_name"].isin(selected_scope)) #Use isin() for array comparison
    ]
    
    # Aggregate emissions data by emission type
    filteredDf = filteredDf.groupby(selected_filter)["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame

    data = [
        dict(
            type="pie",
            labels=filteredDf[selected_filter],
            values=filteredDf["emission_value_tCO2e"],
            name="Emission Breakdown",
            hoverinfo="label+value+percent",
            # textinfo="label+percent+name",
            textinfo = "none",  
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
            domain={ "y": [0, 0.90]}, 
            #Positioning of the pie chart
            #domain controls the size and position of the pie chart. Increasing the range
            #(e.g. [0.1,  0.9]) will increase the size of the pie chart
        ),
    ]
    #Layout customization
    #NOTE: If you modify the layout one by one instead of using single dictionary, 
    #you can keep the initial layout. Otherwise you would be changing the layout all from the start.
    
    #TODO: Make this title dynamic
    layout_pie["title"] = "Emission Breakdown by Sources:"
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
                        font=dict(color="#333333", size="10"), 
                        orientation="v", 
                        bgcolor="rgba(0,0,0,0)"
                        )
    layout_pie["showlegend"] = True  
    
    figure = dict(data=data, layout=layout_pie)
    return figure

#This is the scatter plot by years
@app.callback(
        Output("scatter_graph", "figure"), 
        [
        Input("airport_dropdown", "value"),
        Input("filtering_dropdown", "value"),
        Input("scope-checklist", "value"),
        Input("filter_values_dropdown", "value")
        ]
    )
def make_scatter_figure(selected_airport, selected_filter, selected_scope, selected_filter_values):

    layout_scatter = copy.deepcopy(layout)
    
    # Ensure `selected_filter_values` is a list
    if not isinstance(selected_filter_values, list):
        selected_filter_values = [selected_filter_values]    

    data = []
    #TODO: Don't let the user see filtered values in the dropdown. Now we can see all the values in 
    #the filter column. 

    for filter_value in selected_filter_values:
        filteredDf = all_data_df[ 
            ["airport_name", "year", "scope_name", selected_filter,"emission_value_tCO2e"] 
        ]

        #Filter the data based on the filters selected by the user
        filteredDf = filteredDf[
            (filteredDf["airport_name"] == selected_airport ) &
            (filteredDf["scope_name"].isin(selected_scope) ) & #Use isin() for array comparison
            (filteredDf[selected_filter] == filter_value)
        ]
        
        # Aggregate emissions data by year
        filteredDf = filteredDf.groupby("year")["emission_value_tCO2e"].sum().reset_index()
        #reset_index() is used to convert the groupby object to a DataFrame    

        data.append(
            dict(
                type="scatter",
                mode="lines+markers",
                name=f"{filter_value}",
                x=filteredDf["year"],
                y=filteredDf["emission_value_tCO2e"],
                line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
                marker=dict(symbol="diamond-open"),
            ) 
        )

    layout_scatter["title"] = "Emissions Over Time"
    layout_scatter["legend"] = dict(title= "Filter Values")
    #TODO: Use previous codes for the legend, font etc.

    figure = dict(data=data, layout=layout_scatter)
    return figure

#Main bar graph
@app.callback(
#TODO: Add a year slider down below this graph
    Output("main_bar_graph", "figure"),
    [
        Input("airport_dropdown", "value"),
        Input("scope-checklist", "value"),
    ],
)
def make_main_bar_figure(selected_airport, selected_scope):

    layout_main_bar = copy.deepcopy(layout)

    filteredDf = all_data_df[ 
        ["airport_name", "year", "scope_name", "emission_value_tCO2e"] 
    ]

    #Filter the data based on the filters selected by the user
    filteredDf = filteredDf[
        (filteredDf["airport_name"] == selected_airport ) &
        (filteredDf["scope_name"].isin(selected_scope)) #Use isin() for array comparison 
    ]
    
    # Aggregate emissions data by year
    filteredDf = filteredDf.groupby("year")["emission_value_tCO2e"].sum().reset_index()
    #reset_index() is used to convert the groupby object to a DataFrame    

    # colors = []
    # for i in range(1960, 2018):
    # #This highlights the years within the selected year_slider interval while 
    # #making the other years appear faded (less prominent).        
    #     if i >= int(year_slider[0]) and i < int(year_slider[1]):
    #         colors.append("rgb(123, 199, 255)")
    #     else:
    #         colors.append("rgba(123, 199, 255, 0.2)")

    data = [
        dict(
            #This is the invisible scatter plot. 
            #Since it is invisible, it's likely to serve for interactivity
            type="scatter",
            mode="markers",
            x=filteredDf["year"],
            y=filteredDf["emission_value_tCO2e"] / 2,
            name="All Wells",
            opacity=0,
            hoverinfo="skip",
        ),
        dict(
            type="bar",
            x=filteredDf["year"],
            y=filteredDf["emission_value_tCO2e"],
            name="All Wells",
            marker=dict(color=["rgb(123, 199, 255)", "rgb(123, 199, 255)"]),
        ),
    ]

    layout_main_bar["title"] = "Total Emissions Over Time"
    layout_main_bar["dragmode"] = "select"
    layout_main_bar["showlegend"] = False
    layout_main_bar["autosize"] = True

    figure = dict(data=data, layout=layout_main_bar)
    return figure

# Main
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})
#TODO: Integrate caching into this code
