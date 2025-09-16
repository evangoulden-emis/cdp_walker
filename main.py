import json
from netmiko import ConnectHandler
from getpass import getpass
from rich import print as rprint
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Starting point(s)
root_device = "10.139.2.96"


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
        nd = root_device
    return [{
        "mgmt_address": nd,
        "neighbor_name": "Root Device",
        "platform": "Cisco 3850",
        "hostname": "Root",
        "parent": ""  # this is the actual root of the tree
    }]


def connect_and_discover(netconnect):

    if netconnect.host in visited_devices:
        return None

    visited_devices.add(netconnect.host)

    try:
            dev_name = netconnect.find_prompt().strip("#")
            rprint(f"[green]Connected to {dev_name} ({netconnect.host})[/green]")

            discovered_neighbors = []

            for cmd in DISCOVERY_COMMANDS.values():
                rprint(f"Sending command: '{cmd}' to {dev_name} ({netconnect.host})")
                neighbors = netconnect.send_command(cmd, use_textfsm=True)

                if isinstance(neighbors, list):
                    for neighbor in neighbors:
                        if neighbor['mgmt_address'] and neighbor['mgmt_address'] not in visited_devices:
                            discovered_neighbors.append(neighbor)

            return discovered_neighbors

    except NetmikoTimeoutException:
        rprint(f"[red]Timeout connecting to {netconnect.host} - {netconnect.host}[/red]")
    except NetmikoAuthenticationException:
        rprint(f"[red]Authentication failed for {netconnect.host} - {netconnect.host}[/red]")
    except Exception as e:
        rprint(f"[red]Unexpected error connecting to {netconnect.host} - {netconnect.host} -: {e}[/red]")

    return None

def write_tree_to_file(tree, filename="discovery_tree.json"):
    with open(filename, "w") as f:
        json.dump(tree, f, indent=4)
    rprint(f"[blue]Discovery complete. Tree written to {filename}[/blue]")


def main():
    username, password = get_credentials()
    discovery_tree = {}  # root of the tree
    device_fact_list = {}

    device_queue = initialize_queue()

    while device_queue:
        netconnect = create_connection_handler(device_queue.pop(0), username=username, password=password)
        if netconnect is not None:
            device_facts = get_facts_from_current_device(netconnect)
            rprint(device_facts)
            device_fact_list[device_facts['hostname']] = device_facts
            new_neighbors = connect_and_discover(netconnect)
            if new_neighbors:
                device_fact_list[device_facts['hostname']]['neighbors'] = new_neighbors
                device_queue.extend(new_neighbors)
            netconnect.disconnect()            
        else:
            rprint("[red]Failed to create connection handler. Skipping device.[/red]")
        
    # Write the discovery tree to a file once all devices have been processed.
    write_tree_to_file(device_fact_list)


def get_facts_from_current_device(netconnect):
    facts = {}
    facts['hostname'] = netconnect.find_prompt().strip("#")
    version_output = netconnect.send_command("show version", use_textfsm=True)
    if isinstance(version_output, list) and version_output:
        facts.update(version_output[0])
    return facts


def create_connection_handler(device, username=None, password=None):
    try:
        return ConnectHandler(
            device_type='cisco_ios',
            host=device['mgmt_address'],
            username=username,
            password=password
        )
    except NetmikoTimeoutException:
        rprint(f"[red]Timeout connecting to {device.get('mgmt_address')} - {device.get('hostname')}[/red]")
    except NetmikoAuthenticationException:
        rprint(f"[red]Authentication failed for {device.get('mgmt_address')} - {device.get('hostname')}[/red]")
    except Exception as e:
        rprint(f"[red]Unexpected error connecting to {device.get('mgmt_address')} - {device.get('hostname')} -: {e}[/red]")
    return None


if __name__ == "__main__":
    main()
