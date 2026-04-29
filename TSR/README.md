# Verifying Temporal Sufficient Reasons (TSR)

This folder contains the experimental artifacts for the paper section **"Verifying Temporal Sufficient Reason"**. It corresponds to the results presented in **Table 1**.

The experiments compare our hyperproperty-based verification approach against the CATS tool.

## 📂 Structure

* **`TSR_all_examples.py`**: A script that runs the verification on all benchmark instances used in the paper (Table 1).
* **`TSR_one_example.py`**: A script to verify a single specific instance.
* **`CATS_examples/`**: Contains the benchmark files formatted specifically for the external [CATS tool](https://github.com/cats-tool/cats) to reproduce the baseline results.
* **Benchmark Folders**: Directories like `arbiter/`, `example_1/`, etc., contain the system models and `.hq` (HyperQPTL) query files for our approach.

---

## 🚀 Running Our Approach (TSR)

Our implementation uses **AutoHyper** to verify that a given formula is a Temporal Sufficient Reason. The scripts automatically locate the AutoHyper binary in the `../tools/` directory.

### Prerequisites

Ensure you are inside the `TSR/` directory before running scripts to avoid path errors:

    cd TSR

### 1. Reproduce All Benchmarks (Table 1)
To run the full suite of experiments and see the SAT/UNSAT results:

    python3 TSR_all_examples.py

**Expected Output:**
The script will iterate through the benchmark folders and print the verification result (`SAT` indicates the reason is sufficient).

    [*] Using AutoHyper at: .../tools/AutoHyper/app/AutoHyper

    --- Folder: arbiter ---
      arbiter.hq             -> SAT
      arbiter_simple.hq      -> SAT

    --- Folder: example_1 ---
      example1.hq            -> SAT
    ...

### 2. Run a Single Instance
To verify a specific system and property:

    python3 TSR_one_example.py <path_to_system_file> <path_to_hq_file>

**Example:**

    python3 TSR_one_example.py arbiter/system.txt arbiter/arbiter.hq

---

## 🛠️ Modifying Cause & Effect

The Cause and Effect formulas are defined directly inside the `.hq` files (e.g., `arbiter/arbiter.hq`). 
The file structure follows the implication: `Cause -> Effect`.

To test different reasons or effects, you must manually edit these files.

### Syntax Structure

**1. Arbiter Example (`example_6_odd.hq`):**

    forall pi.
    (
        "r0"_pi
        &
        G 
        (
            ({"r0"_pi} <-> !X {"r0"_pi})
        )
    )                 <-- CAUSE (End of antecedent)
    -> 
    (G !{"g1"_pi})    <-- EFFECT (Consequent)

**2. Example 8 (`example8.hq`):**

    forall pi.
    (
      (
        "a"_pi
        |
        (
        X
        ("a"_pi)
        )
      )
    )                 <-- CAUSE (End of antecedent)
     -> 
      (XX {"error"_pi}) <-- EFFECT (Consequent)

**How to Modify:**
* **To change the Cause:** Edit the logic inside the first block (before the `->`).
* **To change the Effect:** Edit the logic inside the second block (after the `->`).

---

## 🐈 Running the CATS Baseline

To reproduce the comparison times for the **CATS** tool (the right-hand side of Table 1), you must use the external CATS binary.

**Note:** The CATS tool is **not** included in the `../tools/` directory due to its specific build environment requirements.

### Steps to Reproduce:

1.  **Download CATS:**
    Clone and build the tool from the official repository:
    [https://github.com/cats-tool/cats](https://github.com/cats-tool/cats)

2.  **Prepare Benchmarks:**
    Copy the **`CATS_examples/`** folder from this directory into your CATS installation directory.

3.  **Execute:**
    Follow the instructions in the CATS repository to run the verification on the files inside `CATS_examples/`. 
    