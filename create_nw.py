import requests
import json
import time
import math
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# GNS3 Server Configuration
GNS3_SERVER = "http://localhost:3080"
PROJECT_NAME = "Auto_Configured_VPCS_Network2"
SWITCH_TEMPLATE = "Ethernet switch"
VPCS_TEMPLATE = "VPCS"
SWITCH_PORTS = 8  # Standard 8-port Ethernet switch
DEVICES_PER_SWITCH = SWITCH_PORTS - 1  # Reserve 1 port for uplink
TARGET_DEVICES = 50

# Network Configuration
BASE_IP = "192.168.1."
SUBNET_MASK = "255.255.255.0"
GATEWAY_IP = BASE_IP + "1"

class GNS3NetworkBuilder:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.project_id = None
        self.nodes = {}
        self.links = []
        self.template_ids = {}
        self.successful_devices = 0
        self.startup_scripts = {}

    def create_project(self):
        """Create a new GNS3 project"""
        payload = {
            "name": PROJECT_NAME,
            "auto_close": False,
            "auto_open": True,
            "auto_start": True  # Auto-start all devices
        }
        
        response = self.session.post(
            f"{GNS3_SERVER}/v2/projects",
            json=payload
        )
        
        if response.status_code == 201:
            self.project_id = response.json()["project_id"]
            print(f"Project '{PROJECT_NAME}' created successfully")
            time.sleep(2)  # Wait for project to initialize
            return self.project_id
        raise Exception(f"Failed to create project: {response.text}")

    def get_template_id(self, template_name):
        """Get template ID by name"""
        response = self.session.get(f"{GNS3_SERVER}/v2/templates")
        if response.status_code != 200:
            raise Exception(f"Failed to get templates: {response.text}")
            
        for template in response.json():
            if template["name"].lower() == template_name.lower():
                return template["template_id"]
        raise Exception(f"Template '{template_name}' not found")

    def create_node(self, name, template_id, node_type, x, y, properties=None):
        """Create a single node with error handling"""
        try:
            payload = {
                "name": name,
                "node_type": node_type,
                "compute_id": "local",
                "template_id": template_id,
                "x": int(round(x)),
                "y": int(round(y)),
                "properties": properties if properties else {}
            }
            
            response = self.session.post(
                f"{GNS3_SERVER}/v2/projects/{self.project_id}/nodes",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                node_data = response.json()
                self.nodes[name] = node_data
                print(f"Created {name} at ({payload['x']}, {payload['y']})")
                return node_data
            print(f"Warning: Failed to create {name}: {response.text}")
            return None
        except Exception as e:
            print(f"Warning: Failed to create {name}: {str(e)}")
            return None

    def create_link(self, node1, port1, node2, port2):
        """Create a link between two nodes with error handling"""
        try:
            if node1 not in self.nodes or node2 not in self.nodes:
                print(f"Warning: Cannot create link - nodes missing: {node1} or {node2}")
                return None
                
            payload = {
                "nodes": [
                    {
                        "node_id": self.nodes[node1]["node_id"],
                        "adapter_number": 0,
                        "port_number": port1
                    },
                    {
                        "node_id": self.nodes[node2]["node_id"],
                        "adapter_number": 0,
                        "port_number": port2
                    }
                ]
            }
            
            response = self.session.post(
                f"{GNS3_SERVER}/v2/projects/{self.project_id}/links",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                self.links.append(response.json())
                print(f"Created link: {node1}:{port1} <-> {node2}:{port2}")
                return response.json()
            print(f"Warning: Failed to create link {node1}:{port1} <-> {node2}:{port2}: {response.text}")
            return None
        except Exception as e:
            print(f"Warning: Failed to create link: {str(e)}")
            return None

    def configure_vpcs(self, device_name, ip_address):
        """Create startup script for VPCS device"""
        script = f"""
        ip {ip_address} {SUBNET_MASK} {GATEWAY_IP}
        save
        """
        self.startup_scripts[device_name] = script

    def upload_configs(self):
        """Upload configurations to all VPCS devices"""
        for device_name, script in self.startup_scripts.items():
            if device_name in self.nodes:
                node_id = self.nodes[device_name]["node_id"]
                url = f"{GNS3_SERVER}/v2/projects/{self.project_id}/nodes/{node_id}/files/startup.vpc"
                response = self.session.post(
                    url,
                    data=script,
                    headers={"Content-Type": "text/plain"}
                )
                if response.status_code == 204:
                    print(f"Configured {device_name}")
                else:
                    print(f"Failed to configure {device_name}: {response.text}")

    def build_network(self):
        """Build and auto-configure the complete network"""
        try:
            print("Starting auto-configured network construction...")
            
            # Create project
            self.create_project()
            
            # Get template IDs
            switch_template_id = self.get_template_id(SWITCH_TEMPLATE)
            vpcs_template_id = self.get_template_id(VPCS_TEMPLATE)
            
            # Create core switch (will act as gateway)
            core_switch = self.create_node(
                "Core-Switch", 
                switch_template_id, 
                "ethernet_switch", 
                0, -200
            )
            if not core_switch:
                print("Failed to create core switch, aborting")
                return
            
            # Create access switches and VPCS devices
            device_count = 0
            successful_switches = 0
            
            for switch_num in range(1, (TARGET_DEVICES // DEVICES_PER_SWITCH) + 2):
                # Position switches in a circle around core
                angle = 2 * math.pi * (switch_num-1) / ((TARGET_DEVICES // DEVICES_PER_SWITCH) + 1)
                x = 400 * math.cos(angle)
                y = 400 * math.sin(angle)
                
                switch_name = f"Access-Switch-{switch_num}"
                switch_node = self.create_node(
                    switch_name, 
                    switch_template_id, 
                    "ethernet_switch", 
                    x, y
                )
                if not switch_node:
                    continue
                
                # Connect to core switch
                if not self.create_link("Core-Switch", switch_num, switch_name, 0):
                    continue
                
                successful_switches += 1
                
                # Create VPCS devices on this switch
                for port in range(1, SWITCH_PORTS):
                    if device_count >= TARGET_DEVICES:
                        break
                    
                    device_count += 1
                    # Position devices around their switch
                    pc_angle = 2 * math.pi * (port-1) / (SWITCH_PORTS-1)
                    pc_x = x + 150 * math.cos(pc_angle)
                    pc_y = y + 150 * math.sin(pc_angle)
                    
                    pc_name = f"PC-{device_count}"
                    pc_ip = BASE_IP + str(device_count + 10)  # IPs start at .11
                    
                    # Create VPCS with auto-configuration
                    pc_node = self.create_node(
                        pc_name, 
                        vpcs_template_id, 
                        "vpcs", 
                        pc_x, pc_y,
                        properties={"console_auto_start": True}
                    )
                    if not pc_node:
                        continue
                    
                    if self.create_link(switch_name, port, pc_name, 0):
                        self.successful_devices += 1
                        self.configure_vpcs(pc_name, pc_ip)
            
            # Upload all configurations
            self.upload_configs()
            
            print("\nNetwork construction and configuration completed!")
            print(f"Successfully created and configured:")
            print(f"- 1 Core switch")
            print(f"- {successful_switches} Access switches")
            print(f"- {self.successful_devices} VPCS devices")
            print(f"- {len(self.links)} links")
            
            print(f"""
            Network is ready to use!
            All VPCS devices are pre-configured with:
            - IP range: {BASE_IP}11 to {BASE_IP}{10+self.successful_devices}
            - Subnet mask: {SUBNET_MASK}
            - Gateway: {GATEWAY_IP}
            
            To test connectivity:
            1. Open GNS3 and wait for all devices to start
            2. Open console on any VPCS device
            3. Run: ping {BASE_IP}12
            """)
            
        except Exception as e:
            print(f"Fatal error: {str(e)}")
            if self.project_id:
                print(f"Project ID {self.project_id} was created")

if __name__ == "__main__":
    builder = GNS3NetworkBuilder()
    builder.build_network()