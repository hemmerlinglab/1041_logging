volatile int i = 0;

void setup() {
  // put your setup code here, to run once:
   analogWriteResolution(12);
}

void loop() {
  // put your main code here, to run repeatedly:
  //analogWrite(DAC0, i);
  //if(i == 4095)
  //  i = 0;
  //i++;

  analogWrite(DAC0, 0);
  delay(20);
  analogWrite(DAC0, 2000);
  delay(20);
  analogWrite(DAC0, 4095);
  delay(20);
  analogWrite(DAC0, 5095);
  delay(200);
  
}
