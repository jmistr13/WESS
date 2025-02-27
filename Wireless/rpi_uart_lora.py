import serial
import time
import csv
import re
from datetime import datetime

lora = serial.Serial(
	port="/dev/ttyAMA0",
	baudrate=115200,
	timeout=1,
	)
		
lora.write(str.encode("AT+BAND=915000000\r\n"))
time.sleep(1)
lora.write(str.encode("AT+NETWORK_ID=5\r\n"))
time.sleep(1)
lora.write(str.encode("AT+ADDRESS=2\r\n"))
time.sleep(1)

with open("readings.csv", 'w', newline='') as file:
	writer = csv.writer(file)
	writer.writerow(["sensorName","lat","long","transmitDateTime", "CO","NO2","NH3","TDS","turbidity"])
	
	while True: #maybe change this to when theres an actual line to read?
		if lora.in_waiting > 0:
			msg = lora.readline()
			if "+OK" in msg.decode() or "+ERR" in msg.decode():
				continue
			print(msg.decode(errors="ignore").strip())
			vals = re.findall(r"[-+]?(?:\d*\.\d+)", msg.decode())
			now = datetime.now()
			date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
			vals.insert(2, date_time_str)
			sensor_name = msg.decode().split(",")
			if (len(sensor_name) > 1):
				sensor_name = sensor_name[2]
				vals.insert(0, sensor_name)
			print(vals)
			writer.writerow(vals)
			file.flush()
			time.sleep(1)
		else:
			time.sleep(1)

lora.close()
