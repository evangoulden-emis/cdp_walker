from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from rich import inspect
from pprint import pprint as pp
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

network_devices = [
    "10.139.2.96",
]

DISCOVERY_COMMANDS = {
    "cdp" : "show cdp neighbor detail",
    "lldp": "show lldp neighbors detail"
}

visited_devices = set()

def main():
    discovery_info = {}
    visited_devices.clear()

    print("Enter username: ", end="")
    username = input()
    password = getpass(prompt="Enter Password: ")

    for network_device in network_devices:
        connect_to_nd(network_device, username, password, discovery_info, neighbor_name="Root Device")

    for _, neighbors in discovery_info.items():
        for neighbor in neighbors:
            local_int = neighbor.get('local_interface')
            neighbor_name = neighbor.get('neighbor_name')
            mgmt_ip = neighbor.get('mgmt_address')
            platform = neighbor.get('platform')
            print("   Neighbor Details:")
            print("---------------")
            print(f"  Local Interface: {local_int}")
            print(f"  Neighbor Name: {neighbor_name}")
            print(f"  Management IP: {mgmt_ip}")
            print(f"  Platform: {platform}")
            print("---------------")

            if "cisco" in platform.lower() and mgmt_ip not in visited_devices:
                connect_to_nd(mgmt_ip, username, password, discovery_info, neighbor_name, platform=platform)

            print("Device Info Size: ", len(discovery_info))
    
    # Write the discovery_info to a file
    with open("discovery_info.txt", "w") as f:
        pp(discovery_info, stream=f)
        
            

def connect_to_nd(network_device, username, password, discovery_info, neighbor_name, platform="Unknown"):
    if network_device in visited_devices:
        rprint(f"[yellow]Already visited {network_device}, skipping.[/yellow]")
        return

    visited_devices.add(network_device)
    temp_discovery_info = {}

    try:
        with ConnectHandler(device_type='cisco_ios', ip=network_device, username=username, password=password) as net_connect:
            dev_name = net_connect.find_prompt().strip("#")
            rprint(f"[green]Connecting to {dev_name}[/green]")

            for k, v in DISCOVERY_COMMANDS.items():
                rprint(f"Sending command: {v}")
                temp_discovery_info[dev_name + "_" + k] = net_connect.send_command(v, use_textfsm=True)

            check_duplicate(temp_discovery_info, discovery_info)

    except NetmikoTimeoutException:
        rprint(f"[red]Timeout connecting to {neighbor_name} - {network_device} - {platform} [/red]")
        log_error(f"Timeout connecting to {neighbor_name} - {network_device} - {platform}")
    except NetmikoAuthenticationException:
        rprint(f"[red]Authentication failed for {neighbor_name} - {network_device} - {platform} [/red]")
        log_error(f"Authentication failed for {neighbor_name} - {network_device} - {platform}")
    except Exception as e:
        rprint(f"[red]Unexpected error connecting to {neighbor_name} - {network_device} - {platform}: {e}[/red]")
        log_error(f"Unexpected error connecting to {neighbor_name} - {network_device} - {platform}: {e}")



def check_duplicate(temp_discovery_info, discovery_info):
    for device, new_neighbors in temp_discovery_info.items():
        if device not in discovery_info:
            discovery_info[device] = new_neighbors
        else:
            existing_neighbors = discovery_info[device]
            for neighbor in new_neighbors:
                if neighbor not in existing_neighbors:
                    existing_neighbors.append(neighbor)
                    
# Write errors to a log file
def log_error(message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(message + "\n")



if __name__ == "__main__":
    main()