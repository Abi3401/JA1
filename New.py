import RPi.GPIO as GPIO
import time

# --- CONFIGURATION ---
FLOW_SENSOR_PIN = 17       # BCM Pin 17
CALIBRATION_FACTOR = 0.33  # Your custom tested constant

# --- VARIABLES ---
pulse_count = 0
pulse_history = [0, 0, 0]  # 3-second memory buffer for smoothing

# --- INTERRUPT FUNCTION ---
def count_pulse(channel):
    global pulse_count
    pulse_count += 1

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=count_pulse)

print("Flow Sensor Minimal Test Started")
print("Press Ctrl+C to stop")
print("-" * 35)

# --- MAIN LOOP ---
try:
    while True:
        time.sleep(1) # Wait exactly 1 second

        # 1. Update the moving average history
        pulse_history.pop(0)
        pulse_history.append(pulse_count)

        # 2. Reset the live counter immediately for the next second
        pulse_count = 0

        # 3. Calculate the average pulses over 3 seconds
        avg_pulses = sum(pulse_history) / len(pulse_history)

        # 4. Calculate the flow rate using your calibration
        flow_rate = round(avg_pulses / CALIBRATION_FACTOR, 2)

        print(f"Flow Rate: {flow_rate} L/min")

except KeyboardInterrupt:
    print("\nExiting and releasing hardware pins...")
    GPIO.cleanup()
