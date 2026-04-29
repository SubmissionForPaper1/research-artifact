import sys
import re
import subprocess
import os

# --- CONFIGURATION ---
CAUSALITY_VAR = "r"

# Relative path from this script (MSR/) to the tool executable
# This will work on any computer as long as the folder structure is kept
REL_TOOL_PATH = "../tools/AutoHyper/app/AutoHyper"
# ---------------------

def parse_system_file(filepath):
    state_map = {}
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not open system file: {filepath}")
        sys.exit(1)
    
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
    cause_vars = set()
    for _, vars_set in state_map.items():
        if CAUSALITY_VAR in vars_set:
            subset = vars_set.copy()
            subset.remove(CAUSALITY_VAR)
            cause_vars.update(subset)
    return sorted(list(cause_vars))

def parse_hq_effect(filepath):
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
    match = re.match(r'\(([\d\s]+)\)\s*\(([\d\s]+)\)', path_str.strip())
    if not match: return [], []
    prefix_ids = [int(x) for x in match.group(1).split()]
    cycle_ids = [int(x) for x in match.group(2).split()]
    def get_steps(ids):
        steps = []
        for sid in ids:
            if sid in state_map: steps.append(set(state_map[sid]))
            else: steps.append(set())
        return steps
    return get_steps(prefix_ids), get_steps(cycle_ids)

def print_witness_table(pi_prefix, pi_cycle, tau_prefix, tau_cycle, vars_to_show):
    if not vars_to_show: vars_to_show = ["(No specific cause vars detected)"]
    col_width = max(25, len(vars_to_show) * 8)
    
    print(f"\n{'=' * (col_width * 2 + 25)}")
    print(f"{'TIME':<5} | {'REASON REPRESNTATION (Tau)':<{col_width}} | {'ACTUAL TRACE (Pi)':<{col_width}} | {'STATUS'}")
    print(f"{'=' * (col_width * 2 + 25)}")

    def print_row(t, tau_vars, pi_vars):
        current_cause_vars = [v for v in vars_to_show if v in tau_vars]
        is_cause = len(current_cause_vars) > 0
        marker = "<-- MINIMAL REASON" if is_cause else ""
        row_color = "\033[92m" if is_cause else "" # Green
        reset_color = "\033[0m" if is_cause else ""

        def fmt(v_set):
            parts = []
            for v in vars_to_show:
                if v == "(No specific cause vars detected)": return ""
                val = "T" if v in v_set else "F"
                parts.append(f"{v}={val}")
            return ", ".join(parts)
        print(f"{row_color}{t:<5} | {fmt(tau_vars):<{col_width}} | {fmt(pi_vars):<{col_width}} | {marker}{reset_color}")

    max_prefix = max(len(pi_prefix), len(tau_prefix))
    for i in range(max_prefix):
        p_step = pi_prefix[i] if i < len(pi_prefix) else set()
        t_step = tau_prefix[i] if i < len(tau_prefix) else set()
        print_row(i, t_step, p_step)

    print(f"{'-'*5} + {'-'*col_width} + {'-'*col_width} + {'-'*15}")
    print(f"{'CYCLE':<5} | {'(Repeating Pattern)':<{col_width}} | {'(Repeating Pattern)':<{col_width}} |")
    print(f"{'-'*5} + {'-'*col_width} + {'-'*col_width} + {'-'*15}")

    max_cycle = max(len(pi_cycle), len(tau_cycle))
    current_time_idx = max_prefix
    for i in range(max_cycle):
        p_step = pi_cycle[i] if i < len(pi_cycle) else set()
        t_step = tau_cycle[i] if i < len(tau_cycle) else set()
        print_row(current_time_idx, t_step, p_step)
        current_time_idx += 1
    print(f"{'=' * (col_width * 2 + 25)}")

def cleanup_temp_files():
    """Removes temporary files created by the tool."""
    temp_files = ["aut1.hoa", "autRes.hoa"]
    for tf in temp_files:
        if os.path.exists(tf):
            try:
                os.remove(tf)
            except OSError:
                pass

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <system_file> <hq_file>")
        sys.exit(1)

    system_file = sys.argv[1]
    hq_file = sys.argv[2]
    
    # --- DYNAMIC PATH RESOLUTION ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_executable = os.path.abspath(os.path.join(script_dir, REL_TOOL_PATH))
    
    # Auto-detect .exe (if running on Windows/WSL)
    if not os.path.exists(tool_executable) and os.path.exists(tool_executable + ".exe"):
        tool_executable += ".exe"

    if not os.path.exists(tool_executable):
        print(f"Error: AutoHyper executable not found at:\n{tool_executable}")
        print("\nPossible fix: Ensure the 'tools' folder contains the compiled 'AutoHyper' binary.")
        sys.exit(1)
    # -------------------------------

    state_map = parse_system_file(system_file)
    effect = parse_hq_effect(hq_file)
    interesting_vars = get_cause_vars_from_system(state_map)
    
    cmd = [tool_executable, "--explicit", system_file, hq_file, "--witness"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        if "UNSAT" in output:
            print(f"PI: Defined in .hq file (LTL)")
            print(f"Effect: {effect}")
            print("could not find a minimal cause.")
        elif "SAT" in output:
            pi_match = re.search(r'pi:\s+(.*)', output)
            tau_match = re.search(r'tau:\s+(.*)', output)
            
            pi_str_fmt = "Defined in .hq file"
            if pi_match: pi_str_fmt = format_witness_string(pi_match.group(1), state_map)
            tau_str_fmt = "Unknown"
            if tau_match: tau_str_fmt = format_witness_string(tau_match.group(1), state_map)

            print(f"PI: {pi_str_fmt}")
            print(f"Effect: {effect}")
            print(f"found a minimal cause R: {tau_str_fmt}")

            if pi_match and tau_match:
                pi_p, pi_c = get_trace_steps_split(pi_match.group(1), state_map)
                tau_p, tau_c = get_trace_steps_split(tau_match.group(1), state_map)
                print_witness_table(pi_p, pi_c, tau_p, tau_c, interesting_vars)
        else:
            print(f"Effect: {effect}")
            print("Unknown result from AutoHyper.")

        # Remove the temporary files (aut1.hoa, autRes.hoa)
        cleanup_temp_files()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()