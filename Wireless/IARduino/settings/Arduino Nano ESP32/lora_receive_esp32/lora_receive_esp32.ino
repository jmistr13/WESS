String lora_band = "915000000"; //enter band as per your country
String lora_networkid = "5";    //enter Lora Network ID
String lora_address = "2";      //enter Lora address

String incomingString;

void setup()
{
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, D3, D2);
   
  
  delay(1500);
  Serial1.println("AT+BAND=" + lora_band);
  delay(500);
  Serial1.println("AT+NETWORKID=" + lora_networkid);
  delay(500);
  Serial1.println("AT+ADDRESS=" + lora_address);
  delay(1000);
  Serial.println("Initialised");
  
}

void loop()
{ 
  if(Serial1.available()) {
    incomingString = Serial1.readString();
    Serial.println(incomingString);
  }
}
