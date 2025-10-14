
import asyncio
from bleak import BleakClient, BleakScanner
import RPi.GPIO as GPIO
import struct
import time


LED_PIN = 11       # Physical pin 11 (GPIO17)
BUZZER_PIN = 13    # Physical pin 13 (GPIO27)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)            # Use physical pin numbering
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# PWM setup for LED (brightness control)
led_pwm = GPIO.PWM(LED_PIN, 1000)   # 1 kHz frequency
led_pwm.start(0)


def control_output(distance):
    """Controls LED brightness and buzzer beeping based on distance."""
    print(f"Distance: {distance:.2f} cm")

    # Limit the distance range to 0–100 cm
    distance = max(0, min(distance, 100))

    # LED brightness: closer = brighter
    if distance > 50:
        brightness = 10
    elif distance > 30:
        brightness = 40
    elif distance > 15:
        brightness = 70
    else:
        brightness = 100
    led_pwm.ChangeDutyCycle(brightness)

    # Buzzer beeps faster as object gets closer
    if distance > 50:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    elif distance > 30:
        GPIO.output(BUZZER_PIN, GPIO.HIGH); time.sleep(0.2)
        GPIO.output(BUZZER_PIN, GPIO.LOW);  time.sleep(0.5)
    elif distance > 15:
        GPIO.output(BUZZER_PIN, GPIO.HIGH); time.sleep(0.15)
        GPIO.output(BUZZER_PIN, GPIO.LOW);  time.sleep(0.2)
    else:
        GPIO.output(BUZZER_PIN, GPIO.HIGH); time.sleep(0.3)
        GPIO.output(BUZZER_PIN, GPIO.LOW)


def handle_data(sender, data):
    """Called whenever new Bluetooth data is received."""
    try:
        # Decode the 4-byte float sent by Arduino
        distance = struct.unpack('<f', data)[0]
        control_output(distance)
    except Exception:
        print("Bad data received")

async def main():
    print("Scanning for WallSensor device...")
    device = None

    # Keep scanning until we find the Arduino
    while not device:
        for d in await BleakScanner.discover(timeout=3):
            if d.name and "WallSensor" in d.name:
                device = d
                break
        if not device:
            print("WallSensor not found, retrying...")

    print(f"Connecting to: {device.address}")
    async with BleakClient(device.address) as client:
        await client.start_notify("2A6E", handle_data)
        print("Connected! Receiving distance data...")
        while True:
            await asyncio.sleep(1)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    led_pwm.stop()
    GPIO.cleanup()
