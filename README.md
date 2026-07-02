# Datacenter Load Impact on Grid Frequency — PSCAD Study

PSCAD models and results studying how a large AI datacenter load affects grid
frequency on a synchronous power system. Two cases are included: a sudden
**load trip** (breaker step) and a realistic **dynamic training load** driven by a
measured GPU power trace from a Llama2 training run.

Both models share the same reduced-order system frequency response (SFR)
representation — a swing equation with load damping, a turbine-governor, and an
automatic generation control (AGC) loop — so the two cases can be compared
directly.

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
  0.2 s steps).
- `pscad_load_short.csv` — 300 s trimmed window used in PSCAD, space-delimited
  with the PSCAD comment header (`! Time [s]  dP_pu ...`).
- `load_profile.png` / `load_profile_short.png` — plots of the load traces.
- `Dynamic Load Schematic 7-2-26.png` — PSCAD diagram reading the CSV as its
  input.
- `Input signal 7-2-26.png` — the load deviation applied to the model.
- `Frequency Deviation of dynamic load 7-2-26.png` — frequency response;
  continuous small oscillations (≈ ±0.05 Hz) tracking the training workload.
- `RoCoF of dynamic load 7-2-26.png` — corresponding RoCoF.

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

## Reproducing

- Open either `.png` schematic as a reference and rebuild in PSCAD, or load your
  `.pscx` project (add it to the repo if you want others to run it directly).
- Point the file-read component in the dynamic-load model at
  `pscad_load_short.csv`.
- To regenerate the CSVs from raw telemetry:
  ```bash
  cd "Training Load Simulation"
  pip install pandas numpy
  python aggregate_training.py
  ```

## Key results

| Case | Input | Frequency response |
|------|-------|--------------------|
| Load trip | 0.05 pu load removed as a step | Peaks ≈ 60.14 Hz, AGC restores to 60 Hz over ~300 s |
| Dynamic training load | Llama2 16-node power trace, 250 MW scale | Sustained ≈ ±0.05 Hz oscillation tracking the workload |

*Dated 7-2-26. All per-unit values are on a 5 GW system base with H = 5 s.*
