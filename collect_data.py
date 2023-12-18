import sys
import subprocess
from datetime import datetime
import pandas as pd
import paramiko

def collect_data(ssh_host, ssh_username, ssh_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ssh_host, username=ssh_username, password=ssh_password)
        # Run sacctmgr command on the remote server and capture output
        command = "sacct -p -a -o user,account,reqcpus,alloccpus"
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode()
        debug=open("output.txt","w")
        debug.write(result)
        print("result : \n",result)
        # Process output and store in a CSV file
        data = [line.split('|') for line in result.strip().split('\n')]
        print ("data : \n",data)
        columns = ['User', 'Account', 'ReqCPUS', 'AllocCPUS']
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
    df = pd.DataFrame(data_list, columns=columns + ['Timestamp'])
    df.to_csv('usage_data.csv', mode='w', header=(not df.index.any()), index=False)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script_name.py <ssh_host> <ssh_username> <ssh_password>")
        sys.exit(1)

    ssh_host = sys.argv[1]
    ssh_username = sys.argv[2]
    ssh_password = sys.argv[3]

    collect_data(ssh_host, ssh_username, ssh_password)
