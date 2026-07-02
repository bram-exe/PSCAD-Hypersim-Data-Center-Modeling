# Datacenter Load Impact on Grid Frequency — PSCAD Study

PSCAD models and results studying how a large AI datacenter load affects grid
frequency on a synchronous power system. Two cases are included: a sudden
**load trip** (breaker step) and a realistic **dynamic training load** driven by a
measured GPU power trace from a Llama2 training run.

Both models share the same reduced-order system frequency response (SFR)
representation — a swing equation with load damping, a turbine-governor, and an
automatic generation control (AGC) loop — so the two cases can be compared
directly.

*This study is done under the supervision of Dr. Timothy Hansen and Dr. Zongjie Wang, apart of the [Grid Modernization Initiative](https://energy.colostate.edu/grid-modernization-initiative/) at Colorado State University*

## New to Power Systems Concepts? No Problem!

**If you are already familiar with power systems, feel free to skip straight to the [System Model](#system-model) section.**

If you are new to power systems engineering, looking at control block diagrams can feel overwhelming. Personally, if I saw this page a few months ago most of it would have gone way over my head. Much of it is still new to me, so I wanted to make a section for those new to the world of power systems (like myself)  This section breaks down the core physics and jargon used in this simulation model into plain English.

---

### The Grid Analogy: The Spinning Flywheel
Think of the entire power grid as a massive, heavy, spinning flywheel. 
* **The Power Plants** (hydro, steam, gas turbines) are teams of people constantly pushing the flywheel to keep it spinning at exactly **60 Rotations Per Second (60 Hz)**.
* **The Loads** (houses, factories, and our **AI Data Center**) act like friction or brakes pushing against the flywheel.

When a massive data center suddenly starts a heavy AI training model, it's like slamming a brake onto that spinning flywheel. The flywheel will instantly begin to slow down. How fast it slows down, and how the grid recovers, is governed by a fundamental formula called the **Swing Equation**.

---

### Understanding the Swing Equation

In its simplest form, the **Swing Equation** is just Newton's Second Law ($F = ma$) rewritten for a rotating electrical grid:

$$M \left(\frac{d\omega}{dt}\right) = \Delta P - D\omega$$

Where:
* $\frac{d\omega}{dt}$ (**RoCoF**): How fast the grid's speed/frequency is changing right now.
* $M$ (**Inertia**): How heavy and hard-to-move the spinning grid is.
* $\Delta P$ (**Power Imbalance**): The difference between power being generated and power being consumed ($P_{mechanical} - P_{electrical}$).
* $D\omega$ (**Damping**): The grid's natural ability to resist speed changes.

#### Moving from Math to Simulation Blocks
To build this in a simulation tool like PSCAD or Hypersim, we need an **Integrator block** (which turns an acceleration/rate of change into a final speed/frequency). To do that, we rearrange the equation to isolate the rate of change ($\frac{d\omega}{dt}$):

$$\left(\frac{d\omega}{dt}\right) = \frac{1}{M}(\Delta P - D\omega)$$

In the simulation's **Swing Equation block**, this math is converted directly into a loop:
1. We take our power imbalance ($\Delta P$) and subtract the damping effect ($D\omega$).
2. We pass it through a Gain block of $\frac{1}{M}$ to calculate the acceleration.
3. We pass that acceleration through an Integrator block ($\frac{1}{s}$) to output the real-time **Frequency Deviation ($\omega$)**.

---
### Restoring grid balance: Governors and AGC

The swing equation models the problem, we need two components to help respond to that problem. 

1. The Governor: The Local Reflex (Primary Control)
The governor is a local, mechanical or digital throttle attached directly to each individual power plant turbine. Its job is to react **instantly** (within milliseconds to seconds) to any sudden change in grid speed.

* **How it works:** Imagine you are driving a car on cruise control and you suddenly hit a steep hill. The car naturally begins to slow down. The cruise control instantly senses this speed drop and injects more fuel into the engine to stabilize your speed. That is exactly what a governor does. When the data center turns on and grid frequency drops, the governor senses the slowdown and opens up the steam or gas valves to inject more power.
* **The Limitation (Steady-State Error):** Governors are designed with "Droop" (the `R` value in our model). Because of this, a governor **stops the bleeding, but it doesn't heal the wound.** It will stabilize the frequency so it stops dropping, but it will leave the frequency floating at a slightly lower level (e.g., 59.86 Hz instead of 60.00 Hz). To get back to exactly 60.00 Hz, we need the next layer of defense.

2. Automatic Generation Control (AGC): The Central Brain (Secondary Control)
AGC is a centralized, computerized brain operated by the grid's main control center. While governors act locally and instantly, AGC acts globally and more slowly (operating over a horizon of 10 to 30 seconds).

* **How it works:** Going back to the car analogy: your cruise control stabilized the car on the hill, but maybe it settled at 58 mph instead of your target 60 mph. AGC is like you manually tapping the "Resume/Accelerate" button a few times to force the cruise control setpoint back up until the speedometer reads exactly 60 mph.
* **In the Grid:** The AGC system constantly monitors the entire grid's frequency error. If it sees that the governors have stabilized the grid at 59.86 Hz, the AGC system sends a digital signal to multiple power plants across the network, telling them: *"Hey, adjust your baseline power up by 2%."* This wipes out the steady-state error and pulls the frequency line all the way back up to a perfect 60.00 Hz.

---
### The Power Grid Glossary

When analyzing the graphs and parameters in this repository, you will encounter several industry-specific terms. Here is what they actually mean:

#### 1. Per-Unit System (`pu`)
* **What it is:** A method of normalizing values so different sizes of equipment can be easily compared. 
* **Why we use it:** Instead of calculating raw numbers like "250,000,000 Watts" inside a "5,000,000,000 Watt" grid, we establish a **Base Power (5 GW)**. 
* **Example:** The 5 GW grid base is equal to `1.0 pu`. Therefore, a 250 MW data center load is simply represented as `0.05 pu` ($250\text{ MW} / 5000\text{ MW}$). It keeps the math clean and universal.

#### 2. Inertia Constant (`H` and `M`)
* **What it is:** $H$ is the Inertia Constant (measured in seconds). It represents how many seconds a generator can supply its rated power using *purely* the kinetic energy stored in its heavy spinning rotor. 
* **What $M$ is:** $M$ is the angular momentum, mathematically defined as $M = 2H$. 
* **Significance:** If a grid has high inertia ($H = 5$), the frequency drops very slowly when a load hits, giving the grid operators time to react. If a grid has low inertia (like a grid with mostly solar and wind, which have no heavy spinning parts), the frequency will crash incredibly fast.

#### 3. RoCoF (Rate of Change of Frequency)
* **What it is:** The derivative of frequency over time ($\frac{df}{dt}$), measured in Hz per second.
* **Significance:** This is the slope of the frequency line. If RoCoF is too high, protective relays on the grid will panic and trip offline to protect equipment, potentially causing widespread blackouts.

#### 4. Governor Droop Gain (`R`)
* **What it is:** The "throttle sensitivity" of a generator. Droop is a percentage that determines how much a generator will open its fuel/steam valves in response to a drop in frequency.
* **Why it's configured as $-1/R$:** In a control loop, a standard $5\%$ droop means $R = 0.05$. In the diagram, this is inverted as a gain block of $\frac{-1}{0.05} = -20$. This ensures that as frequency drops ($-\omega$), the governor injects a massive positive boost ($+$) of power to stabilize the system.

#### 5. Governor Time Constant (`Tg`)
* **What it is:** The physical reaction delay of the generator's governor mechanism (measured in seconds). 
* **Significance:** It dictates how long it takes for physical valves to open and mechanisms to respond after detecting a frequency drop. A small $T_g$ (e.g., 0.05s) mimics highly responsive assets like batteries, while a larger $T_g$ (e.g., 1.0s to 5.0s) mimics massive thermal power plants.

## System model

The core is a single-machine equivalent of the bulk power system, built from
control blocks in PSCAD. All quantities are in per-unit (pu) on a **5 GW system
base**, and frequency is reported in Hz around a 60 Hz nominal.

| Block | Value | Meaning |
|-------|-------|---------|
| Swing equation gain `1/M` | `0.1` | `1/(2H)` with inertia constant **H = 5 s** |
| Load damping `D` | `2` | Damping torque proportional to frequency deviation |
| Governor gain `1/Tg` | integrator (`1/sT`) with gain `20` | Turbine-governor response speed |
| Droop gain `-1/R` | `-20` | Primary frequency (droop) response, R ≈ 5% |
| AGC | integrator (`1/sT`) with gain `0.3` | Secondary control restoring frequency to nominal |
| Frequency scaling | `× 60` | Converts pu deviation to Hz (60 Hz base) |
| RoCoF block | `sT/(1+sT)` × `10` | Washout filter producing rate-of-change-of-frequency |

The datacenter is represented as a **250 MW load on the 5 GW base = 0.05 pu**.
A positive `dP_pu` is added load; a negative value is a load reduction.

## Repository contents

### `Load Trip Simulation/`

Studies an instantaneous loss of the datacenter load — a breaker opens and drops
the full 0.05 pu (250 MW) load off the system in a single step.

- `Load Trip Schematic 7-2-26.png` — PSCAD control diagram (swing equation +
  governor + AGC), fed by a step/breaker input.
- `Input (breaker state) 7-2-26.png` — the breaker signal that removes the load.
- `Frequency Deviation 7-2-26.png` — frequency overshoots to ≈ 60.14 Hz then AGC
  pulls it back to 60 Hz over ~300 s.
- `RoCoF 7-2-26.png` — rate of change of frequency at the instant of the trip.

### `Training Load Simulation/`

Drives the same system with a **real datacenter power profile** instead of a
clean step. The profile comes from an actual Llama2-70B LoRA fine-tuning job on a
16-node GPU cluster, scaled up to represent a 250 MW datacenter.

- `aggregate_training.py` — processing script (see below).
- `pscad_load_profile.csv` — full load trace, `time, dP_pu` (~10,360 samples,
  0.2 s steps). ##THIS FILE WILL NOT WORK IN PSCAD CURRENTLY, PSCAD operates on space seperated values and does not accept header row. see pscad_load_short.csv for an example of acceptable data in PSCAD##
- `pscad_load_short.csv` — 300 s trimmed window used in PSCAD, space-delimited
  with the PSCAD comment header (`! Time [s]  dP_pu ...`).
- `load_profile.png` / `load_profile_short.png` — plots of the load traces.
- `Dynamic Load Schematic 7-2-26.png` — PSCAD diagram reading the CSV as its
  input.
- `Input signal 7-2-26.png` — the load deviation applied to the model.
- `Frequency Deviation of dynamic load 7-2-26.png` — frequency response;
  continuous small oscillations (≈ ±0.05 Hz) tracking the training workload.
- `RoCoF of dynamic load 7-2-26.png` — corresponding RoCoF.

## Data source

The GPU power telemetry used in this study comes from the dataset published by
Vercellino et al. See citation below:

> Vercellino et al., "Measurement of Generative AI Workload Power Profiles for
> Whole-Facility Data Center Infrastructure Planning," arXiv:2604.07345 (2026).
> https://doi.org/10.48550/arXiv.2604.07345

## Data pipeline (`aggregate_training.py`)

The script turns raw GPU telemetry into a PSCAD-ready load signal:

1. Reads NVML power logs for a single Slurm job (`slurmid_10742842`) across the
   16-node cluster.
2. Sums per-GPU power to a total cluster power time series.
3. Removes the mean to isolate the **variation** (`dP`), preserving only the
   shape of the fluctuation.
4. Scales that variation so the cluster mean maps to a **250 MW** datacenter,
   then converts to **pu on the 5 GW base** (`dP_pu`).
5. Exports the full profile and a 300 s trimmed window (t = 250–550 s, restarted
   at 0) for simulation.

> Note: the script expects raw NVML files under
> `00_raw_datasets/training_llama2_70b_lora/16node/`. Those raw logs are **not**
> included here — only the processed CSV outputs are.
> Please go to https://data.nlr.gov/submissions/312 for full dataset.

## Key results

| Case | Input | Frequency response |
|------|-------|--------------------|
| Load trip | 0.05 pu load removed as a step | Peaks ≈ 60.14 Hz, AGC restores to 60 Hz over ~300 s |
| Dynamic training load | Llama2 16-node power trace, 250 MW scale | Sustained ≈ ±0.05 Hz oscillation tracking the workload |

## Next Steps 

Currently, this study focuses on frequency analysis. Next, I am expanding this model to look at voltage stability. If you have any reccomendations feel free to reach out to me personally. 

---

*Dated 7-2-26. All per-unit values are on a 5 GW system base with H = 5 s.*

*Disclaimer: Parts of this README file was generated with help from Claude, it is quite good at coming up with analogies for these topics, and working with LaTeX can be quite time consuming.*
