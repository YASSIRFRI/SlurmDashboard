from flask import Flask, render_template, request, redirect
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from threading import Thread
from ssh_connection import establish_ssh_connection
from collect_data import collect_data
import plotly.graph_objs as go

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
        dcc.Dropdown(
            id='user-dropdown',
            options=[{'label': user, 'value': user} for user in slurm_users],
            value=None
        ),
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
        dcc.Graph(id='usage-graph')
    ])

# Set the layout to the serve_layout function
dash_app.layout = serve_layout


# Helper function to calculate daily CPU usage
def calculate_daily_cpu_usage(df):
    # Create a copy of the DataFrame to avoid modifying the original DataFrame
    df = df.copy()

    # Initialize a DataFrame to store daily CPU usage
    daily_cpu_usage = pd.DataFrame()

    for _, row in df.iterrows():
        # Generate a date range for each row
        date_range = pd.date_range(start=row['Start'].date(), end=row['End'].date(), freq='D')
        temp_df = pd.DataFrame({'Date': date_range, 'TotalCPUs': [row['AllocCPUS']] * len(date_range)})
        daily_cpu_usage = pd.concat([daily_cpu_usage, temp_df], ignore_index=True)

    # Aggregate total CPUs per day
    daily_cpu_usage['TotalCPUs'] = pd.to_numeric(daily_cpu_usage['TotalCPUs'], errors='coerce')
    daily_cpu_usage = daily_cpu_usage.groupby('Date')['TotalCPUs'].sum().reset_index()
    return daily_cpu_usage


# Callback to update the graph based on user and timeframe selection
@dash_app.callback(
    Output('usage-graph', 'figure'),
    [Input('user-dropdown', 'value'), Input('timeframe-dropdown', 'value')]
)
def update_graph(selected_user, selected_timeframe):
    global ssh
    if not selected_user or not ssh:
        return go.Figure()  # Return an empty figure if no user is selected or if SSH connection fails

    # Collect data for the selected user and timeframe
    dataframe = collect_data(ssh, selected_user, selected_timeframe)

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

    # Calculate daily CPU usage (if needed)
    daily_cpu_usage = calculate_daily_cpu_usage(dataframe)

    # Generate and return the bar chart figure
    fig = px.bar(daily_cpu_usage, x='Date', y='TotalCPUs', title='Daily CPU Usage')
    fig.update_layout(xaxis_title='Date', yaxis_title='Total CPUs Used')
    return fig



# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)