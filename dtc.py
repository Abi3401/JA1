
import obd
import time

# 1. Define the wireless network socket connection for the Wi-Fi ELM327 dongle
OBD_PORT = "socket://192.168.0.10:35000"

print("Connecting to Wi-Fi OBD-II adapter...")

try:
    # 2. Establish connection to the dongle using the network socket
    connection = obd.OBD(OBD_PORT)
    
    # Check if the connection to the adapter and car ECU was successful
    if connection.status() == obd.OBDStatus.CAR_CONNECTED:
        print("Successfully connected to the vehicle ECU!")
        print("------------------------------------------")
        
        # 3. Query Mode 03 (Diagnostic Trouble Codes)
        print("Scanning for diagnostic trouble codes (DTCs)...")
        response = connection.query(obd.commands.GET_DTC)
        
        # 4. Parse and display the results
        if response.value:
            print(f"\nFound {len(response.value)} error code(s):")
            for code, description in response.value:
                print(f" -> {code}: {description}")
        else:
            print("\nNo errors found! The ECU clear flag is active.")
            
    else:
        print("\n[ERROR] Connected to adapter, but cannot talk to the car ECU.")
        print("Ensure the car ignition key is turned to the 'ON' position.")

except Exception as e:
    print(f"\n[CONNECTION FAILED] Could not open socket to {OBD_PORT}")
    print(f"Error details: {e}")
    print("Please verify that your Raspberry Pi is connected to the 'WIFI_OBDII' hotspot.")
