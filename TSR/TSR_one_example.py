import sys
import os
import subprocess

# --- CONFIGURATION ---
# Relative path to AutoHyper from this script (TSR/ folder)
# This finds the tool you already set up in tools/AutoHyper
REL_TOOL_PATH = "../tools/AutoHyper/app/AutoHyper"
# ---------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 TSR_one_example.py <system_file> <hq_file>")
        sys.exit(1)

    system_file = sys.argv[1]
    hq_file = sys.argv[2]

    # --- PATH RESOLUTION (Portable Logic) ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tool_executable = os.path.abspath(os.path.join(script_dir, REL_TOOL_PATH))

    # Auto-detect .exe (for WSL/Windows compatibility)
    if not os.path.exists(tool_executable) and os.path.exists(tool_executable + ".exe"):
        tool_executable += ".exe"

    if not os.path.exists(tool_executable):
        print(f"Error: AutoHyper executable not found at:\n{tool_executable}")
        print("Please check your 'tools' folder.")
        sys.exit(1)
    # ----------------------------------------

    # Construct the command
    # We run in explicit mode. We don't strictly need '--witness' if we just want SAT/UNSAT.
    cmd = [tool_executable, "--explicit", system_file, hq_file]

    try:
        # Run subprocess and capture the output
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()

        # Simple string matching to find the result
        if "UNSAT" in output:
            print("UNSAT")
        elif "SAT" in output:
            print("SAT")
        else:
            print("UNKNOWN")
            # print(output) # Uncomment this if you need to debug errors

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()