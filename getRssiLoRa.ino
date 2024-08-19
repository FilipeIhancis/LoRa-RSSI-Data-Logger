/*****************************************************************************
 *  LoRa Range Measurement Tool with Statistics and Data Logging
 *  
 *  implements a "ping-pong" type of communication, in which both LoRa 
 *  transceivers act simultaneously as transmitters and receivers of 
 *  a fixed message (payload)
 *  
 *  Filipe Ihancis Teixeira (filipeihancist@gmail.com)
 *  
/*****************************************************************************/


/*****************************************************************************/
// Libraries
#include <SPI.h>
#include <LoRa.h>
#include <stdlib.h> 

// Pins for LoRa antenna
#define MISO_LORA 19
#define MOSI_LORA 23
#define SCK_LORA 18
#define SS_PIN_LORA 15
#define DIO0_PIN_LORA 5
#define RESET_PIN_LORA 2

// Control variables
const int SENDING_TIME = 5020;
const int RX_TIMEOUT = 11000;
unsigned long pTimeTx, pTimeNoRx;
int rssiPacket;


/*****************************************************************************/
void LoRa_radio_config()
{
    LoRa.setGain(0);
    LoRa.setPreambleLength(8);
    LoRa.setCodingRate4(5);
    LoRa.setSpreadingFactor(7);
    LoRa.setSyncWord(0xF3);
}

/*****************************************************************************/
void setup() 
{
    // Initialize serial
    Serial.begin(9600); while(!Serial); Serial.println("");

    // Initialize SPI communication
    SPI.begin(SCK_LORA, MISO_LORA, MOSI_LORA, SS_PIN_LORA);

    // Sets LoRa pins
    LoRa.setPins(SS_PIN_LORA, RESET_PIN_LORA, DIO0_PIN_LORA);

    int internalCounter = 0;

    // Initialize LoRa module (915MHz)
    while(!LoRa.begin(915E6)) {
      Serial.print(".");
      delay(500);
      internalCounter++;
      
      if(internalCounter >= 10)
        ESP.restart();
    }
    LoRa_radio_config();
    Serial.println("LoRa Initializing OK");
    LoRa.receive();
}

/*****************************************************************************/
void loop() 
{   
    // Restarts if the program does not receive a message within 11 seconds
    if (millis() - pTimeNoRx >=  RX_TIMEOUT) ESP.restart();
  
    // Check for packages
    int packet = LoRa.parsePacket();
  
    // Execute if module receives packets
    if(packet != 0)
    {
      pTimeNoRx = millis();
      
      // Reads a package
      String message = "";
      while (LoRa.available()) {
        message += (char)LoRa.read();
      }
      // Gets the rssi value
      rssiPacket = LoRa.packetRssi();
  
      // Displays the received message on the Serial Monitor
      Serial.println("\nMensagem recebida: " + message);
      delay(5);
    }
  
    // Transmits packets every 5020 milliseconds
    if(millis() - pTimeTx >= SENDING_TIME)
    {
      // Format message
      String rssi_str = String(rssiPacket);
      String packetSend = "Hello im random sender. RSSI: " + rssi_str;
      
      // Puts radio in idle to transmit properly
      LoRa.idle();

      // Displays the transmited message on the Serial Monitor
      pTimeTx = millis();
      Serial.print("\nMensagem enviada: " + packetSend);

      // Transmits the packet
      LoRa.beginPacket();
      LoRa.print(packetSend);
      LoRa.endPacket();
    
      // Enables module to receive packets
      LoRa.receive();
  
      // Random delay between 3 and 13 milliseconds
      delay(3+rand()%(13));
    }
    delay(1);
}
