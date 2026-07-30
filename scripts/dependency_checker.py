import sys
import re
import requests
from requests.auth import HTTPBasicAuth

BIGIP_HOST = sys.argv[1]
USER = sys.argv[2]
PASS = sys.argv[3]
IRULE_FILE = sys.argv[4]

BASE_URL = f"https://{BIGIP_HOST}/mgmt/tm"
auth = HTTPBasicAuth(USER, PASS)
requests.packages.urllib3.disable_warnings()

def verify_dependencies():
    with open(IRULE_FILE) as f:
        content = f.read()

    # Extract Pools and Classes
    pools = set(re.findall(r'pool\s+([/a-zA-Z0-9_\-]+)', content))
    classes = set(re.findall(r'class\s+match\s+.*?\s+equals\s+([a-zA-Z0-9_\-]+)', content))

    missing = 0

    # Verify Pools
    for pool in pools:
        # Format REST URI path
        formatted_pool = pool.replace('/', '~') if pool.startswith('/') else f"~Common~{pool}"
        url = f"{BASE_URL}/ltm/pool/{formatted_pool}"
        res = requests.get(url, auth=auth, verify=False)
        if res.status_code != 200:
            print(f"[MISSING DEPENDENCY] Pool '{pool}' referenced in iRule does not exist on BIG-IP.")
            missing += 1

    # Verify Data Groups
    for dg in classes:
        url = f"{BASE_URL}/ltm/data-group/internal/~Common~{dg}"
        res = requests.get(url, auth=auth, verify=False)
        if res.status_code != 200:
            print(f"[MISSING DEPENDENCY] Data Group '{dg}' referenced in iRule does not exist on BIG-IP.")
            missing += 1

    return missing == 0

if __name__ == "__main__":
    sys.exit(0 if verify_dependencies() else 1)