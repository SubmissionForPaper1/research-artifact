import spot
import re
import subprocess
import sys

def run_workflow(filename, output_image="final_result.png"):
    print(f"--- Processing {filename} ---")
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    # ==========================================
    # 1. Extract Inputs
    # ==========================================
    inputs_match = re.search(r'\[inputs\]\s*(.*?)\s*\[', content, re.DOTALL)
    if not inputs_match:
        print("Error: Could not find [inputs] section")
        return
    # Parse "r0" "r1" into a set {'r0', 'r1'}
    input_aps = set(re.findall(r'"([^"]+)"', inputs_match.group(1)))
    print(f"Inputs detected: {input_aps}")

    # ==========================================
    # 2. Extract and Process LTL Effect
    # ==========================================
    effect_match = re.search(r'\[effect\]\s*(.*?)\s*\[', content, re.DOTALL)
    if not effect_match:
        print("Error: Could not find [effect] section")
        return
    
    # Clean up the string (remove newlines/padding)
    ltl_formula = effect_match.group(1).strip()
    print(f"LTL Effect Formula found: {ltl_formula}")
    
    # Translate LTL to Automaton
    # using spot.translate ensures we get a compatible automaton
    try:
        aut_effect = spot.translate(ltl_formula)
    except Exception as e:
        print(f"Error translating LTL: {e}")
        return

    # ==========================================
    # 3. Extract and Process HOA System
    # ==========================================
    hoa_match = re.search(r'(HOA:.*--END--)', content, re.DOTALL)
    if not hoa_match:
        print("Error: Could not find HOA content")
        return
    
    hoa_content = hoa_match.group(1)
    aut_system = spot.automaton(hoa_content)
    
    if aut_system is None:
        print("Error parsing HOA system")
        return

    # ==========================================
    # 4. Intersection (Product)
    # ==========================================
    print("Computing intersection (System && Effect)...")
    aut_intersection = spot.product(aut_system, aut_effect)
    
    # Convert intersection to string so we can pass it to autfilt
    # (This bypasses the Python binding issues you had with remove_ap/minimization)
    intersection_hoa = aut_intersection.to_str("hoa")

    # ==========================================
    # 5. Identify Outputs to Remove
    # ==========================================
    # We look at all APs in the intersection and remove those that are NOT inputs
    all_aps = [str(ap) for ap in aut_intersection.ap()]
    aps_to_remove = [ap for ap in all_aps if ap not in input_aps]
    
    if aps_to_remove:
        print(f"Removing output APs: {aps_to_remove}")
    else:
        print("No output APs found to remove.")

    # ==========================================
    # 6. Project & Minimize (using autfilt)
    # ==========================================
    # can be changed here to --small for faster results.
    cmd = ["autfilt", "--sat-minimize"]
    for ap in aps_to_remove:
        cmd.append(f"--remove-ap={ap}")
    
    try:
        print("Running projection and minimization...")
        result = subprocess.run(
            cmd,
            input=intersection_hoa,
            text=True,
            capture_output=True,
            check=True
        )
        
        final_hoa = result.stdout
        print("\n--- Final Minimized HOA ---")
        print(final_hoa)
        
        # ==========================================
        # 7. Render to PNG
        # ==========================================
        # Load back to Spot to get DOT format
        final_aut = spot.automaton(final_hoa)
        dot_string = final_aut.to_str("dot")
        
        subprocess.run(
            ["dot", "-Tpng", "-o", output_image],
            input=dot_string,
            text=True,
            check=True
        )
        print(f"Successfully saved graph to {output_image}")

    except subprocess.CalledProcessError as e:
        print("Error during autfilt/dot processing:")
        print(e.stderr)
    except FileNotFoundError as e:
        print(f"Error: Tool not found ({e.filename}). Make sure Spot (autfilt) and Graphviz (dot) are installed.")

# --- Run the Script ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_input_file>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    run_workflow(input_filename)