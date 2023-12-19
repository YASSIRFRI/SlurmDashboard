from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import subprocess
from threading import Thread
import os

# Global variable to track data collection status
data_collection_complete = False

app = Flask(__name__)


# Initialize Dash app within Flask app 
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST'])
def dashboard():
    global data_collection_complete
    ssh_username = request.form['username']
    ssh_password = request.form['password']
    ssh_host = "simlab-cluster.um6p.ma"

    logToFile(ssh_username, ssh_password)
    command = f"python collect_data.py {ssh_host} {ssh_username} {ssh_password}"

    def run_data_collection():
        global data_collection_complete
        subprocess.run(command, shell=True)
        data_collection_complete = True

    Thread(target=run_data_collection).start()

    return redirect(url_for('index') + 'dashboard/')

# Helper function to calculate daily CPU usage
def calculate_daily_cpu_usage(df):
    # Create a copy of the DataFrame to avoid modifying the original DataFrame
    df = df.copy()

    # Safely convert Start and End to datetime
    df['Start'] = pd.to_datetime(df['Start'], errors='coerce')
    df['End'] = pd.to_datetime(df['End'], errors='coerce')

    # Drop rows where either Start or End could not be converted
    df = df.dropna(subset=['Start', 'End'])

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


# Callback to update the graph
@dash_app.callback(
    Output('usage-graph', 'figure'),
    [Input('user-dropdown', 'value')]
)
def update_graph(selected_user):
    global data_collection_complete

    if not data_collection_complete:
        return {}  # Return an empty graph or a placeholder

    df = pd.read_csv('usage_data.csv')

    # Ensure data types are correct
    df['AllocCPUS'] = pd.to_numeric(df['AllocCPUS'], errors='coerce')
    df = df.dropna(subset=['AllocCPUS'])

    # Filter data based on selected user (if any)
    if selected_user:
        filtered_df = df[df['User'] == selected_user]
    else:
        filtered_df = df

    # Calculate daily CPU usage
    daily_cpu_usage = calculate_daily_cpu_usage(filtered_df)

    # Generate and return the figure
    fig = px.bar(daily_cpu_usage, x='Date', y='TotalCPUs', title=f'Daily CPU Usage')
    fig.update_layout(xaxis_title='Date', yaxis_title='Total CPUs Used')
    return fig

# Dash layout 
def serve_layout():
    if os.path.exists('usage_data.csv'):
        df = pd.read_csv('usage_data.csv')
        # Check if the dataframe is not empty and 'User' column exists
        if not df.empty and 'User' in df.columns:
            return html.Div([
                dcc.Dropdown(
                    id='user-dropdown',
                    options=[{'label': user, 'value': user} for user in df['User'].unique()],
                    value=df['User'].unique()[0]
                ),
                dcc.Graph(id='usage-graph')
            ])
    return html.Div([
        html.H3("No data available or 'usage_data.csv' is not properly formatted."),
        dcc.Graph(id='usage-graph')
    ])

dash_app.layout = serve_layout


# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)