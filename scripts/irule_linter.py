import re
import sys

def lint_irule(file_path):
    errors = []
    warnings = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()

    declared_vars = set()
    
    for i, line in enumerate(lines, 1):
        clean_line = line.strip()
        if clean_line.startswith("#"):
            continue

        # Check for uninitialized variables
        var_set_match = re.search(r'set\s+([a_zA_Z0_9_]+)', clean_line)
        if var_set_match:
            declared_vars.add(var_set_match.group(1))

        var_use_matches = re.findall(r'\$([a_zA_Z0_9_]+)', clean_line)
        for var in var_use_matches:
            if var not in declared_vars and var not in ['static::', 'HTTP::', 'IP::', 'SSL::']:
                errors.append(f"Line {i}: Variable '${var}' used before definition.")

        # Check for command typos
        if re.search(r'switch\s+-(glo|exactt|regexp)\b', clean_line):
            errors.append(f"Line {i}: Malformed switch option found (e.g., '-glo' instead of '-glob').")

        # Check for missing return after HTTP respond/redirect/reject
        if re.search(r'(HTTP::redirect|HTTP::respond|reject)', clean_line):
            # Check if 'return' exists on same line or within next 2 lines
            next_lines = "".join(lines[i-1:i+2])
            if "return" not in next_lines:
                warnings.append(f"Line {i}: Terminal command found without explicit 'return'. Potential fall-through issue.")

    print(f"--- Lint Results for {file_path} ---")
    for err in errors:
        print(f"[ERROR] {err}")
    for warn in warnings:
        print(f"[WARNING] {warn}")

    return len(errors) == 0

if __name__ == "__main__":
    success = all(lint_irule(arg) for arg in sys.argv[1:])
    sys.exit(0 if success else 1)