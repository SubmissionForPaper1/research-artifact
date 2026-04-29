import sys
import re
import subprocess
import os

# --- CONFIGURATION ---
# The folder containing your example subdirectories
EXAMPLES_FOLDER = "MSR_examples"

# Path to the AutoHyper executable
AUTOHYPER_PATH = "../tools/AutoHyper/app/AutoHyper"

# The name of the variable that toggles causality checking
CAUSALITY_VAR = "r"
# ---------------------

def parse_system_file(filepath):
    """Parses the system.txt file to map State IDs to their True variables."""
    state_map = {}
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not open system file: {filepath}")
        return {}
    
    state_pattern = re.compile(r'State:\s+(\d+)\s+\{(.*?)\}')
    matches = state_pattern.findall(content)
    
    for state_id, assignments in matches:
        state_id = int(state_id)
        true_vars = set()
        assign_pattern = re.compile(r'\("(\w+)"\s+(true|false)\)')
        assign_matches = assign_pattern.findall(assignments)
        
        for var_name, val in assign_matches:
            if val == 'true':
                true_vars.add(var_name)
        state_map[state_id] = true_vars
    return state_map

def get_cause_vars_from_system(state_map):
    """Identifies interesting 'cause' variables based on the 'r' toggle."""
    cause_vars = set()
    for _, vars_set in state_map.items():
        if CAUSALITY_VAR in vars_set:
            subset = vars_set.copy()
            subset.remove(CAUSALITY_VAR)
            cause_vars.update(subset)
    return sorted(list(cause_vars))

