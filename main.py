import json
from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Starting point(s)
network_devices = ["10.139.2.96"]

# CDP/LLDP commands
DISCOVERY_COMMANDS = {
    "cdp": "show cdp neighbor detail",
    "lldp": "show lldp neighbors detail"
}

visited_devices = set()

def get_credentials():
    print("Enter username: ", end="")
    username = input()
    password = getpass(prompt="Enter Password: ")
    return username, password


# Queue is a list of devices to be processed.
def initialize_queue(devices=None):
    if devices is None:
        nd = [network_devices[0]]
    return [{
        "ip": nd,
        "neighbor_name": "Root Device",
        "platform": "Cisco 3850",
        "device_name": "Root",
        "parent": ""  # this is the actual root of the tree
    } for ip in devices]


def connect_and_discover(device, username, password):
    ip = device["ip"]
    neighbor_name = device["neighbor_name"]
    platform = device["platform"]
    parent_node = device["parent"]

    if ip in visited_devices:
        return None

    visited_devices.add(ip)

    try:
        with ConnectHandler(device_type='cisco_ios', ip=ip, username=username, password=password) as net_connect:
            current_device_facts = get_facts_from_current_device(net_connect)
            dev_name = net_connect.find_prompt().strip("#")
            rprint(f"[green]Connected to {dev_name} ({ip})[/green]")

            current_node = {
                "ip": ip,
                "neighbor_name": neighbor_name,
                "platform": platform,
                "device_name": dev_name,
                "neighbors": {}
            }

            parent_node[ip] = current_node

            discovered_neighbors = []

            for cmd in DISCOVERY_COMMANDS.values():
                rprint(f"Sending command: '{cmd}' to {dev_name} ({ip})")
                neighbors = net_connect.send_command(cmd, use_textfsm=True)

                if isinstance(neighbors, list):
                    for neighbor in neighbors:
                        mgmt_ip = neighbor.get("mgmt_address")
                        neighbor_name = neighbor.get("neighbor_name")
                        platform = neighbor.get("platform", "Unknown")

                        if mgmt_ip and "cisco" in platform.lower() and mgmt_ip not in visited_devices:
                            discovered_neighbors.append({
                                "ip": mgmt_ip,
                                "neighbor_name": neighbor_name,
                                "platform": platform,
                                "parent": current_node["neighbors"]
                            })

            return (current_device_facts, discovered_neighbors)

    except NetmikoTimeoutException:
        rprint(f"[red]Timeout connecting to {neighbor_name} - {ip} - {platform}[/red]")
    except NetmikoAuthenticationException:
        rprint(f"[red]Authentication failed for {neighbor_name} - {ip} - {platform}[/red]")
    except Exception as e:
        rprint(f"[red]Unexpected error connecting to {neighbor_name} - {ip} - {platform}: {e}[/red]")

    return None

def write_tree_to_file(tree, filename="discovery_tree.json"):
    with open(filename, "w") as f:
        json.dump(tree, f, indent=4)
    rprint(f"[blue]Discovery complete. Tree written to {filename}[/blue]")


def main():
    username, password = get_credentials()
    discovery_tree = {}  # root of the tree

    device_queue = initialize_queue()

    while device_queue:
        device = device_queue.pop(0)
        device_facts, new_neighbors = connect_and_discover(device, username, password)
        if new_neighbors:
            device_queue.extend(new_neighbors)
            
    write_tree_to_file(discovery_tree)


def get_facts_from_current_device(net_connect):
    facts = {}
    facts['hostname'] = net_connect.find_prompt().strip("#")
    version_output = net_connect.send_command("show version", use_textfsm=True)
    if isinstance(version_output, list) and version_output:
        facts.update(version_output[0])
    return facts


if __name__ == "__main__":
    main()
