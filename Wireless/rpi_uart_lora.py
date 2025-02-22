import serial
import time
import csv
import re

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
	writer.writerow(["CO","NO2","NH3","TDS"])
	
	while True:
		msg = lora.readline()
		print(msg.decode(errors="ignore").strip())
		vals = re.findall(r"[-+]?(?:\d*\.\d+)", msg.decode())
		writer.writerow(vals)
		time.sleep(5)

lora.close()
