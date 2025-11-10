#include <ArduinoBLE.h>

const int trigPin = 2;
const int echoPin = 3;

BLEService distanceService("180C");                // BLE service
BLEFloatCharacteristic distanceChar("2A6E", BLERead | BLENotify); // BLE characteristic for distance

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  if (!BLE.begin()) {
    Serial.println("BLE start failed!");
    while (1);
  }

  BLE.setLocalName("WallSensor");
  BLE.setAdvertisedService(distanceService);
  distanceService.addCharacteristic(distanceChar);
  BLE.addService(distanceService);

  distanceChar.writeValue(0.0);
  BLE.advertise();

  Serial.println("WallSensor is now advertising...");
}

float getDistanceCM() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // timeout ~5m
  if (duration == 0) return -1;                  // out of range
  return duration / 58.0;                        // convert to cm
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    while (central.connected()) {
      float distance = getDistanceCM();
      if (distance <= 0) distance = 0.0;  // always send numeric value
      distanceChar.writeValue(distance);

      Serial.print("Distance: ");
      Serial.print(distance);
      Serial.println(" cm");

      delay(1000);  // 1 second interval
    }

    Serial.println("Disconnected. Advertising again...");
    BLE.advertise();
  }
}
