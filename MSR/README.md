# Synthesizing Minimal Sufficient Reason (MSR)

This folder contains the experimental artifacts for the paper section **"Synthesizing Minimal Sufficient Reason"**.

The experiments demonstrate the synthesis of non-temporal minimal sufficient reasons using the $\exists \forall \exists$ quantifier structure formalized in the paper.

## 📂 Structure

* **`MSR_all_examples.py`**: A script that runs the synthesis on all benchmark instances.
* **`MSR_one_example.py`**: A script to synthesize a reason for a single specific instance.
* **`MSR_examples/`**: Contains the system models (`system.txt`) and HyperQPTL query files (`.hq`) defining the synthesis problem.

---

## 🚀 Running Our Approach (MSR)

Our implementation uses **AutoHyper** to synthesize the minimal sufficient reason.

### Prerequisites

Ensure you are inside the `MSR/` directory:

    cd MSR

### 1. Reproduce All Benchmarks
To run the full suite of experiments:

    python3 MSR_all_examples.py

**Expected Output:**
The script prints a text-based visualization of the synthesized reason for each benchmark.

    --- Found directory: MSR_examples/arbiter ---
    Processing: ...
    found a minimal cause R: ...
    
    ===========================================================================
    TIME  | REASON REPRESENTATION (Tau) | ACTUAL TRACE (Pi)         | STATUS
    ===========================================================================
    0     | r0=F, r1=F                  | r0=F, r1=F                | 
    1     | r0=F, r1=F                  | r0=F, r1=T                | 
    3     | r0=F, r1=T                  | r0=F, r1=T                | <-- MINIMAL REASON
    ...

**Interpreting the Output:**
* **REASON REPRESENTATION (Tau):** Represents the sufficient reason. If a variable is present here, its value is part of the reason.
* **ACTUAL TRACE (Pi):** The full execution trace of the system.
* **<-- MINIMAL REASON:** Marks the specific time steps and variable values that constitute the minimal sufficient reason for the effect.

### 2. Run a Single Instance
To synthesize a reason for a specific system and query:

    python3 MSR_one_example.py <path_to_system_file> <path_to_hq_file>

**Example:**

    python3 MSR_one_example.py MSR_examples/example_8/system.txt MSR_examples/example_8/example8.hq

---

## 🛠️ Modifying the Target Effect

The synthesis query is defined in the `.hq` files. Unlike the other experiments, the MSR formula structure is complex ($\exists \pi \exists \tau \forall \pi_2 \forall \tau_2 \exists \pi_3$).

To change the **Effect** (the property you want to explain), you must update it in **two specific locations** within the `.hq` file.

1.  **Location 1 (Validation):** Inside the block quantifying over `pi2`. This verifies that the candidate reason $\tau$ implies the effect.
2.  **Location 2 (Minimality):** Inside the block quantifying over `pi3`. This verifies that no strictly smaller reason $\tau'$ implies the effect.

### Example: Modifying `example8.hq`

**Current File:**
```text
...
&
(
  ( !{"r"_pi2} ... )
  -> 
  (XX {"error"_pi2})   <-- [LOCATION 1] Change Effect Here for pi2
)
&
(
  "r"_tau2 ->(
    !
    (
      ( ... )
      -> 
      (XX {"error"_pi3}) <-- [LOCATION 2] Change Effect Here for pi3
    )
    ...


  ))