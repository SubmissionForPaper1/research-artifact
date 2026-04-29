import sys
import re
import subprocess
import os

# --- CONFIGURATION ---
# Relative path to the AutoHyper executable
REL_TOOL_PATH = "../tools/AutoHyper/app/AutoHyper"
# ---------------------

def parse_system_file(filepath):
    """
    Parses the system.txt file to map State IDs to their True variables.
    Returns a dict: {state_id: set_of_true_variables}
    """
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

def parse_hq_effect(filepath):
    """
    Parses the .hq file to extract the Effect.
    Strategy: Find the implication (->) involving pi2 variables that represents the effect.
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return "Error reading .hq file"

    implication_matches = re.findall(r'->\s*\(([^;]*?_pi2[^;]*?)\)', content, re.DOTALL)
    
    clean_effect = "Unknown"
    
    for match in implication_matches:
        # The contingency condition usually has equality checks <->. The Effect usually doesn't.
        if "<->" not in match:
            raw_effect = match.replace("\n", " ").strip()
            # Clean up syntax: {"var"_pi2} -> var, "var"_pi2 -> var
            clean_effect = re.sub(r'\{?"(\w+)"_pi2\}?', r'\1', raw_effect)
            clean_effect = re.sub(r'\s+', ' ', clean_effect)
            break
            
    return clean_effect

def format_witness_path(path_str, state_map, filter_r=True):
    """
    Converts a witness string like "(10 10) (10 11)" into the variable format.
    """
    match = re.match(r'\(([\d\s]+)\)\s*\(([\d\s]+)\)', path_str.strip())
    
    if not match:
        return "Error parsing witness format"

    prefix_ids = [int(x) for x in match.group(1).split()]
    cycle_ids = [int(x) for x in match.group(2).split()]

    def ids_to_string(ids):
        result = []
        for sid in ids:
            if sid not in state_map:
                result.append("{?}")
                continue
            
            # Get vars
            vars_set = state_map[sid]
            
            # Filter 'r' if requested (usually the causality toggle variable)
            if filter_r:
                vars_set = {v for v in vars_set if v != "r"}
            
            if not vars_set:
                result.append("{}")
            else:
                result.append("{" + ",".join(sorted(vars_set)) + "}")
        return "".join(result)

    prefix_str = ids_to_string(prefix_ids)
    cycle_str = ids_to_string(cycle_ids)

    return f"{prefix_str} ({cycle_str})^ω"

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 MCE_one_example.py <system_file> <hq_file>")
        sys.exit(1)

    system_file = sys.argv[1]
    hq_file = sys.argv[2]
    
    # --- PATH RESOLUTION ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_executable = os.path.abspath(os.path.join(script_dir, REL_TOOL_PATH))
    
    if not os.path.exists(tool_executable) and os.path.exists(tool_executable + ".exe"):
        tool_executable += ".exe"

    if not os.path.exists(tool_executable):
        print(f"Error: AutoHyper executable not found at:\n{tool_executable}")
        sys.exit(1)
    # -----------------------

    # 1. Parse Inputs
    state_map = parse_system_file(system_file)
    effect = parse_hq_effect(hq_file)
    
    # 2. Run AutoHyper
    cmd = [tool_executable, "--explicit", system_file, hq_file, "--witness"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # 3. Process Output
        if "UNSAT" in output:
            print(f"PI: Defined in .hq file (LTL)")
            print(f"Effect: {effect}")
            print("could not find a minimal contrastive explanation.")
            
        elif "SAT" in output:
            # 1. Parse PI Witness
            pi_match = re.search(r'pi:\s+(.*)', output)
            if pi_match:
                pi_witness_str = pi_match.group(1)
                pi_formatted = format_witness_path(pi_witness_str, state_map, filter_r=True)
                print(f"PI: {pi_formatted}")
            else:
                print("PI: Defined in .hq file (LTL)")

            # 2. Print Effect
            print(f"Effect: {effect}")
            
            # 3. Parse Tau Witness (The Explanation)
            tau_match = re.search(r'tau:\s+(.*)', output)
            if tau_match:
                tau_witness_str = tau_match.group(1)
                tau_formatted = format_witness_path(tau_witness_str, state_map, filter_r=True)
                # --- CHANGED OUTPUT HERE ---
                print(f"found a minimal contrastive explanation: {tau_formatted}")
            else:
                print("found a minimal contrastive explanation: (Could not parse witness)")
                
        else:
            print(f"Effect: {effect}")
            print("Unknown result from AutoHyper.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()