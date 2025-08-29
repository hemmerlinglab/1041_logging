//#include <Time.h>

void setup() {

  Serial.begin(9600);
  pinMode(A0,INPUT);
  pinMode(A1,INPUT);
  pinMode(A2,INPUT);
  pinMode(A3,INPUT);
  pinMode(A4,INPUT);
  pinMode(A5,INPUT);
  pinMode(A6,INPUT);
  pinMode(A7,INPUT);
  pinMode(3,INPUT);
  analogReadResolution(12);
  
}


void loop() {
  //Serial.flush();
  //read the input on analog pin 0:
  int V_temp = analogRead(A0);
  delay(5);
  V_temp = analogRead(A0);
  delay(10);
  int V_pressure_p = analogRead(A2);
  delay(5);
  V_pressure_p = analogRead(A2);
  delay(10);
  int V_pressure_m = analogRead(A5);
  delay(5);
  V_pressure_m = analogRead(A5);
  long flow1 = pulseIn(3,HIGH,2000000);
  int V_hornet_pressure = analogRead(A3);
  delay(5);
  V_hornet_pressure = analogRead(A3);
  long flow2 = pulseIn(3,HIGH,2000000);
  int V_UCR_in = analogRead(A6);
  delay(5);
  V_UCR_in = analogRead(A6);
  long flow3 = pulseIn(3,HIGH,2000000);
  int V_UCR_out = analogRead(A7);
  delay(5);
  V_UCR_out = analogRead(A7);
  delay(10);
  int UHV_pressure = analogRead(A4);
  delay(5);
  UHV_pressure = analogRead(A4);
  

  float prd = 2*(max(flow1,max(flow2,flow3)));
  if(prd<0.01){
    prd = 66000.0;
  };

  //Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5V):

  // Conversion could be wrong: 0.13 V corresponds to 1.3 lpm and 1.95 V correspond to 25.3 grad
  float res = 4095.0;
  float Vmax = 3.3;
  float flow = prd; // * 14.0/5.0 + 1.0;  
  float temp = V_temp * (Vmax / res); // * 120.0/5.0 * 0.5;  
  float pressure =  (V_pressure_p - V_pressure_m) * (Vmax / res) * 3.0;
  float hornet_pressure =  V_hornet_pressure * (Vmax / res) * 3.0;
  float V_in = V_UCR_in*(Vmax/res);
  float V_out = V_UCR_out*(Vmax/res);
  float uhv = UHV_pressure*(Vmax/res)*3.0;
  
  //print out the value you need:
  //Serial.print(hour());

  String mess = "temp,"+String(temp)+",flow,"+String(flow)+",pressure,"+String(pressure)+",hornet_pressure,"+String(hornet_pressure)+",UCR_in,"+String(V_in)+",UCR_out,"+String(V_out)+",uhv,"+String(uhv);
  //Serial.print("temp,");
  //Serial.print(temp);
  //Serial.print(",flow,");
  //Serial.print(flow);
  //Serial.print(",pressure,");
  //Serial.print(pressure);
  //Serial.print(",hornet_pressure,");
  //Serial.println(hornet_pressure);
  Serial.println(mess);
  //Serial.flush();
  delay(500);
  }
