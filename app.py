from flask import Flask, render_template, request, redirect
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from ssh_connection import establish_ssh_connection
from collect_data import collect_data_days_based, collect_data_datetime_based
import plotly.graph_objs as go
from dash_core_components import DatePickerRange
from datetime import datetime, timedelta
from dash.dependencies import Input, Output
from dash import html, Input, Output
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# Load template
load_figure_template("bootstrap_dark")

ssh = None

app = Flask(__name__)

# Initialize Dash app within Flask app 
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP, "https://fonts.googleapis.com/css2?family=Rubik&display=swap"])

# Function to get all the users. These users will be displayed in the dropdown menu
def get_slurm_users():
    global ssh
    if ssh is None:
        print("SSH connection not established.")
        return []
    try:
        command = "sacctmgr -P show user"
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()

        # Parse the result to extract usernames
        users = [line.split('|')[0] for line in result.strip().split('\n')[1:] if line]
        return users
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST'])
def dashboard():
    global ssh
    ssh_username = request.form['username']
    ssh_password = request.form['password']
    ssh_host = "simlab-cluster.um6p.ma"

    # Establish SSH connection
    ssh = establish_ssh_connection(ssh_host, ssh_username, ssh_password)
    if ssh:
        return redirect('/dashboard/')
    else:
        return render_template('login.html', error="SSH connection failed")


# Function to serve the layout, called each time the page is loaded
def serve_layout():
    slurm_users = get_slurm_users()  # Fetch users from Slurm DB
    return html.Div([
    # Sidebar
    html.Div([
        html.H2("Filters", style={'textAlign': 'center', 'color': '#FFF'}),
            # User selection dropdown
            html.Div(
                [
                    dcc.Dropdown(
                        id='user-dropdown',
                        options=[{'label': user, 'value': user} for user in slurm_users],
                        value=None
                    )
                ],
                style={'margin-bottom': '20px', 'margin-top': '20px'}
            ),
            html.Div([
                html.Label('Customize the timeframe\t', style={'color': '#FFF'}),
                daq.BooleanSwitch(
                    id='date-selection-toggle',
                    on=True,  # Initially on
                    labelPosition="top",
                    color="#EF213B",
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '10px', 'margin-bottom': '10px'}),
            
            # Date Picker Range
            html.Div([
                DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=datetime(1995, 8, 5), 
                    max_date_allowed=datetime.now(),
                    initial_visible_month=datetime.now(),
                    start_date=datetime.now() - timedelta(days=30),  # Default to 30 days ago
                    end_date=datetime.now(),
                    style={
                        'display': 'block',  # Initially visible
                        'width': '100%',  
                        'fontFamily': 'Fantasy, sans-serif',  
                        'border': '1px solid #ccc',  
                        'borderRadius': '5px',  
                        'padding': '10px',  
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'  
                    }
                )
                ],
                style={
                    'display': 'flex',  
                    'flexDirection': 'column',  
                    'alignItems': 'center', 
                    # 'margin-bottom': '20px',
                }
            ),

            # Timeframe selection
            html.Div(
                [dcc.Dropdown(
                    id='timeframe-dropdown',
                    options=[
                        {'label': '1 Month Ago', 'value': 30},
                        {'label': '2 Months Ago', 'value': 60},
                        {'label': '3 Months Ago', 'value': 90},
                        {'label': '4 Months Ago', 'value': 120},
                        {'label': '5 Months Ago', 'value': 150},
                        {'label': '6 Months Ago', 'value': 180},
                        {'label': '7 Months Ago', 'value': 210},
                        {'label': '8 Months Ago', 'value': 240},
                        {'label': '9 Months Ago', 'value': 270},
                        {'label': '10 Months Ago', 'value': 300},
                        {'label': '11 Months Ago', 'value': 330},
                        {'label': '1 Year Ago', 'value': 365}
                    ],
                    value=30  # Default value set to 1 month ago
                )
                ],
                style={
                    'margin-bottom': '20px',
                    }
            ),

            # Toggle between CPU usage and Hours usage
            html.Div(
                [dcc.RadioItems(
                    id='graph-type',
                    options=[
                        {'label': 'Number of CPUs/GPUs', 'value': 'cpu_gpu'},
                        {'label': 'Hours Usage', 'value': 'hours'}
                    ],
                    value='cpu_gpu',
                    labelStyle={'display': 'block', 'margin': '10px 0'},  
                    inputStyle={'marginRight': '5px'},  
                    style={
                        'display': 'flex',  
                        'flexDirection': 'column',  
                        'fontFamily': 'Arial, sans-serif',  
                        'padding': '10px',  
                        'border': '1px solid #ccc',  
                        'margin': '20px',
                        'borderRadius': '10px', 
                        'backgroundColor': '#000', 
                        'color': '#FFF', 
                    }
                )
                ],
                style={}
            )
    ], style={
        'display': 'flex',  
        'flexDirection': 'column',  
        'justifyContent': 'center', 
        'height': '100vh',  
        'width': '20%',  
        'fontFamily': "'Rubik', sans-serif", 
        'float': 'left', 
        'borderRight': '2px solid #04090E', 
        'padding': '0 10px 20px', 
        'background-color': '#04090E', 
        'box-sizing': 'border-box'}),
    
    # Main content area
    html.Div([
        html.H2("Visualize the results", style={'textAlign': 'center', 'color': '#000', 'font-weight': 'bold'}),
        dcc.Graph(id='usage-graph')
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'width': '80%',
        'float': 'right', 
        'height': '100vh', 
        'padding': '40px', 
        'background-color': "#FFF", 
        'fontFamily': "'Rubik', sans-serif"})
])

