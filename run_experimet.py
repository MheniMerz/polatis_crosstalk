from cross_talk_lib import *
import pandas as pd

# Set constants
BROKER_URL = "http://localhost:5672/"
SWITCH_API = "http://192.168.56.10:8008/api/data/optical-switch:cross-connects"
CSV_FILE = "data/64x64-noise-measurement.csv"
channel = 1  # adjust to match your Time Tagger channel

# Init MP client
mp_client = init_mp_client(BROKER_URL)
capability_id = select_capability(mp_client)

# Define switch type presets
SWITCH_TYPES = {
    "1": ("8x8", 1, 8, 9, 16),
    "2": ("64x64", 1, 64, 65, 128),
    "3": ("test64x64", 1, 8, 65, 72)
}

# Prompt user to select
print("Select Polatis switch type:")
for key, (label, _, _, _, _) in SWITCH_TYPES.items():
    print(f"  [{key}] {label}")


while True:
    choice = input("Enter your choice: ").strip()
    if choice in SWITCH_TYPES:
        label, in_start, in_end, out_start, out_end = SWITCH_TYPES[choice]
        ingress_range = in_end - in_start + 1
        egress_range = out_end - out_start + 1
        ingress_ports = list(range(in_start, in_end + 1))
        egress_ports = list(range(out_start, out_end + 1))
        print(f"✅ Selected: {label} — Ingress ports {in_start}-{in_end}, Egress ports {out_start}-{out_end}")
        break
    else:
        print("❌ Invalid choice. Please select from the menu.")

# Ask the user for the list of TT channels to use
while True:
    user_input = input("Enter the list of TT channels in use (e.g., 1 2 5 7): ").strip()
    try:
        tt_channels = sorted(set(int(ch) for ch in user_input.split() if int(ch) > 0))
        if not tt_channels:
            raise ValueError
        print(f"✅ Accepted TT channels: {tt_channels}")
        break
    except ValueError:
        print("❌ Please enter a space-separated list of positive integers without duplicates.")

# Cleanup any existing cross-connects

delete_all_crossconnects(SWITCH_API)

# Break egress ports into chunks matching TT channel count
tt_channel_count = len(tt_channels)
egress_chunks = [egress_ports[i:i+tt_channel_count] for i in range(0, len(egress_ports), tt_channel_count)]
print(egress_chunks)
for classical_in in ingress_ports:
    print(f"\n🔌 Please connect the CLASSICAL LASER to INGRESS port {classical_in}")
    input("Press Enter once connected...")
    for e_chunk_idx, egress_chunk in enumerate(egress_chunks):
        print("\n🧠 Prepare for quantum measurements:")
        print("🔌 Please connect the following EGRESS ports to the corresponding Time Tagger (TT) channels:\n")
        for idx, quantum_out in enumerate(egress_chunk):
            tt_channel = tt_channels[idx]
            print(f"    - EGRESS port {quantum_out} → TT channel {tt_channel}")

        input("\n✅ Once all connections are made, press Enter to continue...")
        for idx, quantum_out in enumerate(egress_chunk):
            tt_channel = tt_channels[idx]
            for classical_out in egress_ports:
                if classical_out == quantum_out:
                    continue
                print(f"\n🔌 Classical out is {classical_out} No Action Needed!")
                # Create Classical cross-connect
                create_crossconnect(classical_in, classical_out, SWITCH_API)
                print(f"🔌 Created classical cross-connect from {classical_in} to {classical_out}")
                for quantum_in in ingress_ports:
                    if quantum_in == classical_in:
                        continue
                    ok = create_crossconnect(quantum_in, quantum_out, SWITCH_API)
                    if not ok:
                        print(f"❌ Failed to connect {quantum_in} -> {quantum_out}")
                        continue
                    print(f"🔌 Created quantum cross-connect from {quantum_in} to {quantum_out}")
                    print(f"🔄 Measuring counts from {tt_channel}...")

            
        
