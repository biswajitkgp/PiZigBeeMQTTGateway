import paho.mqtt.client as mqtt
import serial
import time
import requests
from datetime import datetime
import pytz

# Serial port setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.flush()

# MQTT setup
broker_address = "13.235.151.163"
port = 1883  # Default MQTT port, change if needed
topic = "test"

# URLs to fetch scale factors for each ADC
scale_factor_url_adc1 = "http://skubotics.in/clients/rail/api/get-scale-factor.php?cpu=3&adc=1"
scale_factor_url_adc2 = "http://skubotics.in/clients/rail/api/get-scale-factor.php?cpu=3&adc=2"
scale_factor_url_adc3 = "http://skubotics.in/clients/rail/api/get-scale-factor.php?cpu=3&adc=3"
scale_factor_url_adc4 = "http://skubotics.in/clients/rail/api/get-scale-factor.php?cpu=3&adc=4"

# Fetch scale factors
def fetch_scale_factors(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        scale_factors = response.text.strip().split(',')
        # Convert to floats and pad with 1s if less than 16
        scale_factors = [float(sf) for sf in scale_factors]
        if len(scale_factors) < 16:
            scale_factors.extend([1.0] * (16 - len(scale_factors)))
        return scale_factors
    except requests.RequestException as e:
        print(f"Failed to fetch scale factors: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response received'}")
        return [1.0] * 16

# MQTT client setup
client = mqtt.Client("RaspberryPi")
client.username_pw_set(username="your_username", password="your_password")  # Add if your broker requires authentication

# Connect to MQTT broker
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    
    client.on_connect = on_connect
    client.connect(broker_address, port)
    client.loop_start()

def publish(client, data):
    result = client.publish(topic, data)
    status = result[0]
    if status == 0:
        print(f"Sent {data} to topic {topic}")
    else:
        print(f"Failed to send message to topic {topic}")

connect_mqtt()
scale_factors1 = fetch_scale_factors(scale_factor_url_adc1)
scale_factors2 = fetch_scale_factors(scale_factor_url_adc2)
scale_factors3 = fetch_scale_factors(scale_factor_url_adc3)
scale_factors4 = fetch_scale_factors(scale_factor_url_adc4)

# Variables to retain previous values for each ADC
ADC1_A1 = ADC1_A2 = 0.0
ADC2_A1 = ADC2_A2 = 0.0
ADC3_A1 = ADC3_A2 = 0.0
ADC4_A1 = ADC4_A2 = 0.0

while True:
    current_adc = None  # Initialize current_adc to None at the start of each iteration

    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        print(f"Read from serial: {line}")

        # Update the respective ADC variables based on the serial data
        if line.startswith("**S0E51**") and line.endswith("**R2**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 1
            ADC1_A1 = float(line.split("**")[2])
        elif line.startswith("**S1E51**") and line.endswith("**R2**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 1
            ADC1_A2 = float(line.split("**")[2])
        elif line.startswith("**S0E52**") and line.endswith("**R2**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 2
            ADC2_A1 = float(line.split("**")[2])
        elif line.startswith("**S1E52**") and line.endswith("**R2**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 2
            ADC2_A2 = float(line.split("**")[2])
        elif line.startswith("**S0E53**") and line.endswith("**R1**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 3
            ADC3_A1 = float(line.split("**")[2])
        elif line.startswith("**S1E53**") and line.endswith("**R1**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 3
            ADC3_A2 = float(line.split("**")[2])
        elif line.startswith("**S0E54**") and line.endswith("**R1**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 4
            ADC4_A1 = float(line.split("**")[2])
        elif line.startswith("**S1E54**") and line.endswith("**R1**"):
            cycle_start_time = time.time()  # Record the start time of the cycle
            current_adc = 4
            ADC4_A2 = float(line.split("**")[2])

        # Convert ADC values to voltage and scale them for the current ADC
        if current_adc == 1:
            V1 = (ADC1_A1 / 1023.0) * 5
            V2 = (ADC1_A2 / 1023.0) * 5
            scaled_V1 = round(V1 * scale_factors1[0], 2)
            scaled_V2 = round(V2 * scale_factors1[1], 2)
            A_values = [scaled_V1, scaled_V2]
        elif current_adc == 2:
            V1 = (ADC2_A1 / 1023.0) * 5
            V2 = (ADC2_A2 / 1023.0) * 5
            scaled_V1 = round(V1 * scale_factors2[0], 2)
            scaled_V2 = round(V2 * scale_factors2[1], 2)
            A_values = [scaled_V1, scaled_V2]
        elif current_adc == 3:
            V1 = (ADC3_A1 / 1023.0) * 5
            V2 = (ADC3_A2 / 1023.0) * 5
            scaled_V1 = round(V1 * scale_factors3[0], 2)
            scaled_V2 = round(V2 * scale_factors3[1], 2)
            A_values = [scaled_V1, scaled_V2]
        elif current_adc == 4:
            V1 = (ADC4_A1 / 1023.0) * 5
            V2 = (ADC4_A2 / 1023.0) * 5
            scaled_V1 = round(V1 * scale_factors4[0], 2)
            scaled_V2 = round(V2 * scale_factors4[1], 2)
            A_values = [scaled_V1, scaled_V2]

        # If we have identified an ADC and its values, construct the MQTT message
        if current_adc is not None:
            A_values += [0.0] * (16 - len(A_values))  # Pad with zeros if necessary
            D_values = [0] * 10  # D1 to D10 values

            # Get the current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime("%Y-%m-%d#%H:%M:%S")

            mqtt_message = f"CPU3#ADC{current_adc}#"
            mqtt_message += ",".join(map(str, A_values)) + ","
            mqtt_message += ",".join(map(str, D_values)) + "#"
            mqtt_message += timestamp

            print(f"MQTT Message: {mqtt_message}")

            # Publish the MQTT message
            publish(client, mqtt_message)

            cycle_end_time = time.time()  # Record the end time after publishing
            cycle_duration = cycle_end_time - cycle_start_time  # Calculate the cycle duration

            # Print the time taken for the serial read and MQTT transmission cycle
            print(f"Cycle time for ADC{current_adc}: {cycle_duration:.2f} seconds ({cycle_duration*1000:.2f} ms)")
