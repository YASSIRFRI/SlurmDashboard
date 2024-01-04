from datetime import datetime, timedelta
import pandas as pd
import os

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
    command = f"sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End --user={user} --starttime={start_time_str} --endtime={end_time_str}"
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode()
    
    # Define the expected header
    expected_header = "JobID|User|AllocCPUS|AllocGRES|Start|End"

    # Check if result contains only the header (i.e. if the result is empty)
    if result.strip() == expected_header: 
        return pd.DataFrame() 

    return preprocess_data(result)


# This function constructs and executes an sacct command to collect data for a specified user within the period [start_date, end_date]
def collect_data_datetime_based(ssh, user, start_date, end_date):
    
    # Convert start and end dates from string to datetime
    start_date = datetime.strptime(start_date[:10], "%Y-%m-%d").strftime('%Y-%m-%d')
    end_date = datetime.strptime(end_date[:10], "%Y-%m-%d").strftime('%Y-%m-%d')

    # Construct and execute the data collection command
    command = f"sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End --user={user} --starttime={start_date} --endtime={end_date}"
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode()
    
    # Define the expected header
    expected_header = "JobID|User|AllocCPUS|AllocGRES|Start|End"

    # Check if result contains only the header (i.e. if the result is empty)
    if result.strip() == expected_header: 
        return pd.DataFrame() 

    return preprocess_data(result)


# This function processes the command output and converts it into a DataFrame
def preprocess_data(result):
    df = pd.DataFrame()

    # Process output and store in a CSV file
    data = [line.split('|') for line in result.strip().split('\n')[1:]]
    # print("data : \n",data)
    columns = ['JobID', 'User', 'AllocCPUS', 'AllocGRES', 'Start', 'End']
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

    # Expanding each job
    expanded_rows = [expand_job(row) for index, row in df.iterrows()]
    df = pd.DataFrame([item for sublist in expanded_rows for item in sublist])

    # Apply formatting to the ElapsedTime column
    df['ElapsedTime'] = df['ElapsedTime'].apply(lambda x: format_timedelta(pd.to_timedelta(x)))
    
    # Convert ElapsedTime to timedelta
    df['ElapsedTime_td'] = pd.to_timedelta(df['ElapsedTime'])

    # Calculate CPUTime and GPUTime in timedelta
    df['CPUTime_td'] = df['AllocCPUS'] * df['ElapsedTime_td']
    df['GPUTime_td'] = df['NumGPUs'] * df['ElapsedTime_td']

    df['CPUTime'] = df['CPUTime_td'].apply(timedelta_to_dd_hh_mm_ss)
    df['GPUTime'] = df['GPUTime_td'].apply(timedelta_to_dd_hh_mm_ss)

    # Drop temporary timedelta columns
    df.drop(columns=['ElapsedTime_td', 'CPUTime_td', 'GPUTime_td'], inplace=True)

    # Check if CSV file exists and append or create new file accordingly
    # We do not read from the csv file. Instead we directly use the generated dataframe. These lines are kept for debugging purposes.
    # csv_file = 'usage_data.csv'
    # file_exists = os.path.isfile(csv_file)
    # df.to_csv(csv_file, mode='a', header=not file_exists, index=False)

    return df

# Function to expand the jobs into multiple rows for each day
def expand_job(row):
    start = row['Start']
    end = row['End']
    current_date = start.date()
    rows = []

    while start < end:
        next_day = (datetime.combine(current_date, datetime.min.time()) + timedelta(days=1))
        if next_day > end:
            next_day = end
        elapsed_time = next_day - start
        rows.append({
            'JobID': row['JobID'],
            'User': row['User'],
            'AllocCPUS': row['AllocCPUS'],
            'AllocGRES': row['AllocGRES'],
            'Date': current_date,
            'ElapsedTime': elapsed_time,
            'NumGPUs': row['NumGPUs']
        })
        start = next_day
        current_date += timedelta(days=1)

    return rows

# Adjusting the format of the ElapsedTime column to HH:MM:SS
def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Convert timedeltas to DD-HH:MM:SS format
def timedelta_to_dd_hh_mm_ss(td):
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}-{hours:02}:{minutes:02}:{seconds:02}"