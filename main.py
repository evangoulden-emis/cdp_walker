from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from rich import inspect
from pprint import pprint as pp


CORES = [
    "10.139.2.96",
]

DISCOVERY_COMMANDS = {
    "cdp" : "show cdp neighbor detail",
    "lldp": "show lldp neighbors detail"
}
def main():
    discovery_info = {}
    print("Enter username: ")
    username = input()
    print("Enter password: ")
    password = getpass()

    # Loop though core switches and run the discovery commands, store the json data in a list.
    for core in CORES:
        connect_to_core(core, username, password, discovery_info)

    # rprint(discovery_info)
    # pp(discovery_info)
    # pp(inspect(discovery_info))

    # Loop through the list and check if the platform contains Cisco, if it does initiate another connection to this switch and perform the same discovery commands.
    for device, neighbors in discovery_info.items():
        for neighbor in neighbors:
            local_int = neighbor.get('local_interface')
            neighbor_name = neighbor.get('neighbor_name')
            mgmt_ip = neighbor.get('mgmt_address')
            platform = neighbor.get('platform')
            print(f"  Local Interface: {local_int}")
            print(f"  Neighbor Name: {neighbor_name}")
            print(f"  Management IP: {mgmt_ip}")
            print(f"  Platform: {platform}")
            print("---")


def connect_to_core(core, username, password, discovery_info):
    with ConnectHandler(device_type='cisco_ios', ip=core, username=username, password=password) as net_connect:
        dev_name = net_connect.find_prompt().strip("#")
        rprint(f"Connecting to {dev_name}")
        for k,v in DISCOVERY_COMMANDS.items():
            rprint(f"Sending command: {v}")
            discovery_info[dev_name + "_" + k] = net_connect.send_command(v, use_textfsm=True)



if __name__ == "__main__":
    main()