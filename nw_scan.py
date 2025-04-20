import requests
import time
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class GNS3NetworkScanner:
    def __init__(self):
        self.server = "http://localhost:3080"
        self.session = requests.Session()
        self.session.verify = False
        
    def get_network_stats(self):
        projects = self.session.get(f"{self.server}/v2/projects").json()
        for project in projects:
            if project["name"] == "AI-Monitored-Network":
                nodes = self.session.get(
                    f"{self.server}/v2/projects/{project['project_id']}/nodes"
                ).json()
                
                stats = []
                for node in nodes:
                    node_stats = {
                        "name": node["name"],
                        "type": node["node_type"],
                        "cpu": self._get_random_metric(0, 100),
                        "memory": self._get_random_metric(0, 100),
                        "latency": self._get_random_metric(1, 50),
                        "packet_loss": self._get_random_metric(0, 5),
                        "errors": self._get_random_metric(0, 1)
                    }
                    stats.append(node_stats)
                return stats
        return []
    
    def _get_random_metric(self, min_val, max_val):
        return round(min_val + (max_val - min_val) * np.random.random(), 2)

if __name__ == "__main__":
    scanner = GNS3NetworkScanner()
    print(scanner.get_network_stats())