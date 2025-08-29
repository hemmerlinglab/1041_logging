// Setups
const float VREF = 3.3f;            // ADC reference voltage
const int BITS = 12;                // ADC resolution
const unsigned long PERIOD = 10;    // ADC frequency, in ms
const unsigned long BRATE = 115200; // Arduino baudrate

// Auto configurations
const float scale = VREF / ((1 << BITS) - 1);    // ADC scale conversion factor
unsigned long last = 0;                          // Last time, in ms

// Initialization
void setup() {
  
  // Set ADC resolution of Arduino
  analogReadResolution(BITS);

  // Set baudrate of Arduino
  Serial.begin(BRATE);

  // Standby and wait until the client is connected
  while (!Serial) { ; }
  
}

// Main loop
void loop() {
  // Output period management
  unsigned long now = millis();
  if ((now - last) < PERIOD) return;
  last = now;

  //read the input on analog pin 0:
  int sensorValue_room = analogRead(A0);
  int sensorValue_cryo = analogRead(A1);
  int sensorValue_ICR = analogRead(A2);
  int sensorValue_ICH = analogRead(A3);

  //Convert the analog reading (which goes from 0 - 2^BITS) to a voltage (0 - 3.3V):
  float voltage_room = sensorValue_room * scale;
  float voltage_cryo = sensorValue_cryo * scale;
  float voltage_ICR = sensorValue_ICR * scale;
  float voltage_ICH = sensorValue_ICH * scale;

  //print out the value you need
  Serial.print(voltage_room, 3);
  Serial.print(',');
  Serial.print(voltage_cryo, 3);
  Serial.print(',');
  Serial.print(voltage_ICR, 3);
  Serial.print(',');
  Serial.println(voltage_ICH, 3);

}