def parse_hq_effect(filepath):
    """Parses the .hq file to extract the Effect string."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return "Error reading .hq file"

    implication_matches = re.findall(r'->\s*\(([^;]*?_pi2[^;]*?)\)', content, re.DOTALL)
    clean_effect = "Unknown"
    
    for match in implication_matches:
        if "<->" not in match:
            raw_effect = match.replace("\n", " ").strip()
            clean_effect = re.sub(r'\{?"(\w+)"_pi2\}?', r'\1', raw_effect)
            clean_effect = re.sub(r'\s+', ' ', clean_effect)
            break
    return clean_effect

def format_witness_string(path_str, state_map):
    """Recreates the string output like: {r0,r1}{g0} ({r0}{})^w"""
    match = re.match(r'\(([\d\s]+)\)\s*\(([\d\s]+)\)', path_str.strip())
    if not match: return "Error parsing witness"

    prefix_ids = [int(x) for x in match.group(1).split()]
    cycle_ids = [int(x) for x in match.group(2).split()]

    def ids_to_str(ids):
        res = []
        for sid in ids:
            if sid not in state_map:
                res.append("{?}")
                continue
            vset = state_map[sid].copy()
            if CAUSALITY_VAR in vset: vset.remove(CAUSALITY_VAR)
            if not vset: res.append("{}")
            else: res.append("{" + ",".join(sorted(vset)) + "}")
        return "".join(res)

    return f"{ids_to_str(prefix_ids)} ({ids_to_str(cycle_ids)})^ω"

def get_trace_steps_split(path_str, state_map):
    """Parses witness string into two lists: prefix_steps and cycle_steps."""
    match = re.match(r'\(([\d\s]+)\)\s*\(([\d\s]+)\)', path_str.strip())
    if not match: return [], []

    prefix_ids = [int(x) for x in match.group(1).split()]
    cycle_ids = [int(x) for x in match.group(2).split()]

    def get_steps(ids):
        steps = []
        for sid in ids:
            if sid in state_map:
                steps.append(set(state_map[sid]))
            else:
                steps.append(set())
        return steps
    return get_steps(prefix_ids), get_steps(cycle_ids)

def print_witness_table(pi_prefix, pi_cycle, tau_prefix, tau_cycle, vars_to_show):
    """Prints the table with separated sections for Prefix and Cycle."""
    if not vars_to_show:
        vars_to_show = ["(No specific cause vars detected)"]

    col_width = max(25, len(vars_to_show) * 8)
    
    print(f"\n{'=' * (col_width * 2 + 25)}")
    print(f"{'TIME':<5} | {'REASON REPRESNTATION (Tau)':<{col_width}} | {'ACTUAL TRACE (Pi)':<{col_width}} | {'STATUS'}")
    print(f"{'=' * (col_width * 2 + 25)}")

    def print_row(t, tau_vars, pi_vars):
        current_cause_vars = [v for v in vars_to_show if v in tau_vars]
        is_cause = len(current_cause_vars) > 0
        marker = "<-- MINIMAL REASON" if is_cause else ""
        row_color = "\033[92m" if is_cause else "" # Green
        reset_color = "\033[0m"

        def fmt(v_set):
            parts = []
            for v in vars_to_show:
                if v == "(No specific cause vars detected)": return ""
                val = "T" if v in v_set else "F"
                parts.append(f"{v}={val}")
            return ", ".join(parts)

        print(f"{row_color}{t:<5} | {fmt(tau_vars):<{col_width}} | {fmt(pi_vars):<{col_width}} | {marker}{reset_color}")

    # Prefix
    max_prefix = max(len(pi_prefix), len(tau_prefix))
    for i in range(max_prefix):
        p_step = pi_prefix[i] if i < len(pi_prefix) else set()
        t_step = tau_prefix[i] if i < len(tau_prefix) else set()
        print_row(i, t_step, p_step)

    # Separator
    print(f"{'-'*5} + {'-'*col_width} + {'-'*col_width} + {'-'*15}")
    print(f"{'CYCLE':<5} | {'(Repeating Pattern)':<{col_width}} | {'(Repeating Pattern)':<{col_width}} |")
    print(f"{'-'*5} + {'-'*col_width} + {'-'*col_width} + {'-'*15}")

    # Cycle
    max_cycle = max(len(pi_cycle), len(tau_cycle))
    current_time_idx = max_prefix
    for i in range(max_cycle):
        p_step = pi_cycle[i] if i < len(pi_cycle) else set()
        t_step = tau_cycle[i] if i < len(tau_cycle) else set()
        print_row(current_time_idx, t_step, p_step)
        current_time_idx += 1

    print(f"{'=' * (col_width * 2 + 25)}")

def process_single_example(system_file, hq_file):
    """Runs the logic for one pair of system and HQ files."""
    print(f"\nProcessing:\n System: {system_file}\n HQ: {hq_file}")
    
    # 1. Parse Inputs & Detect Vars
    state_map = parse_system_file(system_file)
    if not state_map: return
    
    effect = parse_hq_effect(hq_file)
    interesting_vars = get_cause_vars_from_system(state_map)
    
    # 2. Run AutoHyper
    cmd = [AUTOHYPER_PATH, "--explicit", system_file, hq_file, "--witness"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # 3. Process Output
        if "UNSAT" in output:
            print(f"PI: Defined in .hq file (LTL)")
            print(f"Effect: {effect}")
            print("could not find a minimal cause.")
            
        elif "SAT" in output:
            # String Output
            pi_match = re.search(r'pi:\s+(.*)', output)
            tau_match = re.search(r'tau:\s+(.*)', output)
            
            pi_str_fmt = "Defined in .hq file"
            if pi_match: pi_str_fmt = format_witness_string(pi_match.group(1), state_map)
            
            tau_str_fmt = "Unknown"
            if tau_match: tau_str_fmt = format_witness_string(tau_match.group(1), state_map)

            print(f"PI: {pi_str_fmt}")
            print(f"Effect: {effect}")
            print(f"found a minimal cause R: {tau_str_fmt}")

            # Table Output
            if pi_match and tau_match:
                pi_p, pi_c = get_trace_steps_split(pi_match.group(1), state_map)
                tau_p, tau_c = get_trace_steps_split(tau_match.group(1), state_map)
                print_witness_table(pi_p, pi_c, tau_p, tau_c, interesting_vars)
        else:
            print(f"Effect: {effect}")
            print(f"Result: Unknown (AutoHyper output length: {len(output)})")

    except FileNotFoundError:
        print(f"Error: {AUTOHYPER_PATH} not found.")
    except Exception as e:
        print(f"An error occurred running AutoHyper: {e}")

def main():
    if not os.path.exists(EXAMPLES_FOLDER):
        print(f"Error: Examples folder '{EXAMPLES_FOLDER}' not found.")
        sys.exit(1)

    # Walk through the directory structure
    found_any = False
    for root, dirs, files in os.walk(EXAMPLES_FOLDER):
        # 1. Find the system file (ends in system.txt)
        system_files = [f for f in files if f.endswith("system.txt")]
        if not system_files:
            continue # Skip folders without a system file

        # Use the first system file found (usually there is only one)
        sys_path = os.path.join(root, system_files[0])
        
        # 2. Find all .hq files in the same directory
        hq_files = [f for f in files if f.endswith(".hq")]
        
        if hq_files:
            found_any = True
            print(f"\n--- Found directory: {root} ---")
            for hq in hq_files:
                hq_path = os.path.join(root, hq)
                process_single_example(sys_path, hq_path)

    if not found_any:
        print(f"No valid examples (system.txt + .hq) found in {EXAMPLES_FOLDER}")

if __name__ == "__main__":
    main()