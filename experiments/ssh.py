import paramiko
from scp import SCPClient, SCPException
from pathlib import Path

def start_cep_application(client, application):
    cmd = 'sudo systemctl start {}'.format(application)
    stdin, stdout, stderr = client.exec_command(cmd)

def stop_cep_application(client, application):
    cmd = 'sudo systemctl stop {}'.format(application)
    stdin, stdout, stderr = client.exec_command(cmd)

def start_nmon(client):
    cmd = 'nmon -t -f -s 5 -c 400'
    stdin, stdout, stderr = client.exec_command(cmd)

def kill_application(client, application):
    stdin, stdout, stderr = client.exec_command('pgrep {}'.format(application))
    output = ''
    for line in stdout.readlines():
        output += line
    pid = output.strip('\n')
    client.exec_command('kill -9 {}'.format(pid))

def start_ssh_connection(hostname, user):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, 22, user)
    return client

def get_logs(client, dir, pattern, output):
    stdin, stdout, stderr = client.exec_command('ls {}/{}'.format(dir, pattern))
    result = stdout.read().split()
    Path(output).mkdir(parents=True, exist_ok=True)
    scp = SCPClient(client.get_transport())
    for file in result:
        file_get = scp.get(file, output)
    client.exec_command('cd {} && rm {}'.format(dir, pattern))
    scp.close()

def get_number_of_starts_cep(client):
    cmd = 'journalctl -u ddos-10s.service | grep Running | wc -l'
    stdin, stdout, stderr = client.exec_command(cmd)
    output = ''
    for line in stdout.readlines():
        output += line
    number = output.strip('\n')
    return int(number)
