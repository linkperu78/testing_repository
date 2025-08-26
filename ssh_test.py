import paramiko

def legacy_ssh_command(host: str, username: str, password: str, command: str):
    """
    Connects to a legacy SSH server using Paramiko and executes a command.
    Supports old algorithms like diffie-hellman-group1-sha1 and ssh-dss.
    """

    # Add old / weak algorithms explicitly
    paramiko.transport.Transport._preferred_kex = (
        'diffie-hellman-group1-sha1',
        'diffie-hellman-group14-sha1',
        'diffie-hellman-group-exchange-sha1',
    )
    paramiko.transport.Transport._preferred_keys = (
        'ssh-rsa',
        'ssh-dss',
    )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False,
        )

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        return output.strip(), error.strip()

    finally:
        client.close()


# Example usage
if __name__ == "__main__":
    host = "192.168.19.23"
    username = "admin"
    password = "your_password_here"
    command = "show version"  # replace with a command your device understands

    out, err = legacy_ssh_command(host, username, password, command)
    print("OUTPUT:\n", out)
    print("ERROR:\n", err)
