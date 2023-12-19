# ssh_connection.py
import paramiko

def establish_ssh_connection(ssh_host, ssh_username, ssh_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ssh_host, username=ssh_username, password=ssh_password)
        return ssh
    except Exception as e:
        print(f"Error connecting to {ssh_host}: {e}")
        return None
