from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from rich import inspect



CORES = [
    "10.139.2.96",
]

DISCOVERY_COMMANDS = [
    "show cdp neighbor detail",
    "show lldp neighbors detail"]

def main():
    discovery_info = {}
    print("Enter username: ")
    username = input()
    print("Enter password: ")
    password = getpass()

    # Loop though core switches and run the discovery commands, store the json data in a list.
    for core in CORES:
        connect_to_core(core, username, password, discovery_info)

    rprint(discovery_info)
    # Loop through the list and check if the platform contains Cisco, if it does initiate another connection to this switch and perform the same discovery commands.
    for device in discovery_info.values():
        for entry in device:
            if "cisco" in entry["platform"].lower():
                connect_to_core(entry["dest_ip"], username, password, discovery_info)



def connect_to_core(core, username, password, discovery_info):
    with ConnectHandler(device_type='cisco_ios', ip=core, username=username, password=password) as net_connect:
        dev_name = net_connect.find_prompt().strip("#")
        rprint(f"Connecting to {dev_name}")
        for command in DISCOVERY_COMMANDS:
            rprint(f"Sending command: {command}")
            discovery_info[dev_name] = net_connect.send_command(command, use_textfsm=True)



if __name__ == "__main__":
    main()