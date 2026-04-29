import os
import sys
import subprocess
import argparse
import shutil
import re
import glob
import spot

# --- Configuration ---
INPUT_FOLDER = "both_examples"
OUTPUT_FOLDER = "corp_results"
TEMP_BASE = "corp_runs"

# Path to the Corp tool relative to this script
CORP_TOOL_PATH = "../tools/corp/corp.py"

# --- Parsing & Helper Functions ---

def parse_cats_file(filepath):
    """Parses the custom [section] format."""
    data = {}
    current_section = None
    buffer = []
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
        return "" 

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
    if not ap_match: return system_text

    system_aps = re.findall(r'"([^"]+)"', ap_match.group(1))
    output_indices = [str(i) for i, ap in enumerate(system_aps) if ap not in inputs]
    
    controllable_line = f"controllable-AP: {' '.join(output_indices)}"
    if "--BODY--" in system_text:
        return system_text.replace("--BODY--", f"{controllable_line}\n--BODY--")
    return system_text + "\n" + controllable_line

# --- Batch Processing Logic ---

def generate_png(hoa_path, output_png_path):
    """Converts HOA file to PNG using Spot and Dot."""
    try:
        aut = spot.automaton(hoa_path)
        dot_string = aut.to_str("dot")
        
        subprocess.run(
            ["dot", "-Tpng", "-o", output_png_path],
            input=dot_string,
            text=True,
            check=True
        )
        return True
    except Exception as e:
        print(f"    [!] visualization failed: {e}")
        return False

def process_file(filepath):
    filename = os.path.basename(filepath)
    base_name = os.path.splitext(filename)[0]
    
    print(f"\n>>> Processing: {filename}")

    # 1. Parse
    data = parse_cats_file(filepath)
    required = ['system', 'effect', 'lasso', 'inputs']
    if any(k not in data for k in required):
        print(f"    [!] Skipping: Missing sections in {filename}")
        return

    # 2. Setup Temp Directory
    work_dir = os.path.join(TEMP_BASE, base_name)
    if not os.path.exists(work_dir): os.makedirs(work_dir)
    
    path_sys = os.path.join(work_dir, "system.hoa")
    path_eff = os.path.join(work_dir, "effect.txt")
    path_trc = os.path.join(work_dir, "trace.txt")
    path_res = os.path.join(work_dir, "result.hoa")

    # 3. Create Files
    with open(path_sys, 'w') as f:
        f.write(inject_controllable_info(data['system'], data['inputs']))
    with open(path_eff, 'w') as f:
        f.write(data['effect'])
    with open(path_trc, 'w') as f:
        f.write(translate_lasso(data['lasso']))
    
    # 4. Resolve Tool Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_path = os.path.abspath(os.path.join(script_dir, CORP_TOOL_PATH))
    
    if not os.path.exists(tool_path):
        print(f"    [!] Error: Corp tool not found at {tool_path}")
        return

    # 5. Run Corp
    # Note: We run it using the full path to corp.py
    cmd = [
        sys.executable, tool_path, 
        "-s", path_sys, 
        "-e", path_eff, 
        "-t", path_trc, 
        "-o", path_res
    ]
    
    try:
        # Added text=True so stderr is readable if we need to print it
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        print(f"    [!] Corp.py failed (exit code {e.returncode})")
        # Printing stderr helps see WHY it failed (e.g. syntax error in input)
        print(f"    [DEBUG] Error details:\n{e.stderr}") 
        return

    # 6. Visualize Result
    if os.path.exists(path_res):
        png_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.png")
        if generate_png(path_res, png_path):
            print(f"    [+] Success! Image saved: {png_path}")
        else:
            print("    [!] Result generated, but PNG creation failed.")
    else:
        print("    [!] Corp.py finished but no result.hoa found.")

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output folder: {OUTPUT_FOLDER}")

    files = glob.glob(os.path.join(INPUT_FOLDER, "*.txt"))
    
    if not files:
        print(f"No .txt files found in {INPUT_FOLDER}")
        return

    print(f"Found {len(files)} files. Starting batch run...")
    
    for f in files:
        process_file(f)

    print("\nBatch processing complete.")

if __name__ == "__main__":
    main()