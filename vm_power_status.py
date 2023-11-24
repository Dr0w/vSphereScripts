import csv
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import getpass
import ssl

# Disable SSL verification
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Connect to the vCenter Server
print('.-=vSphere Last Power Off/On Status Logger=-.')
server = input('Enter hostname(host.domain.xyz): ')
username = input('Enter your username: ')
password = getpass.getpass(prompt='Enter your password: ')
service_instance = SmartConnect(host=server, user=username, pwd=password, port=443, sslContext=ssl_context)

if not service_instance:
    raise SystemExit("Unable to connect to the vCenter Server with the provided credentials.")

# List all VMs inside the vCenter Server (depends on user access rights)
content = service_instance.RetrieveContent()
vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

# Specify the output CSV file name
csv_file = 'vm_power_status_list.csv'


# Retrieve the last power on/off task for a VM
def get_last_power_event(vm_outer):
    event_manager = content.eventManager
    event_filter_spec = vim.event.EventFilterSpec()
    event_filter_spec.entity = vim.event.EventFilterSpec.ByEntity(entity=vm_outer, recursion="self")
    events = event_manager.QueryEvents(event_filter_spec)
    last_power_on_event_outer = None
    last_power_off_event_outer = None
    for event in events:
        if isinstance(event, vim.event.VmPoweredOnEvent) and (
                not last_power_on_event_outer or event.createdTime > last_power_on_event_outer.createdTime):
            last_power_on_event_outer = event
        if isinstance(event, vim.event.VmPoweredOffEvent) and (
                not last_power_off_event_outer or event.createdTime > last_power_off_event_outer.createdTime):
            last_power_off_event_outer = event
    return last_power_on_event_outer, last_power_off_event_outer


# Extract the keys
header = ["VM Name", "Power State", "Last Power On Task Time", "Last Power Off Task Time"]

# Write the list of VMs and task information to the CSV file
with open(csv_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=header)
    writer.writeheader()
    for vm in vm_list.view:
        power_state = "POWERED ON" if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn \
            else "POWERED OFF"
        last_power_on_event, last_power_off_event = get_last_power_event(vm)
        writer.writerow({
            "VM Name": vm.name,
            "Power State": power_state,
            "Last Power On Task Time": last_power_on_event.createdTime.strftime(
                "%Y-%m-%d %H:%M:%S") if last_power_on_event else "N/A",
            "Last Power Off Task Time": last_power_off_event.createdTime.strftime(
                "%Y-%m-%d %H:%M:%S") if last_power_off_event else "N/A",
        })

# Disconnect from the vCenter Server
Disconnect(service_instance)
