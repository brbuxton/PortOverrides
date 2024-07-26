import requests
import os
import json

# Variables for user input
API_KEY = os.getenv('API_KEY')
ORG_ID = os.getenv('ORG_ID')
PORT_PROFILE = 'your_port_profile'

# Define headers
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}


def get_switch_details(serial):
    try:
        url = f'https://api.meraki.com/api/v1/devices/{serial}'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        profileId = response.json()['switchProfileId']
        networkId = response.json()['networkId']
        networkName = response.json()['name']
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    try:
        url = f'https://api.meraki.com/api/v1/devices/{serial}/switch/ports'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        switch_ports = response.json()

        return networkId, profileId, switch_ports, networkName

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


# Function to get the port overrides for a specific port profile on a switch
def get_template_profile_ports_config(configTemplateId, profileId):
    try:
        # Get the list of switch ports and their configs in a switch profile.
        url = f'https://api.meraki.com/api/v1/organizations/{ORG_ID}/configTemplates/{configTemplateId}/switch/profiles/{profileId}/ports'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        switch_ports = response.json()

        return switch_ports

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def get_template_profiles(configTemplateId):
    try:
        # Get a list of switch profiles for a template
        url = f'https://api.meraki.com/api/v1/organizations/{ORG_ID}/configTemplates/{configTemplateId}/switch/profiles'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        switch_templates = response.json()

        return switch_templates

    except requests.exceptions.RequestException:
        print(f"Error: {e}")
        return []


def get_templates():
    try:
        # Get a list of templates
        url = f'https://api.meraki.com/api/v1/organizations/{ORG_ID}/configTemplates'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        switch_templates = response.json()

        return switch_templates

    except requests.exceptions.RequestException:
        print(f"Error: {e}")
        return []


def get_port_diff(configTemplate, configSwitch):
    differences = []
    for template_port, port in zip(configTemplate, configSwitch):
        port_diff = {}
        for key in template_port:
            if template_port[key] != port.get(key):
                port_diff[key] = {'template': template_port[key], 'port': port.get(key)}
                print(port_diff)
        if port_diff:
            differences.append({'portId': template_port['portId'], 'differences': port_diff})
    print(differences)
    return differences


def get_Template_Index():
    index = {}
    try:
        for template in get_templates():
            for profile in get_template_profiles(template['id']):
                # print(profile)
                # print(profile['switchProfileId'])
                # print(template['id'])
                # index.setdefault(template['id'], []).append(profile['switchProfileId'])
                index[profile['switchProfileId']]=template['id']

    except:
        print("No templates found")
        return {}
    return index


def get_switches_in_network(networkId):
    try:
        # Get a list of templates
        url = f'https://api.meraki.com/api/v1/networks/{networkId}/devices'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        devices = response.json()
        switches = []
        for device in devices:
            try:
                print(device['serial'], device['switchProfileId'])
                switches.append([device['serial'],device['switchProfileId']])
            except KeyError:
                print("No switch")

        return switches

    except requests.exceptions.RequestException:
        print(f"Error: {e}")
        return []
    return


def list_networks():
    try:
        # Get a list of network and print it
        url = f'https://api.meraki.com/api/v1/organizations/{ORG_ID}/networks'
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        networks = response.json()

        return networks

    except requests.exceptions.RequestException:
        print(f"Error: {e}")
        return []


# Create the template index
template_index = get_Template_Index()
# print("Template Index")
# print(template_index)

# Print a list of networks
print(json.dumps(list_networks(),indent=4))

# now set the networkId to the network you want to check the diff of
networkId = 'Your Network Here'

network_switches = get_switches_in_network(networkId)
# print(network_switches)
for switch in network_switches:
    # print(switch)
    switch_details = get_switch_details(switch[0])
    # print(switch_details)
    profile_config = get_template_profile_ports_config(template_index[switch_details[1]], switch_details[1])
    # print(profile_config)
    diff = get_port_diff(profile_config, switch_details[2])

    # Convert dictionary to a pretty-printed JSON string
    pretty_json = json.dumps(diff, indent=4)

    # Write the formatted JSON string to a file
    with open(f'{switch_details[3]}_diff.json', 'w') as file:
        file.write(pretty_json)
        file.close()
