String lora_band = "915000000"; //enter band as per your country
String lora_networkid = "5";    //enter Lora Network ID
String lora_address = "3";      //enter Lora address

int CO_pin = A0;
int NH3_pin = A1;
int NO2_pin = A2;
int NH3Value = 0;
int COValue = 0;
int NO2Value = 0;
int mappedCOValue = 0;
int mappedNH3Value = 0;
int mappedNO2Value = 0;
void setup() {
  Serial.begin(9600); // Start serial communication
  Serial1.begin(115200);
  pinMode(CO_pin, INPUT);
  pinMode(NH3_pin, INPUT);
  pinMode(NO2_pin, INPUT);

  delay(1500);
  Serial1.println("AT+BAND=" + lora_band);
  delay(500);
  Serial1.println("AT+NETWORKID=" + lora_networkid);
  delay(500);
  Serial1.println("AT+ADDRESS=" + lora_address);
  delay(1000);
  Serial.println("Initialised");
}

void loop() {
  // Read the analog value from pin A0
  COValue = analogRead(CO_pin);
  NH3Value = analogRead(NH3_pin);
  NO2Value = analogRead(NO2_pin);

  // Map the sensor value from the range 0-1023 to 0-50
  mappedCOValue = map(COValue, 0, 1023, 0, 15);
  mappedNH3Value = map(NH3Value, 0, 1023, 0, 15);
  mappedNO2Value = map(NO2Value, 0, 1023, 0, 3);

  String transmission = "AT+SEND=2,";
  String payload = "dummy,69.420,13.37," + String(mappedCOValue) + "," + String(mappedNH3Value) + "," + String(mappedNO2Value) + ",,";
  String l = String(payload.length()) + ",";
  transmission += l + payload;
  Serial1.println(transmission);
  Serial.println("Values sent");

  delay(1800000); // Delay to make the output readable
}
