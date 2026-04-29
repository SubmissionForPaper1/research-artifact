# Sufficient Reasons and Contrastive Explanations for Reactive Systems - Experimental Artifact

This repository contains the implementation and experimental evaluation for the paper **"Sufficient Reasons and Contrastive Explanations for Reactive Systems"**.

The artifacts are organized into four main folders, each corresponding to a specific experimental section of the paper. We provide a comprehensive suite of scripts to reproduce the tables and figures presented in the work.

## 📂 Repository Structure

Each folder contains its own `README.md` with specific execution instructions.

### 1. [TSR](./TSR) (Temporal Sufficient Reason)
* **Paper Section:** *Verifying Temporal Sufficient Reason* (Table 1)
* **Description:** Verifies sufficient reasons using our implementation and compares performance against the **CATS** tool.
* **Key Dependencies:** AutoHyper, CATS.

### 2. [MTSR](./MTSR) (Minimal Temporal Sufficient Reason)
* **Paper Section:** *Synthesizing Minimal Temporal Sufficient Reason* (Tables 2 & 3)
* **Description:** Synthesizes explicit causal witnesses (automata) and compares execution time and size against the **Corp** tool.
* **Key Dependencies:** Spot (Python), Corp.

### 3. [MSR](./MSR) (Minimal Sufficient Reason)
* **Paper Section:** *Synthesizing Minimal Sufficient Reason* (Non-temporal)
* **Description:** Synthesizes minimal sufficient reasons using the $\exists \forall \exists$ quantifier structure.
* **Key Dependencies:** AutoHyper.

### 4. [MCE](./MCE) (Minimal Contrastive Explanation)
* **Paper Section:** *Synthesizing Minimal Contrastive Explanation*
* **Description:** Synthesizes minimal contrastive explanations (counterfactuals) for specific benchmark cases (e.g., `example_6`, `tp_left`).
* **Key Dependencies:** AutoHyper.

---

## ⚙️ System Requirements

To ensure all scripts run correctly, please verify your environment matches the following:

* **Operating System:** Linux (Ubuntu 20.04 LTS or 22.04 LTS recommended).
    * *Note for Windows Users:* We strongly recommend using **WSL2** (Windows Subsystem for Linux) with Ubuntu.
* **Python:** Version 3.8 or higher.
* **Architecture:** x86_64.

---

## 📦 Installation Guide

Follow these steps in this exact order to set up the environment.

### Step 1: Install System-Level Dependencies
Some Python libraries (specifically `pygraphviz`) require system development headers to compile.
**Run this in your terminal first:**

    sudo apt-get update
    sudo apt-get install -y python3-dev graphviz libgraphviz-dev build-essential

### Step 2: Set Up Python Virtual Environment
We recommend using a virtual environment to manage dependencies.

1.  **Create the environment:** 
# (If this fails, try installing python3-venv: sudo apt install python3-venv)
    
    python3 -m venv venv

2.  **Activate the environment:**
    
    source venv/bin/activate

### Step 3: Install Python Libraries
Install the required packages listed in `requirements.txt`:

    pip install -r requirements.txt

### Step 4: Install Spot (Critical for MTSR)
The **Spot** library is required for the automata synthesis experiments.

**🔍 Verification Check:**
Before installing, check if you already have a working version of Spot by running:
```bash
python3 -c "import spot; print('Spot version:', spot.version())"
```
* **If this prints a version number** (e.g., `2.11.6`), **you are done!** You can skip the rest of Step 4.
* **If this gives an error** (`ModuleNotFoundError`), proceed with the installation below.

**Installation Instructions:**
Since external repositories can be unreliable, we recommend building it from source.

Run the following commands one by one: (Note: The make step may take 5-10 minutes. Please be patient.)

```bash
# 1. Download the source code (Version 2.11.6)
wget -c http://www.lrde.epita.fr/dload/spot/spot-2.11.6.tar.gz
tar -xzf spot-2.11.6.tar.gz
cd spot-2.11.6

# 2. Configure the build to include Python bindings
./configure --prefix=/usr --enable-python

# 3. Compile and Install
make
sudo make install

# 4. Clean up (Optional)
cd ..
rm -rf spot-2.11.6 spot-2.11.6.tar.gz
```

*> **Troubleshooting:** If the apt installation fails or you are not on Ubuntu, you can download and compile Spot from source (http://spot.lrde.epita.fr/install.html), but this takes significantly longer.*

### Verification Check:
After the installation completes, verify it works by running:

python3 -c "import spot; print('Spot version:', spot.version())"

If this prints the version number, you are ready to proceed.

---

## 🛠️ Included Tools

The following tools are **pre-packaged** in the `tools/` directory and do not require manual installation:
* **AutoHyper:** Located at `tools/AutoHyper/app/AutoHyper`.
* **Corp:** Located at `tools/corp/corp.py`.

**Note on CATS Tool:**
The CATS tool (used only for baselines in the **TSR** experiment) is **not** included due to complex build requirements. If you wish to run the CATS comparison, please follow the instructions in `TSR/README.md` to compile it manually.

---

## 🧪 Running Experiments

All scripts are configured to automatically look for tools in the local `tools/` directory.

**To reproduce specific results:**

1.  Navigate to the relevant folder:
    ```bash
    cd TSR   # For Table 1 (Verification)
    # OR
    cd MTSR  # For Tables 2 & 3 (Synthesis Comparison)
    ```

2.  Follow the instructions in the local `README.md` to execute the scripts.

---

References

[1] CATS: https://github.com/cats-tool/cats
[2] AutoHyper: https://github.com/AutoHyper/AutoHyper
[3] CORP: https://github.com/reactive-systems/corp
[4] Spot: https://spot.lre.epita.fr
