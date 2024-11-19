import paramiko

"""
Creates an ssh client using paramiko between the app and the robot.
"""

class SSHClient:
    def __init__(self, server, username=None, password=None, port=22):
        """Init SSH connection to server etc., url changeable to username, ip etc."""
        self.port = port
        self.username = username
        self.server = server
        self.password = password
        self.client = paramiko.SSHClient()
        self.connect()

    def connect(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # "bad" security", meant for private network
        self.client.connect(self.server, username=self.username, password=self.password, port=self.port)

    def run_ssh_command(self, cmd_command):
        ssh_stdin, ssh_stdout, ssh_stderr = self.client.exec_command(cmd_command)
        print "SSH says.."
        print ssh_stdin
        print ssh_stdout
        print ssh_stderr
        print "======================"
