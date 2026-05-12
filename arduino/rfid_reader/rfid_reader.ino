#include <SPI.h>
#include <MFRC522.h>

// Arduino Uno/Nano + MFRC522:
// SDA/SS -> D10
// SCK    -> D13
// MOSI   -> D11
// MISO   -> D12
// RST    -> D9
// 3.3V   -> 3.3V
// GND    -> GND
#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);

String formatUid(MFRC522::Uid uid) {
  String value = "";

  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 0x10) {
      value += "0";
    }

    value += String(uid.uidByte[i], HEX);

    if (i < uid.size - 1) {
      value += ":";
    }
  }

  value.toUpperCase();
  return value;
}

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Aguarda a serial em placas com USB nativo.
  }

  SPI.begin();
  rfid.PCD_Init();

  Serial.println("RFID pronto. Aproxime uma tag/cartao.");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  Serial.print("UID:");
  Serial.println(formatUid(rfid.uid));

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(500);
}
