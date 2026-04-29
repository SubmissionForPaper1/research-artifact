import os
import sys
import subprocess

# --- CONFIGURATION ---
# Directories to ignore
IGNORE_DIRS = {"CATS_examples", "__pycache__", ".git"}
# Path to AutoHyper (relative to this script)
REL_TOOL_PATH = "../tools/AutoHyper/app/AutoHyper"
# ---------------------

def run_tsr_check(tool_path, system_file, hq_file):
    """Runs AutoHyper and returns 'SAT' or 'UNSAT'."""
    cmd = [tool_path, "--explicit", system_file, hq_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "UNSAT" in result.stdout:
            return "UNSAT"
        elif "SAT" in result.stdout:
            return "SAT"
        else:
            return "UNKNOWN"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    # 1. Resolve Tool Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_executable = os.path.abspath(os.path.join(script_dir, REL_TOOL_PATH))
    
    # Handle .exe for Windows/WSL
    if not os.path.exists(tool_executable) and os.path.exists(tool_executable + ".exe"):
        tool_executable += ".exe"

    if not os.path.exists(tool_executable):
        print(f"Error: AutoHyper executable not found at: {tool_executable}")
        sys.exit(1)

    print(f"[*] Using AutoHyper at: {tool_executable}\n")

    # 2. Iterate through directories
    root_dir = "."
    found_any = False

    # Get all immediate subdirectories
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(d)]
    subdirs.sort()

    for d in subdirs:
        if d in IGNORE_DIRS or d.startswith("."):
            continue

        dir_path = os.path.join(root_dir, d)
        
        # Check if system.txt exists
        system_file = os.path.join(dir_path, "system.txt")
        if not os.path.exists(system_file):
            continue

        # Find all .hq files in this directory
        hq_files = [f for f in os.listdir(dir_path) if f.endswith(".hq")]
        if not hq_files:
            continue
        
        found_any = True
        print(f"--- Folder: {d} ---")
        
        for hq in sorted(hq_files):
            hq_path = os.path.join(dir_path, hq)
            result = run_tsr_check(tool_executable, system_file, hq_path)
            
            # Print format: <folder>/<hq_file>: <RESULT>
            print(f"  {hq:<30} -> {result}")
        print("")

    if not found_any:
        print("No suitable folders found (containing system.txt and *.hq files).")

    # Cleanup temporary files (optional)
    for tmp in ["aut1.hoa", "autRes.hoa"]:
        if os.path.exists(tmp):
            os.remove(tmp)

if __name__ == "__main__":
    main()