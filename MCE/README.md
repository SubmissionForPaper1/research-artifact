# Synthesizing Minimal Contrastive Explanations (MCE)

This folder contains the experimental artifacts for the paper section **"Synthesizing Minimal Contrastive Explanation"**.

The experiments demonstrate the synthesis of minimal counterfactuals (contrastive explanations) for specific benchmarks.

## 📂 Structure

* **`MCE_all_examples.py`**: A script that runs the synthesis on the benchmark subset used in this section (`example_6`, `tp_left`, `tp_right`).
* **`MCE_one_example.py`**: A script to synthesize a contrastive explanation for a single specific instance.
* **Benchmark Folders**: Directories like `example_6/`, `tp_left/`, etc., contain the system models and `.hq` files.

---

## 🚀 Running Our Approach (MCE)

Our implementation uses **AutoHyper** to synthesize a minimal contrastive explanation.

### Prerequisites

Ensure you are inside the `MCE/` directory:

    cd MCE

### 1. Reproduce All Benchmarks
To run the full suite of experiments:

    python3 MCE_all_examples.py

**Expected Output:**
The script prints the minimal contrastive explanation found (or reports if none exists).

    [*] Starting Batch MCE Check using tool at: .../tools/AutoHyper/app/AutoHyper

    --- Processing: example_6/example_6_globally.hq ---
    PI: {r0,r1}{g0}{r0,r1} ({g0}{r0,r1})^ω
    Effect: G !g1
    found a minimal contrastive explanation: {r1}{g1}{r0,r1} ({g0}{r0,r1})^ω

    --- Processing: tp_left/tp_left.hq ---
    PI: Defined in .hq file (LTL)
    Effect: F e
    could not find a minimal contrastive explanation.

**Interpreting the Output:**
* **PI:** The original trace where the Effect holds.
* **Effect:** The property we are explaining (why did this happen?).
* **Found Explanation:** The synthesized counterfactual trace ($\tau$) that is minimally different from $\pi$ but *violates* the Effect.
* **"Could not find...":** Indicates no valid counterfactual exists (e.g., in `tp_left`, the effect is inevitable).

### 2. Run a Single Instance
To synthesize an explanation for a specific system:

    python3 MCE_one_example.py <path_to_system_file> <path_to_hq_file>

**Example:**

    python3 MCE_one_example.py example_6/system.txt example_6/example_6_globally.hq

---

## 🛠️ Modifying the Target Effect

The synthesis query is defined in the `.hq` files.
To change the **Effect** (the property you want to explain), you must update it in **two specific locations** within the `.hq` file to ensure the logic remains consistent.

### Logic Overview
1.  **Explanation Validity ($\tau$):** We check `!Effect(_tau)`. The explanation $\tau$ must *not* satisfy the original effect (it must change the outcome).
2.  **Minimality Check ($\pi_2$):** We check `Effect(_pi2)`. Any trace $\pi_2$ that is "closer" to the original $\pi$ than $\tau$ must still satisfy the original effect (meaning $\tau$ is the *minimal* necessary change).

### Example: Modifying `example_6_globally.hq`

**Current File (Effect = `G !g1`):**
```text
...
&
(
  !(G !{"g1"_tau})   <-- [LOCATION 1] Validity: _tau violates "G !g1" (Effect)
)
&
(
( ... quantifier logic ... ) 
->
(
  ( ... )
  ->
  (G !{"g1"_pi2})    <-- [LOCATION 2] Minimality: _pi2 still satisfies "G !g1" (Effect)
)
)