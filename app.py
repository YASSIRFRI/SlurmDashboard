# app.py
from flask import Flask, render_template, request, redirect, url_for
import os
import subprocess
import dash
from dash import html
import dash_core_components as dcc
import pandas as pd
from dash.dependencies import Input, Output
from threading import Thread

# Load environment variables from .env file

app = Flask(__name__)

# Initialize Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Placeholder for Dash layout
dash_app.layout = html.Div()

def run_dash():
    dash_app.run_server(debug=False)

# Create a separate thread for the Dash app
dash_thread = Thread(target=run_dash)
dash_thread.start()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST'])
def dashboard():
    print("Received POST request to /dashboard")
    ssh_username = request.form['username']
    ssh_password = request.form['password']
    ssh_host="simlab-cluster.um6p.ma"
    #option = request.form['option']
    # Run collect_data.py with user-provided credentials
    command = f"python collect_data.py {ssh_host} {ssh_username} {ssh_password}"
    subprocess.run(command, shell=True)
    # Redirect to the Dash dashboard
    return redirect(url_for('dash_dashboard'))

@app.route('/dash_dashboard')
def dash_dashboard():
    print("Received GET request to /dash_dashboard")
    return dash_app.index()

# Callback to update Dash layout based on data
@dash_app.callback(
    Output('usage-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n_intervals):
    # Load data from the CSV file
    df = pd.read_csv('usage_data.csv')

    figure = {
        'data': [
            {'x': df['User'], 'y': df['UsedCPU'], 'type': 'bar', 'name': 'Used CPU Hours'},
        ],
        'layout': {
            'title': 'Usage per User',
            'xaxis': {'title': 'User'},
            'yaxis': {'title': 'Used CPU Hours'},
        }
    }

    return figure

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    dash_thread.join()
