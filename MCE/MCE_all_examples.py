import os
import sys
import subprocess
import re

# --- CONFIGURATION ---
# Path to AutoHyper (relative to this script)
REL_TOOL_PATH = "../tools/AutoHyper/app/AutoHyper"
# ---------------------

def parse_system_file(filepath):
    state_map = {}
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return {}
    
    state_pattern = re.compile(r'State:\s+(\d+)\s+\{(.*?)\}')
    matches = state_pattern.findall(content)
    
    for state_id, assignments in matches:
        state_id = int(state_id)
        true_vars = set()
        assign_pattern = re.compile(r'\("(\w+)"\s+(true|false)\)')
        assign_matches = assign_pattern.findall(assignments)
        for var_name, val in assign_matches:
            if val == 'true': true_vars.add(var_name)
        state_map[state_id] = true_vars
    return state_map

def parse_hq_effect(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return "Unknown"
    implication_matches = re.findall(r'->\s*\(([^;]*?_pi2[^;]*?)\)', content, re.DOTALL)
    clean_effect = "Unknown"
    for match in implication_matches:
        if "<->" not in match:
            raw_effect = match.replace("\n", " ").strip()
            clean_effect = re.sub(r'\{?"(\w+)"_pi2\}?', r'\1', raw_effect)
            clean_effect = re.sub(r'\s+', ' ', clean_effect)
            break
    return clean_effect

def format_witness_path(path_str, state_map):
    match = re.match(r'\(([\d\s]+)\)\s*\(([\d\s]+)\)', path_str.strip())
    if not match: return "Error parsing witness"
    prefix_ids = [int(x) for x in match.group(1).split()]
    cycle_ids = [int(x) for x in match.group(2).split()]

    def ids_to_string(ids):
        result = []
        for sid in ids:
            if sid not in state_map:
                result.append("{?}")
                continue
            vars_set = state_map[sid]
            vars_set = {v for v in vars_set if v != "r"} # Filter 'r'
            if not vars_set: result.append("{}")
            else: result.append("{" + ",".join(sorted(vars_set)) + "}")
        return "".join(result)
    return f"{ids_to_string(prefix_ids)} ({ids_to_string(cycle_ids)})^ω"

def process_example(tool_executable, system_file, hq_file):
    state_map = parse_system_file(system_file)
    effect = parse_hq_effect(hq_file)
    
    cmd = [tool_executable, "--explicit", system_file, hq_file, "--witness"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        
        if "UNSAT" in output:
            print(f"PI: Defined in .hq file (LTL)")
            print(f"Effect: {effect}")
            print("could not find a minimal contrastive explanation.")
        elif "SAT" in output:
            pi_match = re.search(r'pi:\s+(.*)', output)
            tau_match = re.search(r'tau:\s+(.*)', output)
            
            pi_str = "Defined in .hq file"
            if pi_match: pi_str = format_witness_path(pi_match.group(1), state_map)
            
            tau_str = "Error"
            if tau_match: tau_str = format_witness_path(tau_match.group(1), state_map)
            
            print(f"PI: {pi_str}")
            print(f"Effect: {effect}")
            print(f"found a minimal contrastive explanation: {tau_str}")
        else:
            print(f"Effect: {effect}")
            print("Unknown result from AutoHyper.")
            
    except Exception as e:
        print(f"Error running AutoHyper: {e}")

def main():
    # 1. Resolve Tool
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_executable = os.path.abspath(os.path.join(script_dir, REL_TOOL_PATH))
    if not os.path.exists(tool_executable) and os.path.exists(tool_executable + ".exe"):
        tool_executable += ".exe"
    if not os.path.exists(tool_executable):
        print(f"Error: AutoHyper not found at {tool_executable}")
        sys.exit(1)

    print(f"[*] Starting Batch MCE Check using tool at: {tool_executable}\n")

    # 2. Iterate Folders
    root_dir = "."
    subdirs = sorted([d for d in os.listdir(root_dir) if os.path.isdir(d) and not d.startswith(".") and d != "__pycache__"])

    for d in subdirs:
        dir_path = os.path.join(root_dir, d)
        system_file = os.path.join(dir_path, "system.txt")
        
        if not os.path.exists(system_file):
            continue

        hq_files = sorted([f for f in os.listdir(dir_path) if f.endswith(".hq")])
        
        for hq in hq_files:
            print(f"--- Processing: {d}/{hq} ---")
            hq_path = os.path.join(dir_path, hq)
            process_example(tool_executable, system_file, hq_path)
            print("") # Empty line between examples

if __name__ == "__main__":
    main()