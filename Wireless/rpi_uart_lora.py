import serial
import time

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
		
while True:
	msg = lora.readline()
	print(msg.decode(errors="ignore").strip())

lora.close()
