import time
import requests
from datetime import datetime
from measurement_plane.measurement_plane_client.MP_client import MeasurementPlaneClient

USERNAME = "admin"
PASSWORD = "root"

def create_crossconnect(ingress, egress, url):
    pair_path = f"/pair={ingress}"
    data = f"<pair><ingress>{ingress}</ingress><egress>{egress}</egress></pair>"
    full_url = url + pair_path
    r = requests.put(full_url, data=data,
                     headers={"Accept": "application/yang-data+xml", "Content-Type": "application/yang-data+xml"},
                     auth=(USERNAME, PASSWORD))
    return r.status_code in [201, 204]

def delete_all_crossconnects(url):
    requests.delete(url,
                    headers={"Accept": "application/yang-data+xml", "Content-Type": "application/yang-data+xml"},
                    auth=(USERNAME, PASSWORD))
    
def delete_crossconnect(ingress_port, base_url):
    url = f"{base_url}/pair={ingress_port}"
    response = requests.delete(
        url,
        headers={"Accept": "application/yang-data+xml", "Content-Type": "application/yang-data+xml"},
        auth=(USERNAME, PASSWORD)
    )
    return response.status_code == 204

def init_mp_client(broker_url):
    return MeasurementPlaneClient(broker_url)

def measure_counts(mp_client: MeasurementPlaneClient, capability_id, channel, timeout=5):
    results = []

    def on_result_callback(result):
        results.append(result[-1])

    capabilities = mp_client.get_capabilities()
    capability = capabilities[capability_id]
    measurement = mp_client.create_measurement(capability)

    measurement.configure(
        schedule="now||stream",
        parameters={"channels": str(channel)},
        stream_results=False,
        redirect_to_storage=False,
        result_callback=on_result_callback,
        completion_callback=None
    )
    mp_client.send_measurement(measurement)
    time.sleep(timeout)
    mp_client.interrupt_measurement(measurement)

    # Extract count rates for the specified channel
    count_rates = [r.get(channel) for r in results if channel in r]

    if count_rates:
        return sum(count_rates) / len(count_rates)
    else:
        return -1
    
    
    
    
def select_capability(mp_client):
    import pandas as pd
    from IPython.display import display, clear_output
    import time
    from tabulate import tabulate

    while True:
        print("🔄 Loading capabilities...")
        time.sleep(1)  # Allow some time for late announcements
        while True:
            capabilities = mp_client.get_capabilities()
            if capabilities:
                break
            time.sleep(1)  # Wait for capabilities to be available

        # Format and display table
        capability_items = list(capabilities.items())
        table = pd.DataFrame([
            {
                "Index": idx + 1,
                "Capability ID": cap_id,
                "Endpoint": cap.get("endpoint", "N/A"),
                "Name": cap.get("capabilityName", cap.get("label", "Unnamed"))
            }
            for idx, (cap_id, cap) in enumerate(capability_items)
        ])
        clear_output(wait=True)
        #display(table[["Index", "Endpoint", "Name"]].set_index("Index"))
        #print(table[["Index", "Endpoint", "Name"]].to_string(index=False))
        # Build the table
        table_data = [
            [idx + 1, cap.get("endpoint", "N/A"), cap.get("capabilityName", cap.get("label", "Unnamed"))]
            for idx, (cap_id, cap) in enumerate(capability_items)
        ]
        headers = ["Index", "Endpoint", "Name"]

        # Pretty print with lines
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        user_input = input("Choose a capability index or press Enter to retry, or type 'q' to quit: ").strip().lower()
        if user_input == 'q':
            return None
        elif user_input == '':
            continue  # Retry

        try:
            idx = int(user_input)
            if 1 <= idx <= len(capability_items):
                selected_id, selected_cap = capability_items[idx - 1]
                name = selected_cap.get("capabilityName", selected_cap.get("label", "Unnamed"))
                ep = selected_cap.get("endpoint", "N/A")
                print(f"\n✅ Selected Capability: '{name}' @ endpoint '{ep}'")
                return selected_id
            else:
                print("❌ Invalid index. Try again.")
        except ValueError:
            print("❌ Please enter a valid integer or press Enter to reload.")
