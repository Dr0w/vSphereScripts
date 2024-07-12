import csv
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import getpass
import ssl
from tqdm import tqdm

# Disable SSL verification
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Connect to the vCenter Server
print('.-=vSphere VM Power On Script=-.')
server = input('Enter hostname(host.domain.xyz): ')
username = input('Enter your username: ')
password = getpass.getpass(prompt='Enter your password: ')
service_instance = SmartConnect(host=server, user=username, pwd=password, port=443, sslContext=ssl_context)

if not service_instance:
    raise SystemExit("Unable to connect to the vCenter Server with the provided credentials.")

# List all VMs inside the vCenter Server (depends on user access rights)
content = service_instance.RetrieveContent()
vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

# Specify the input CSV file name
input_csv_file = 'vm_list.csv'

# Read the list of VM names from the CSV file
vm_names_to_power_on = []
with open(input_csv_file, mode='r', newline='') as file:
    reader = csv.DictReader(file)
    if 'VM Name' not in reader.fieldnames:
        raise KeyError("The CSV file does not contain the 'VM Name' column.")
    for row in reader:
        vm_names_to_power_on.append(row['VM Name'])

# Power on the VMs
print("Starting to powering on VMs:")
for vm in tqdm(vm_list.view, desc="Powering on VMs"):
    if vm.name in vm_names_to_power_on:
        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
            print(f"Powering on VM: {vm.name}")
            task = vm.PowerOn()
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                pass
            if task.info.state == vim.TaskInfo.State.success:
                print(f"VM {vm.name} powered on successfully.")
            else:
                print(f"Failed to power on VM {vm.name}: {task.info.error}")
        else:
            print(f"VM {vm.name} is already powered on.")

print("Operation finished. Disconnecting...")
# Disconnect from the vCenter Server
Disconnect(service_instance)
