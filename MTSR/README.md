# Synthesizing Minimal Temporal Sufficient Reasons (MTSR)

This folder contains the experimental artifacts for the paper section **"Synthesizing Minimal Temporal Sufficient Reason"**. It corresponds to the results presented in **Tables 2 and 3**.

The experiments compare our automata-theoretic synthesis approach (MTSR) against the Corp tool (Coenen et al. 2022).

## 📂 Structure

### Scripts
* **`MTSR_all_examples.py`**: Runs our MTSR synthesis on all benchmark instances.
* **`MTSR_one_example.py`**: Runs MTSR synthesis on a single specific instance.
* **`corp_all_examples.py`**: Runs the Corp baseline on all benchmark instances.
* **`corp_one_example.py`**: Runs the Corp baseline on a single specific instance.

### Data & Results
* **`both_examples/`**: Contains the benchmark definition files (system models, input alphabets, and target effects) used by both tools.
* **`MTSR_results/`**: Directory where the resulting automata from our approach are saved (as PNG images).
* **`corp_results/`**: Directory where the resulting automata from the Corp tool are saved.

---

## 🚀 Running Our Approach (MTSR)

Our implementation uses the **Spot** library to synthesize a minimal witness automaton that explains the target effect.

### Prerequisites

Ensure you are inside the `MTSR/` directory:

    cd MTSR

### 1. Reproduce All Benchmarks
To synthesize reasons for all examples in `both_examples/`:

    python3 MTSR_all_examples.py

**Output:**
The script processes each file and saves the synthesized witness automaton as a PNG image in the `MTSR_results/` folder.

    Found 11 files to process...
    --- Processing: example_8.txt ---
    Success! Saved to: ./MTSR_results/example_8.png
    ...

### 2. Run a Single Instance
To synthesize a reason for a specific system:

    python3 MTSR_one_example.py <path_to_txt_file>

**Example:**

    python3 MTSR_one_example.py both_examples/example_8.txt

**Output:**
The script prints the HOA (Hanoi Omega-Automata) representation to the console and saves the visualization to `final_result.png`.

---

## 🏢 Running the Corp Baseline

We provide wrapper scripts to execute the **Corp** tool on the same benchmark set for comparison.

### 1. Reproduce All Benchmarks
To run the Corp tool on all examples:

    python3 corp_all_examples.py

**Output:**
Results are saved as images in the `corp_results/` folder.

    Found 11 files. Starting batch run...
    >>> Processing: example_8.txt
        [+] Success! Image saved: corp_results/example_8.png

### 2. Run a Single Instance
To run Corp on a specific system:

    python3 corp_one_example.py <path_to_txt_file>

**Example:**

    python3 corp_one_example.py both_examples/example_8.txt

---

## 🛠️ Modifying the Synthesis Target

The benchmarks are defined in custom `.txt` files located in the `both_examples/` directory. These files define the System (as an automaton) and the **Effect** (the property we want to explain).

To synthesize a reason for a different property, you must edit the **`[effect]`** section of the file.

### File Format (`both_examples/example_8.txt`)

    [info]
    Example 8

    [inputs]
    "a"

    [cause]
    "a" | X "a"

    [effect]       <-- MODIFY THIS SECTION
    X X "error"

    [lasso]
    ... (Trace definition)

    [system]
    HOA: v1
    ... (System Automaton Definition)

**How to Modify:**
1.  Open the desired file (e.g., `both_examples/example_8.txt`).
2.  Locate the `[effect]` header.
3.  Change the LTL formula below it to your desired target property.
4.  Run `MTSR_one_example.py` on the modified file to synthesize a new sufficient reason.