import pandas as pd
import os
import glob
import numpy as np

raw_path = "00_raw_datasets/training_llama2_70b_lora/16node/"

all_files = glob.glob(os.path.join(raw_path, "*nvml*"))
print(f"Total nvml files: {len(all_files)}")

selected_slurm = "10742842"
gpu_files = [f for f in all_files if f"slurmid_{selected_slurm}_" in f]
print(f"Files for slurm {selected_slurm}: {len(gpu_files)}")

combined_power = None
timestamps = None

for f in gpu_files:
    df = pd.read_csv(f, sep=r'\s+', comment='#', header=None)
    power = df.iloc[:, 2:6].sum(axis=1)
    
    if combined_power is None:
        timestamps = df.iloc[:, 0]
        combined_power = power
    else:
        min_len = min(len(combined_power), len(power))
        combined_power = combined_power.iloc[:min_len].reset_index(drop=True) + power.iloc[:min_len].reset_index(drop=True)
        timestamps = timestamps.iloc[:min_len].reset_index(drop=True)

result = pd.DataFrame({
    "timestamp": timestamps,
    "power_w": combined_power
})

print(f"Max: {result['power_w'].max()/1e6:.2f} kW")
print(f"Min: {result['power_w'].min()/1e6:.2f} kW")
print(f"Mean: {result['power_w'].mean()/1e6:.2f} kW")

# Convert mW to kW for easier handling
result["power_kw"] = result["power_w"] / 1e6

# Subtract mean to get the deviation signal
mean_kw = result["power_kw"].mean()
result["dP_kw"] = result["power_kw"] - mean_kw

# Scale: 16-node cluster → 250 MW DC
# Mean cluster = 34.13 kW represents the "mean DC load" 
# So scale factor preserves the SHAPE of variation
scale_factor = 250_000 / mean_kw  # kW to kW ratio, then we're in DC's MW scale
result["dP_mw"] = result["dP_kw"] * scale_factor / 1000  # back to MW

# Convert to pu on 5 GW system base
result["dP_pu"] = result["dP_mw"] / 5000

# Create relative timestamp
result["time"] = (pd.to_datetime(result["timestamp"], format="%Y-%m-%d_%H:%M:%S.%f") - 
                  pd.to_datetime(result["timestamp"].iloc[0], format="%Y-%m-%d_%H:%M:%S.%f")).dt.total_seconds()

# Trim to 300 seconds starting at t=250
short = result[(result["time"] >= 250) & (result["time"] <= 550)].copy()
short["time"] = short["time"] - short["time"].iloc[0]  # restart at 0

# Write with PSCAD-required comment header
with open("pscad_load_short.csv", "w", newline='') as f:
    f.write("! Time [s]   dP_pu    -- Llama2 16-node training trace scaled to 250MW DC on 5GW base\n")
    short[["time", "dP_pu"]].to_csv(f, index=False, header=False, sep=' ', lineterminator='\n')
print(f"Short version: {len(short)} samples, {short['time'].max():.1f}s duration")

# Export full profile
pscad_df = result[["time", "dP_pu"]]
pscad_df.to_csv("pscad_load_profile.csv", index=False)

print(f"\nDC scale: 250 MW on 5 GW base = 0.05 pu base load")
print(f"Max dP: {result['dP_pu'].max():.5f} pu  ({result['dP_mw'].max():.1f} MW)")
print(f"Min dP: {result['dP_pu'].min():.5f} pu  ({result['dP_mw'].min():.1f} MW)")
print(f"Duration: {result['time'].max():.1f} seconds")
print(f"Samples: {len(result)}")
