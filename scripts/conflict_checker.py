import sys
import json
import re

def check_vs_conflicts(mapping_file):
    with open(mapping_file) as f:
        data = json.load(f)
    
    irules = data["attached_irules"]
    has_responded_checked = {}
    response_commands = {}

    for irule in irules:
        path = f"irules/{irule}"
        with open(path) as f:
            content = f.read()

        # Check if HTTP::has_responded safeguard exists
        has_responded_checked[irule] = "HTTP::has_responded" in content
        
        # Check for response triggers
        response_commands[irule] = bool(re.search(r'(HTTP::redirect|HTTP::respond|reject|pool|node)', content))

    # Audit Matrix
    conflict_found = False
    active_responders = [ir for ir, responds in response_commands.items() if responds]
    
    if len(active_responders) > 1:
        for irule in active_responders[1:]:
            if not has_responded_checked[irule]:
                print(f"[CRITICAL CONFLICT] Virtual Server '{data['virtual_server']}': iRule '{irule}' executes routing/response actions without checking 'HTTP::has_responded'. Risk of TCL execution crash due to collision with earlier iRules.")
                conflict_found = True

    return not conflict_found

if __name__ == "__main__":
    sys.exit(0 if check_vs_conflicts(sys.argv[1]) else 1)