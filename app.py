from flask import Flask, render_template, request, redirect
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from threading import Thread
from ssh_connection import establish_ssh_connection
from collect_data import collect_data_days_based, collect_data_datetime_based
import plotly.graph_objs as go
from dash_core_components import DatePickerRange
from datetime import datetime, timedelta
from dash.dependencies import Input, Output, State
from dash import Dash, html, Input, Output, callback
import dash_daq as daq


global ssh

app = Flask(__name__)

# Initialize Dash app within Flask app 
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Function to get all the users. These users will be displayed in the dropdown menu
def get_slurm_users():
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
        # ssh.close() 
        return redirect('/dashboard/')
    else:
        return render_template('login.html', error="SSH connection failed")


# Function to serve the layout, called each time the page is loaded
def serve_layout():
    slurm_users = get_slurm_users()  # Fetch users from Slurm DB
    return html.Div([
    # Sidebar
    html.Div([
        html.H2("Filters", style={'textAlign': 'center', 'font-family': 'fantasy'}),
            # User selection dropdown
            dcc.Dropdown(
                id='user-dropdown',
                options=[{'label': user, 'value': user} for user in slurm_users],
                value=None
            ),
            html.Div([
                html.Label('Choose Date Selection Mode:'),
                daq.BooleanSwitch(
                    id='date-selection-toggle',
                    on=True,  # Initially on
                    labelPosition="top",
                    color="#9B51E0",
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
            # Date Picker Range
            DatePickerRange(
                id='date-picker-range',
                min_date_allowed=datetime(1995, 8, 5),  # Adjust as needed
                max_date_allowed=datetime.now(),
                initial_visible_month=datetime.now(),
                start_date=datetime.now() - timedelta(days=30),  # Default to 30 days ago
                end_date=datetime.now(),
                style={'display': 'block'}  # Initially visible
            ),
            # Timeframe selection
            dcc.Dropdown(
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
            ),
            # Toggle between CPU usage and Hours usage
            dcc.RadioItems(
                id='graph-type',
                options=[
                    {'label': 'CPU/GPU Usage', 'value': 'cpu_gpu'},
                    {'label': 'Hours Usage', 'value': 'hours'}
                ],
                value='cpu_gpu'
            )
    ], style={'width': '20%', 'float': 'left', 'height': '100vh', 'borderRight': '2px solid grey', 'padding': '20px', 'background-color': ''}),

    # Main content area
    html.Div([
        html.H2("Visualize the results", style={'textAlign': 'center', 'font-family': 'fantasy'}),
        dcc.Graph(id='usage-graph')
    ], style={'width': '70%', 'float': 'right', 'padding': '20px', 'background-color': ""})
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
     Input('date-selection-toggle', 'on')]  # Add toggle switch's state as input]
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
                title="No data available for this user during this period of time",
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
            )
        )

    # Depending on the selected graph type, create and return the appropriate figure
    if selected_graph == 'cpu_gpu':
        # Calculate daily CPU/GPU usage
        daily_usage = calculate_daily_cpu_gpu_usage(dataframe)
        # Generate the CPU/GPU usage bar chart figure
        fig = px.bar(daily_usage, x='Date', y=['TotalCPUs', 'TotalGPUs'], title='Daily CPU and GPU Usage', labels={'value':'Usage', 'variable':'Resource'})
        fig.update_layout(xaxis_title='Date', yaxis_title='Usage')
    else:
        # Create Hours usage graph
        daily_hours_usage = calculate_daily_hours_usage(dataframe)
        fig = px.bar(daily_hours_usage, x='Date', y='Hours', title='Daily Hours Usage')

    return fig


# Helper function to calculate daily CPU usage
def calculate_daily_cpu_gpu_usage(df):
    df = df.copy()

    daily_data = []
    for _, row in df.iterrows():
        date_range = pd.date_range(start=row['Start'].date(), end=row['End'].date(), freq='D')
        temp_df = pd.DataFrame({
            'Date': date_range, 
            'TotalCPUs': [row['AllocCPUS']] * len(date_range),
            'TotalGPUs': [row['NumGPUs']] * len(date_range)
        })
        daily_data.append(temp_df)

    daily_cpu_gpu_usage = pd.concat(daily_data, ignore_index=True)

    # Convert columns to numeric, handling non-numeric data
    daily_cpu_gpu_usage['TotalCPUs'] = pd.to_numeric(daily_cpu_gpu_usage['TotalCPUs'], errors='coerce')
    daily_cpu_gpu_usage['TotalGPUs'] = pd.to_numeric(daily_cpu_gpu_usage['TotalGPUs'], errors='coerce')

    # Group by date and sum both CPUs and GPUs
    daily_cpu_gpu_usage = daily_cpu_gpu_usage.groupby('Date').sum().reset_index()

    return daily_cpu_gpu_usage

# Helper function to calculate daily Hours usage
# This function computes the sum of daily usage hours per user.
# It returns the summed totals grouped by user and date.
def calculate_daily_hours_usage(df):
    # Create a copy of the DataFrame to avoid modifying the original DataFrame
    df = df.copy()
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    # print(df)
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    # Apply the function
    daily_usage_data = [usage for idx, row in df.iterrows() for usage in calculate_daily_usage(row)]
    daily_usage_df = pd.DataFrame(daily_usage_data)

    # print(daily_usage_df)
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    # Group by User and Date, then sum the Hours
    grouped_df = daily_usage_df.groupby(['User', 'Date'])['Hours'].sum().reset_index()

    # print(grouped_df)
    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    return grouped_df


# This function takes a row from a DataFrame representing record with 'Start' and 'End' timestamps.
# It calculates the daily usage in hours for each date within the range from 'Start' to 'End'. 
# The function returns a list of dictionaries, each containing the original row data plus 'Date' and 'Hours' keys for every day the usage spans. If a usage period extends over multiple days, it splits the hours accordingly for each day.
def calculate_daily_usage(row):
    start_date = row['Start'].date()
    end_date = row['End'].date()
    current_date = start_date
    usage_per_day = []

    while current_date <= end_date:
        next_day = pd.Timestamp(current_date + pd.Timedelta(days=1))
        daily_end = min(row['End'], next_day)
        daily_hours = (daily_end - max(row['Start'], pd.Timestamp(current_date))).total_seconds() / 3600
        if daily_hours > 0:
            usage = row.to_dict()
            usage.update({'Date': current_date, 'Hours': daily_hours})
            usage_per_day.append(usage)
        current_date += pd.Timedelta(days=1)

    return usage_per_day




# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)