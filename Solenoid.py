import RPi.GPIO as GPIO
import time

SOLENOID_PIN = 4

blinkTime = 0.5

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_PIN,GPIO.OUT)

try:
    while True:
        GPIO.output(SOLENOID_PIN,GPIO.HIGH)
        time.sleep(blinkTime)
except KeyboardInterrupt:
    GPIO.cleanup()
