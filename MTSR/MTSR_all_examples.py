import spot
import re
import subprocess
import os
import glob

# Configuration
INPUT_FOLDER = "./both_examples"
OUTPUT_FOLDER = "./MTSR_results"

def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output folder: {OUTPUT_FOLDER}")

def process_single_file(filepath):
    filename = os.path.basename(filepath)
    file_stem = os.path.splitext(filename)[0]
    output_image = os.path.join(OUTPUT_FOLDER, f"{file_stem}.png")

    print(f"\n--- Processing: {filename} ---")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filename}: Could not read file ({e})")
        return

    # 1. Extract Inputs
    inputs_match = re.search(r'\[inputs\]\s*(.*?)\s*\[', content, re.DOTALL)
    if not inputs_match:
        print(f"Skipping {filename}: [inputs] section not found")
        return
    input_aps = set(re.findall(r'"([^"]+)"', inputs_match.group(1)))
    
    # 2. Extract LTL Effect
    effect_match = re.search(r'\[effect\]\s*(.*?)\s*\[', content, re.DOTALL)
    if not effect_match:
        print(f"Skipping {filename}: [effect] section not found")
        return
    ltl_formula = effect_match.group(1).strip()
    
    # Translate LTL
    try:
        aut_effect = spot.translate(ltl_formula)
    except Exception as e:
        print(f"Skipping {filename}: Invalid LTL ({e})")
        return

    # 3. Extract HOA System
    hoa_match = re.search(r'(HOA:.*--END--)', content, re.DOTALL)
    if not hoa_match:
        print(f"Skipping {filename}: HOA content not found")
        return
    hoa_content = hoa_match.group(1)
    
    # Parse HOA
    aut_system = spot.automaton(hoa_content)
    if aut_system is None:
        print(f"Skipping {filename}: Spot failed to parse HOA block")
        return

    # 4. Intersection
    aut_intersection = spot.product(aut_system, aut_effect)
    intersection_hoa = aut_intersection.to_str("hoa")

    # 5. Identify Outputs to Remove
    all_aps = [str(ap) for ap in aut_intersection.ap()]
    aps_to_remove = [ap for ap in all_aps if ap not in input_aps]
    
    # 6. Project & Minimize (autfilt subprocess)
    cmd = ["autfilt", "--small"]
    for ap in aps_to_remove:
        cmd.append(f"--remove-ap={ap}")
    
    try:
        result = subprocess.run(
            cmd,
            input=intersection_hoa,
            text=True,
            capture_output=True,
            check=True
        )
        final_hoa = result.stdout
        
        # 7. Render to PNG
        final_aut = spot.automaton(final_hoa)
        dot_string = final_aut.to_str("dot")
        
        subprocess.run(
            ["dot", "-Tpng", "-o", output_image],
            input=dot_string,
            text=True,
            check=True
        )
        print(f"Success! Saved to: {output_image}")

    except subprocess.CalledProcessError as e:
        print(f"Error processing {filename}: {e.stderr}")
    except FileNotFoundError:
        print("Error: 'autfilt' or 'dot' not found. Check installation.")
        return

def main():
    ensure_output_folder()
    
    # Find all .txt files in the examples folder
    files = glob.glob(os.path.join(INPUT_FOLDER, "*.txt"))
    
    if not files:
        print(f"No .txt files found in {INPUT_FOLDER}")
        return

    print(f"Found {len(files)} files to process...")
    
    for filepath in files:
        process_single_file(filepath)

if __name__ == "__main__":
    main()