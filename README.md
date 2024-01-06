# CPU & GPU Usage Dashboard


## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Data Processing with Pandas](#data-processing-with-pandas)
- [How to Use](#how-to-use)


## Introduction
This project is designed to provide an efficient way to monitor and display the usage of resources on the UM6P SimLab cluster. It allows users to connect via SSH and retrieve data about CPU/GPU usage.

## Features
- **Login Page:** Secure entry point requiring username and password.
![Login](images/Login.png)
- **SSH Connection:** Connects to SimLab using SSH for data retrieval.
![Dashboard](images/Dashboard.png)
- **User Dropdown Menu:** Displays all users of the cluster, allowing for specific user analysis.
- **Timeframe Filtering:** Offers predefined timeframes (e.g., 1 month ago, 2 months ago, ..., up to 1 year ago) or a custom timeframe.
![Custom Timeframe](images/Dashboard.png)
![Predefined Timeframes](images/PredefinedTimeframe.png)
- **Visualization Options:** Choose between two plots:
    - Number of CPUs/GPUs used
    - Number of hours of CPU/GPU usage

![Option 1](images/Option1.png)
![Option 2](images/Option2.png)



## Data Processing with Pandas

Upon user selection of a specific user and timeframe, the application undertakes the following data processing steps:

1. **Data Retrieval:** Utilizes the command `sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End --user={user} --starttime={start_date} --endtime={end_date}` to collect the relevant data from the SimLab cluster.

2. **Handling No Data Scenario:** If no data is available for the chosen user within the specified period, the system displays an appropriate message to inform the user about the absence of data.

3. **Data Preprocessing:**
    - **Filtering Batch Entries:** Eliminates batch entries from the collected dataset.
    - **Extracting CPU and GPU Information:** Retrieves the number of GPUs and CPUs for each job.
    - **Job Duration Segmentation:** For each job entry, the system dissects it into multiple rows, corresponding to individual days within the job's duration. Each new row includes fields like 'JobID', 'User', 'AllocCPUS', 'AllocGRES', 'Date', 'ElapsedTime', and 'NumGPUs'. The 'Date' field signifies each day the job runs, 'ElapsedTime' denotes the duration of that day's segment of the job, while the other fields retain the same values as the original job entry.
    - **Calculating CPUTime and GPUTime:** Derives the CPU and GPU times for each day.
    - **Aggregation:** Groups the data by day and computes the sums:
        - For the first plot: The number of CPUs/GPUs for each day.
        - For the second plot: The CPU/GPU times of each day.

These data processing steps enable the creation of accurate visual representations, facilitating a comprehensive analysis of resource usage over the selected timeframe for the specified user on the SimLab cluster.



## How to Use
1. **Launching the Application:** Navigate to the application folder and execute the command `python app.py` to initiate the application.
2. **Logging In:** Enter your SimLab credentials to establish a secure connection.
3. **User and Timeframe Selection:** Utilize the dropdown menu to select a specific user and define the timeframe for analysis.
4. **Plot Selection:** Choose the desired plot type to visualize resource usage data effectively.
5. **Logging Out:** Securely exit the application upon completion of analysis.
