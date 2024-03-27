#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

#define i2c_Address 0x3c
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SH1106G display = Adafruit_SH1106G(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Shift register - 74HC595
const int clockPin = 4;
const int latchPin = 3;
const int dataPin = 2;

// Rotatory encoder
const int inputCLK = 7;
const int inputDT = 8;
const int inputSW = 9;

int counter = 0; 
int currentStateCLK;
int previousStateCLK;
int currentStateSW;
String encdir ="";

void setup ()
{
  Serial.begin(9600);
  delay(250);

  // Shift register
  pinMode(latchPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(dataPin, OUTPUT);

  // Rotatory encoder
  pinMode (inputCLK, INPUT);
  pinMode (inputDT, INPUT);
  pinMode (inputSW, INPUT);
  
  previousStateCLK = digitalRead(inputCLK);

  display.begin(i2c_Address, true);
  display.display();
}

void loop() {
  checkEncoderState();
  displayRotatoryData();
}

void displayRotatoryData() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.println("Drawing Machine");
  display.print("Rotary direction: ");
  display.println(encdir);
  display.print("Rotary switch: ");
  display.println(currentStateSW);
  display.print("Rotary counter: ");
  display.println(counter);
  display.display();
}

void checkEncoderState() {
  currentStateCLK = digitalRead(inputCLK);
  currentStateSW = digitalRead(inputSW);

  if (currentStateCLK != previousStateCLK){ 
    if (digitalRead(inputDT) != currentStateCLK) { 
      counter ++;
      encdir ="CW";
    }
    else {
      counter --;
      encdir ="CCW";
    }
  }
}

void writeShiftRegister(byte data) {
  digitalWrite(latchPin, LOW);
  shiftOut(dataPin, clockPin, MSBFIRST, data);
  digitalWrite(latchPin, HIGH);
}
