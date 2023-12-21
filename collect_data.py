from datetime import datetime, timedelta
import pandas as pd

# Function to extract GPU count
def extract_gpu_count(gres_value):
    if pd.isna(gres_value):
        return 0
    elif 'gpu:' in gres_value:
        return int(gres_value.split(':')[-1])
    else:
        return 0
    
    
# This function calculates the start and end times based on the number of days specified.
# It constructs and executes an sacct command to collect data for a specified user within the timeframe. 
def collect_data_days_based(ssh, user, days=30):
    
    # Calculate start and end times for the specified duration
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    start_time_str = start_time.strftime('%Y-%m-%d')
    end_time_str = end_time.strftime('%Y-%m-%d')

    # Construct and execute the data collection command
    command = f"sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End,Elapsed --user={user} --starttime={start_time_str} --endtime={end_time_str}"
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode()

    return preprocess_data(result)


# This function constructs and executes an sacct command to collect data for a specified user within the period [start_date, end_date]
def collect_data_datetime_based(ssh, user, start_date, end_date):
    
    # Convert start and end dates from string to datetime
    start_date = datetime.strptime(start_date[:10], "%Y-%m-%d").strftime('%Y-%m-%d')
    end_date = datetime.strptime(end_date[:10], "%Y-%m-%d").strftime('%Y-%m-%d')

    # Construct and execute the data collection command
    command = f"sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End,Elapsed --user={user} --starttime={start_date} --endtime={end_date}"
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode()

    return preprocess_data(result)


# This function processes the command output and converts it into a DataFrame
def preprocess_data(result):
    # Process output and store in a CSV file
    data = [line.split('|') for line in result.strip().split('\n')[1:]]
    # print("data : \n",data)
    columns = ['JobID', 'User', 'AllocCPUS', 'AllocGRES', 'Start', 'End', 'Elapsed']
    df = pd.DataFrame(data, columns=columns)

    # Filter out batch entries
    df = df[df['User'] != ""]

    # Convert Start and End to datetime
    df['Start'] = pd.to_datetime(df['Start'], errors='coerce')
    df['End'] = pd.to_datetime(df['End'], errors='coerce')
    
    # Drop rows where either Start or End could not be converted
    df = df.dropna(subset=['Start', 'End'])

    # Ensure data types are correct
    df['AllocCPUS'] = pd.to_numeric(df['AllocCPUS'], errors='coerce')
    df = df.dropna(subset=['AllocCPUS'])

    # Apply the function to create a new column
    df['NumGPUs'] = df['AllocGRES'].apply(extract_gpu_count)

    # Check if CSV file exists and append or create new file accordingly
    # csv_file = 'usage_data.csv'
    # file_exists = os.path.isfile(csv_file)
    # df.to_csv(csv_file, mode='a', header=not file_exists, index=False)

    return df