# Set the layout to the serve_layout function
dash_app.layout = serve_layout

@dash_app.callback(
    [Output('date-picker-range', 'style'),
     Output('timeframe-dropdown', 'style')],
    [Input('date-selection-toggle', 'on')]
)
def toggle_date_input(toggle_value):
    if toggle_value:
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}


# Callback to update the graph based on user and timeframe selection
@dash_app.callback(
    Output('usage-graph', 'figure'),
    [Input('user-dropdown', 'value'), 
     Input('graph-type', 'value'), 
     Input('timeframe-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('date-selection-toggle', 'on')]  # Add toggle switch's state as input
)
def update_graph(selected_user, selected_graph, selected_timeframe, start_date, end_date, toggle_switch_state):
    global ssh
    if not selected_user or not ssh:
        return go.Figure()  # Return an empty figure if no user is selected or if SSH connection fails
    
    # Initialize an empty DataFrame
    dataframe = pd.DataFrame()

    # Determine data collection method based on toggle switch state
    if toggle_switch_state:
        # Custom date range selected
        if start_date and end_date:
            dataframe = collect_data_datetime_based(ssh, selected_user, start_date, end_date)
    else:
        # Predefined timeframe selected
        if selected_timeframe is not None:
            dataframe = collect_data_days_based(ssh, selected_user, selected_timeframe)

    if dataframe.empty:
        # Return a figure with a message if the dataframe is empty
        return go.Figure(
            data=[go.Scatter(x=[], y=[])],
            layout=go.Layout(
                title="No data available for this user during this period of time.",
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
            )
        )

    # Depending on the selected graph type, create and return the appropriate figure
    if selected_graph == 'cpu_gpu':
        # Generate the CPU/GPU usage bar chart figure
        df = dataframe.groupby('Date')[['AllocCPUS', 'NumGPUs']].sum().reset_index()
        
        # Rename the columns 'AllocCPUS' to 'CPU' and 'NumGPUs' to 'GPU'
        df = df.rename(columns={'AllocCPUS': 'CPU', 'NumGPUs': 'GPU'})
        
        fig = px.bar(df, x='Date', y=['CPU', 'GPU'], title='Daily Number of CPUs/GPUs Used', labels={'value':'Usage', 'variable':'Resource'})
        fig.update_layout(xaxis_title='Date', yaxis_title='Usage')
        # fig.update_traces(texttemplate='%{value}', textposition='outside')

    else:
        # Create Hours usage graph
        df = dataframe
        def convert_to_timedelta(time_str):
            days, time = time_str.split('-')
            hours, minutes, seconds = map(int, time.split(':'))
            return timedelta(days=int(days), hours=hours, minutes=minutes, seconds=seconds)
        
        df['CPUTime'] = df['CPUTime'].apply(convert_to_timedelta)
        df['GPUTime'] = df['GPUTime'].apply(convert_to_timedelta)

        # Group by Date and sum CPUTime and GPUTime
        grouped_df = df.groupby('Date').agg({'CPUTime': 'sum', 'GPUTime': 'sum'}).reset_index()

        # Convert timedeltas to total hours for plotting
        grouped_df['CPU'] = grouped_df['CPUTime'].dt.total_seconds() / 3600
        grouped_df['GPU'] = grouped_df['GPUTime'].dt.total_seconds() / 3600
        
        # Create plot
        fig = px.bar(grouped_df, x='Date', y=['CPU', 'GPU'],
                    title='Daily CPU and GPU Hours Usage',
                    labels={'value':'Usage (hours)', 'variable':'Resource'},
                    category_orders={"variable": ["CPU", "GPU"]})
        fig.update_layout(xaxis_title='Date', yaxis_title='Usage (hours)')
        # fig.update_traces(texttemplate='%{value}h', textposition='outside')

    return fig


# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)