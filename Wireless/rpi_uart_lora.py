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
	writer.writerow(["transmitDateTime", "CO","NO2","NH3","TDS"])
	
	while True:
		msg = lora.readline()
		print(msg.decode(errors="ignore").strip())
		vals = re.findall(r"[-+]?(?:\d*\.\d+)", msg.decode())
		
		now = datetime.now()
		date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
		vals.insert(0, date_time_str)
		print(vals)
		writer.writerow(vals)
		file.flush()
		time.sleep(5)

lora.close()
