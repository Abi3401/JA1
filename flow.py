import RPi.GPIO as GPIO
import time

FLOW_PIN = 17
pulse_count = 0

def count_pulse(channel):
    global pulse_count
    pulse_count += 1

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(FLOW_PIN, GPIO.FALLING, callback=count_pulse)

print("Flow Sensor Test Started!")
print("Blow into the sensor or spin the rotor...")
print("-" * 40)

try:
    while True:
        time.sleep(1) # Wait 1 second
        flow_rate = round(pulse_count / 0.45, 2)
        print(f"Raw Pulses: {pulse_count} | Flow Rate: {flow_rate} L/min")
        pulse_count = 0 # Reset for the next second
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nTest Stopped safely.")
