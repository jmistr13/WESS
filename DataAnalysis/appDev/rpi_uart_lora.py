import serial
import time
import csv
import re
from datetime import datetime

# Method to create new file. New file is generated after 1000 rows
def generate_new_file():
	# Set up variables and parameters
	global filename, row_count
	file_date = datetime.now().strftime("%Y-%m-%d")
	filename = "2025-03-12_readings.csv" # constant for now
	row_count = 0 # New file created after 1000 rows, reset counter when new file is generated
	
	# Add header to csv
	with open(filename, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(["sensorName","lat","long","transmitDateTime", "CO","NH3","N02","TDS","turbidity"])

file_date = datetime.now().strftime("%Y-%m-%d")
filename = f"{file_date}_readings.csv"

#setup lora connection
lora = serial.Serial(
	port="/dev/ttyAMA0",
	baudrate=115200,
	timeout=1,
	)

#setup lora params
lora.write(str.encode("AT+BAND=915000000\r\n"))
time.sleep(1)
lora.write(str.encode("AT+NETWORK_ID=5\r\n"))
time.sleep(1)
lora.write(str.encode("AT+ADDRESS=2\r\n"))
time.sleep(1)

with open(filename, 'a', newline='') as file:
	writer = csv.writer(file)
	
	# if file is empty, add header
	if file.tell() == 0:
		writer.writerow(["sensorName","lat","long","transmitDateTime", "CO","NO2","NH3","TDS","turbidity"])
	while True: # maybe change this to when theres an actual line to read?
		if lora.in_waiting > 0: # Run if there is incoming data
			msg = lora.readline()
			if "+OK" in msg.decode() or "+ERR" in msg.decode():
				continue
			print(msg.decode(errors="ignore").strip())
			
			vals = re.findall(r"[-+]?(?:\d*\.\d+)", msg.decode()) # Get incoming data vals
			now = datetime.now() # Take current system datetime
			date_time_str = now.strftime("%Y-%m-%d %H:%M:%S") # Create datetime string
			vals.insert(2, date_time_str) # Add datetime string to vals
			
			sensor_name = msg.decode().split(",") # get sensor name
			if (len(sensor_name) > 1):
				sensor_name = sensor_name[2]
				vals.insert(0, sensor_name) # add sensor name to vals
			else:
				vals.insert(0, 'unknown') # if no sensor name, add unknown
			
			print(vals)
			writer.writerow(vals)	
			file.flush() #push change to disk	
			time.sleep(1)
			
		else: # Sleep if no incoming data
			time.sleep(1)

lora.close()
