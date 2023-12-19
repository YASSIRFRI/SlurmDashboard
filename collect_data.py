import sys
import subprocess
from datetime import datetime
import pandas as pd
import paramiko
import os
from datetime import datetime, timedelta

def collect_data(ssh_host, ssh_username, ssh_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ssh_host, username=ssh_username, password=ssh_password)

        # Calculate start and end times for one year duration
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        start_time_str = start_time.strftime('%Y-%m-%d')
        end_time_str = end_time.strftime('%Y-%m-%d')

        # Run sacct command on the remote server with the specified time range
        command = f"sacct -P -o JobID,User,AllocCPUS,AllocGRES,Start,End,Elapsed --allusers --duplicates --starttime={start_time_str} --endtime={end_time_str}"
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()

        # debug=open(".log","a")
        # debug.write(result)
        # print("result : \n",result)

        # Process output and store in a CSV file
        data = [line.split('|') for line in result.strip().split('\n')[1:]]
        print("data : \n",data)
        columns = ['JobID', 'User', 'AllocCPUS', 'AllocGRES', 'Start', 'End', 'Elapsed']
        df = pd.DataFrame(data, columns=columns)
        # df['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if CSV file exists and append or create new file accordingly
        csv_file = 'usage_data.csv'
        file_exists = os.path.isfile(csv_file)
        df.to_csv(csv_file, mode='a', header=not file_exists, index=False)

        # Ensure that the number of columns matches the expected number
        #if len(data[0]) == len(columns):
        #df = pd.DataFrame(data, columns=columns)
        #df['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #df.to_csv('usage_data.csv', mode='w', header=(not df.index.any()), index=False)
        #else:
            #print(f"Unexpected number of columns in the data: {len(data[0])}")

    except Exception as e:
        print(f"Error connecting to {ssh_host}: {e}")

    finally:
        ssh.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script_name.py <ssh_host> <ssh_username> <ssh_password>")
        sys.exit(1)

    ssh_host = sys.argv[1]
    ssh_username = sys.argv[2]
    ssh_password = sys.argv[3]

    collect_data(ssh_host, ssh_username, ssh_password)

