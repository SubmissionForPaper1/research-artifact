import os
import sys
import subprocess
import argparse
import shutil
import re

# --- Configuration ---
# Path to the Corp tool relative to this script
CORP_TOOL_PATH = "../tools/corp/corp.py"

def parse_cats_file(filepath):
    """Parses the custom [section] format line-by-line."""
    data = {}
    current_section = None
    buffer = []
    # Removed '[cause]' from known headers so it is ignored if present
    KNOWN_HEADERS = {'[info]', '[inputs]', '[effect]', '[lasso]', '[system]'}

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if stripped in KNOWN_HEADERS:
            if current_section:
                data[current_section] = "".join(buffer).strip()
            current_section = stripped[1:-1].lower()
            buffer = []
        else:
            if current_section:
                buffer.append(line)
    if current_section:
        data[current_section] = "".join(buffer).strip()
    return data

def translate_lasso(lasso_text):
    """Translates CATS [lasso] format to Spot trace format."""
    lines = lasso_text.split('\n')
    aps = []
    prefix_steps = []
    loop_steps = []

    for line in lines:
        line = line.strip()
        if line.startswith("AP:"):
            aps = re.findall(r'"([^"]+)"', line)
        elif line.startswith("Prefix:"):
            prefix_steps = re.findall(r'\{([^}]*)\}', line)
        elif line.startswith("Loop:"):
            loop_steps = re.findall(r'\{([^}]*)\}', line)

    if not aps:
        print("Error: No AP line found in [lasso] section.")
        sys.exit(1)

    def to_formula(indices_str):
        active_indices = set(map(int, indices_str.split())) if indices_str.strip() else set()
        terms = [f'"{ap}"' if i in active_indices else f'!"{ap}"' for i, ap in enumerate(aps)]
        return "(" + " & ".join(terms) + ")"

    p_forms = [to_formula(s) for s in prefix_steps]
    l_forms = [to_formula(s) for s in loop_steps]

    trace_str = "; ".join(p_forms)
    if l_forms:
        if trace_str: trace_str += "; "
        trace_str += "cycle{" + "; ".join(l_forms) + "}"
    return trace_str

def inject_controllable_info(system_text, inputs_text):
    """Injects 'controllable-AP' into HOA system text."""
    inputs = set(re.findall(r'"([^"]+)"', inputs_text))
    if not inputs: inputs = set(inputs_text.split())

    ap_match = re.search(r'AP:\s*\d+\s*(.*)', system_text)
    if not ap_match: return system_text # Should fail later if critical

    system_aps = re.findall(r'"([^"]+)"', ap_match.group(1))
    output_indices = [str(i) for i, ap in enumerate(system_aps) if ap not in inputs]
    
    controllable_line = f"controllable-AP: {' '.join(output_indices)}"
    if "--BODY--" in system_text:
        return system_text.replace("--BODY--", f"{controllable_line}\n--BODY--")
    return system_text + "\n" + controllable_line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    input_path = args.input_file
    if not os.path.exists(input_path): sys.exit(f"File {input_path} not found.")

    # --- PATH RESOLUTION LOGIC ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_path = os.path.abspath(os.path.join(script_dir, CORP_TOOL_PATH))
    
    if not os.path.exists(tool_path):
        sys.exit(f"Error: Corp tool not found at {tool_path}")
    # -----------------------------

    print(f"[*] Parsing {input_path}...")
    data = parse_cats_file(input_path)

    # Setup Workspace
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    work_dir = os.path.join("corp_runs", base_name)
    if not os.path.exists(work_dir): os.makedirs(work_dir)

    path_sys = os.path.join(work_dir, "system.hoa")
    path_eff = os.path.join(work_dir, "effect.txt")
    path_trc = os.path.join(work_dir, "trace.txt")
    path_res = os.path.join(work_dir, "result.hoa")

    # Process Sections
    print("[*] Injecting controllable-AP info...")
    with open(path_sys, 'w') as f:
        f.write(inject_controllable_info(data['system'], data['inputs']))
    
    with open(path_eff, 'w') as f:
        f.write(data['effect'])

    print("[*] Translating Trace...")
    with open(path_trc, 'w') as f:
        f.write(translate_lasso(data['lasso']))

    # Run Corp
    cmd = [
        sys.executable, tool_path, 
        "-s", path_sys, 
        "-e", path_eff, 
        "-t", path_trc, 
        "-o", path_res
    ]
    
    print(f"[*] Running corp.py for {base_name}...")
    try:
        subprocess.run(cmd, check=True)
        print("\n[+] Success!")
        if os.path.exists(path_res): print(f"    Result: {path_res}")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] corp.py failed code {e.returncode}")

    if not args.keep: print(f"[*] Files in: {work_dir}")

if __name__ == "__main__":
    main()