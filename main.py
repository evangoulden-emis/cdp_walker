from netmiko import ConnectHandler
import ipaddress
from getpass import getpass

CORES = [
    "10.139.2.96",
    "10.10.20.2",
]

def main():
    print("Enter username: ")
    username = input()
    print("Enter password: ")
    password = getpass()

    for core in CORES:
        with ConnectHandler(device_type='cisco_ios', ip=core, username=username, password=password) as net_connect:
            print(net_connect.find_prompt())
            core_cdp_info = net_connect.send_command("show cdp neighbor detail", use_textfsm=True)


if __name__ == "__main__":
    main()