#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Servo.h>

#include <SD.h>

AccelStepper stepper1(AccelStepper::DRIVER, 6, 7);
AccelStepper stepper2(AccelStepper::DRIVER, 8, 9);

Servo servoMotor;

const int ms0 = 2;
const int ms1 = 3;
const int ms2 = 4;

const int servoPin = 10;

MultiStepper steppers;

File file;
const int chipSelect = 5;

int index = 0;
int maxSpeed = 3000;  // Default maxSpeed
int servoPos = 0;

void setup() {
  Serial.begin(9600); 

  while (!SD.begin(chipSelect)) {
    Serial.println("SD card initialization failed!");
    delay(500);
  }

  file = SD.open("PATH.TXT");
  if (!file) {
    Serial.println("File open failed!");
    return;
  }

  bool maxSpeedSet = false;

  pinMode(ms0, OUTPUT);
  pinMode(ms1, OUTPUT);
  pinMode(ms2, OUTPUT);
  
  digitalWrite(ms0, LOW);
  digitalWrite(ms1, HIGH);
  digitalWrite(ms2, HIGH);

  stepper1.setMaxSpeed(maxSpeed);  stepper2.setMaxSpeed(maxSpeed);

  steppers.addStepper(stepper1);
  steppers.addStepper(stepper2);

  servoMotor.attach(servoPin);
  
  delay(500);

  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();

    if (line.startsWith("maxSpeed:")) {
      int colonIndex = line.indexOf(':');
      if (colonIndex != -1) {
        String maxSpeedStr = line.substring(colonIndex + 1);
        maxSpeed = maxSpeedStr.toInt();
        stepper1.setMaxSpeed(maxSpeed);
        stepper2.setMaxSpeed(maxSpeed);
        Serial.print("Set maxSpeed: ");
        Serial.println(maxSpeed);
        continue;
      }
    }
    else if (line.startsWith("PENUP:")) {
      int colonIndex = line.indexOf(':');
      if (colonIndex != -1) {
        String servoPosStr = line.substring(colonIndex + 1);
        servoPos = servoPosStr.toInt();
        servoMotor.write(servoPos);
        Serial.print("Servo write: ");
        Serial.println(servoPos);
        delay(1000);
        continue;
      }
    }
    else if (line.startsWith("PENDOWN:")) {
      int colonIndex = line.indexOf(':');
      if (colonIndex != -1) {
        String servoPosStr = line.substring(colonIndex + 1);
        servoPos = servoPosStr.toInt();
        servoMotor.write(servoPos);
        Serial.print("Servo write: ");
        Serial.println(servoPos);
        delay(1000);
        continue;
      }
    }

    int commaIndex = line.indexOf(',');

    if (commaIndex != -1) {
      String num1Str = line.substring(0, commaIndex);
      String num2Str = line.substring(commaIndex + 1);

      int num1 = num1Str.toInt();
      int num2 = num2Str.toInt();

      long positions[2];

      positions[0] = num1;
      positions[1] = num2;
        
      steppers.moveTo(positions);
      steppers.runSpeedToPosition();

      Serial.print("Executed ");
      Serial.print(num1);
      Serial.print(",");
      Serial.println(num2);
    }
  }

}

void loop() {
  
}
