import obd

# Auto-connect to the ELM327
connection = obd.OBD() 

# --- READ THE ERRORS (Mode 03) ---
response = connection.query(obd.commands.GET_DTC)

if not response.is_null():
    # This returns a list of tuples: [("P0133", "Oxygen Sensor Circuit..."), ...]
    for code, description in response.value:
        print(f"Error Found: {code} - {description}")
else:
    print("No errors found!")

# --- CLEAR THE ERRORS (Mode 04) ---
# connection.query(obd.commands.CLEAR_DTC)
