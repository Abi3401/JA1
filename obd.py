import customtkinter as ctk
import obd
import time
import threading
import csv
import subprocess
from datetime import datetime
import RPi.GPIO as GPIO

# --- CONFIGURATION ---
WIFI_SSID = "WiFi_OBDII"  # CHANGE THIS to your exact dongle name
OBD_PORT = "socket://192.168.0.10:35000"
FLOW_SENSOR_PIN = 17 # BCM Pin 17

# --- THE DASHBOARD APP ---
class CarDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. SETUP WINDOW FOR 1920x1080
        self.title("OBDII Dashboard 1080p")
        self.geometry("1920x1080")
        self.attributes('-fullscreen', True) 
        ctk.set_appearance_mode("Dark")
        
        # System Variables
        self.running = False
        self.connection = None
        self.csv_file = None
        self.writer = None

        # STORAGE FOR "LAST KNOWN VALUE"
        self.val_rpm = 0
        self.val_speed = 0
        self.val_cool = 0
        
        # FLOW SENSOR VARIABLES
        self.val_flow = 0.0
        self.pulse_count = 0
        
        # Setup GPIO for the Flow Sensor
        GPIO.setmode(GPIO.BCM)
        # Pull up resistor prevents false triggering from electrical noise
        GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Background listener that triggers on every pulse
        GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=self.count_pulse)
        
        # Layout: Grid System
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure(0, weight=3) # Gauges Area
        self.grid_rowconfigure(1, weight=1) # Buttons Area

        # --- GAUGES (SCALED UP FOR 1080p) ---
        self.lbl_speed = self.create_gauge("SPEED", "0", "km/h", 0, 0)
        self.lbl_rpm = self.create_gauge("RPM", "0", "rpm", 0, 1)
        self.lbl_coolant = self.create_gauge("COOLANT", "0", "°C", 0, 2)
        # Replaced Oil gauge with Flow Rate gauge
        self.lbl_flow = self.create_gauge("FLOW RATE", "0.0", "L/min", 0, 3)

        # --- BUTTONS (SCALED UP) ---
        self.btn_wifi = ctk.CTkButton(self, text="CONNECT WIFI", command=self.connect_wifi, 
                                      fg_color="#0066CC", height=120, font=("Arial", 30, "bold"))
        self.btn_wifi.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        self.btn_start = ctk.CTkButton(self, text="START LOG", command=self.start_logging, 
                                       fg_color="#009933", height=120, font=("Arial", 30, "bold"), state="disabled")
        self.btn_start.grid(row=1, column=1, padx=20, pady=20, sticky="ew")

        self.btn_stop = ctk.CTkButton(self, text="STOP", command=self.stop_logging, 
                                      fg_color="#CC0000", height=120, font=("Arial", 30, "bold"), state="disabled")
        self.btn_stop.grid(row=1, column=2, padx=20, pady=20, sticky="ew")

        self.btn_exit = ctk.CTkButton(self, text="EXIT & SAVE", command=self.close_app, 
                                      fg_color="#555555", height=120, font=("Arial", 30, "bold"))
        self.btn_exit.grid(row=1, column=3, padx=20, pady=20, sticky="ew")

        # Status Bar
        self.lbl_status = ctk.CTkLabel(self, text="Status: Disconnected", text_color="gray", font=("Arial", 24))
        self.lbl_status.grid(row=2, column=0, columnspan=4, pady=10)

    def count_pulse(self, channel):
        """Hardware interrupt that increments every time the rotor spins"""
        self.pulse_count += 1

    def create_gauge(self, title, value, unit, r, c):
        frame = ctk.CTkFrame(self)
        frame.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=("Arial", 32)).pack(pady=(40, 0))
        lbl_value = ctk.CTkLabel(frame, text=value, font=("Arial", 140, "bold"), text_color="#33CCFF")
        lbl_value.pack(expand=True)
        ctk.CTkLabel(frame, text=unit, font=("Arial", 28)).pack(pady=(0, 40))
        return lbl_value

    def connect_wifi(self):
        self.lbl_status.configure(text="Connecting to WiFi...", text_color="yellow")
        self.update()
        cmd = f'nmcli dev wifi connect "{WIFI_SSID}"'
        try:
            subprocess.run(cmd, shell=True, check=True)
            self.lbl_status.configure(text=f"WiFi Connected to {WIFI_SSID}", text_color="green")
            self.connect_obd()
        except subprocess.CalledProcessError:
            self.lbl_status.configure(text="WiFi Connection Failed", text_color="red")

    def connect_obd(self):
        self.lbl_status.configure(text="Connecting to ECU...", text_color="yellow")
        self.update()
        try:
            self.connection = obd.OBD(OBD_PORT, check_voltage=False, fast=True, timeout=5, protocol="6")
            if self.connection.is_connected():
                self.lbl_status.configure(text="ECU Connected! Ready to Log.", text_color="#00FF00")
                self.btn_start.configure(state="normal")
                self.btn_wifi.configure(state="disabled") 
            else:
                self.lbl_status.configure(text="ECU Connection Failed", text_color="red")
        except Exception as e:
            self.lbl_status.configure(text=f"Error: {str(e)}", text_color="red")

    def start_logging(self):
        if not self.connection or not self.connection.is_connected(): return
        
        filename = f"Trip_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = open(filename, mode='w', newline='')
        self.writer = csv.writer(self.csv_file)
        # Added Flow_Lmin to the CSV Header
        self.writer.writerow(["Timestamp", "RPM", "Speed", "Coolant", "Flow_Lmin"])

        self.running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text=f"LOGGING TO: {filename}", text_color="#00FF00")
        
        threading.Thread(target=self.logging_loop, daemon=True).start()

    def stop_logging(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="Logging Stopped. File Saved.", text_color="white")
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None

    def close_app(self):
        self.stop_logging()
        GPIO.cleanup() # Critical: Release the hardware pins on exit
        self.destroy()

    def logging_loop(self):
        cmd_rpm = obd.commands.RPM
        cmd_speed = obd.commands.SPEED
        cmd_cool = obd.commands.COOLANT_TEMP
        
        last_logged_time = None

        while self.running:
            # 1. Query OBD Data
            rpm = self.connection.query(cmd_rpm, force=True)
            speed = self.connection.query(cmd_speed, force=True)
            cool = self.connection.query(cmd_cool, force=True)

            if not rpm.is_null(): self.val_rpm = int(rpm.value.magnitude)
            if not speed.is_null(): self.val_speed = int(speed.value.magnitude)
            if not cool.is_null(): self.val_cool = int(cool.value.magnitude)

            # 2. Process Flow Math & Log Data (Exactly once per second)
            current_time = datetime.now().strftime('%H:%M:%S')

            if self.writer and current_time != last_logged_time:
                # Calculate flow rate based on pulses received in the last 1 second
                # Formula for YF-DN40: Q = Frequency / 0.45
                self.val_flow = round(self.pulse_count / 0.45, 2)
                
                # Reset pulse counter for the next second
                self.pulse_count = 0 
                
                # Write to CSV
                self.writer.writerow([current_time, self.val_rpm, self.val_speed, self.val_cool, self.val_flow])
                self.csv_file.flush()
                last_logged_time = current_time

            # 3. Update GUI
            self.after(0, self.update_labels, self.val_rpm, self.val_speed, self.val_cool, self.val_flow)
            time.sleep(0.1)

    def update_labels(self, rpm, speed, cool, flow):
        self.lbl_rpm.configure(text=str(rpm))
        self.lbl_speed.configure(text=str(speed))
        self.lbl_coolant.configure(text=str(cool))
        self.lbl_flow.configure(text=str(flow))

if __name__ == "__main__":
    app = CarDashboard()
    app.mainloop()
