from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from rich import inspect


discovery_output = []
CORES = [
    "10.139.2.96",
    "TBC",
]

DISCOVERY_COMMANDS = [
    "show cdp neighbor detail",
    "show lldp neighbors detail"]

def main():
    print("Enter username: ")
    username = input()
    print("Enter password: ")
    password = getpass()

    for core in CORES:
        with ConnectHandler(device_type='cisco_ios', ip=core, username=username, password=password) as net_connect:
            rprint(net_connect.find_prompt())
            for command in DISCOVERY_COMMANDS:
                rprint(f"Sending command: {command}")
                discovery_output.append(net_connect.send_command(command, use_textfsm=True))
                rprint(discovery_output)


if __name__ == "__main__":
    main()