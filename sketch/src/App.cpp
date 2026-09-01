#include "App.h"

#include <Arduino.h>
#include <Arduino_RouterBridge.h>
#include <SCServo.h>

#include "BridgeApi.h"
#include "Config.h"
#include "DiagLog.h"
#include "NetworkRelay.h"
#include "ServoBus.h"
#include "ServoController.h"

namespace app {
namespace {

SMS_STS g_driver;
servo::ServoBus g_bus(g_driver, config::kServoId, config::kBusReadRetries);
servo::ServoController g_controller(g_bus);
net::NetworkRelay g_relay(config::kEthernetCsPin, config::kApiPort,
                          config::kRelayChunkBytes);
api::BridgeApi g_api(g_controller, &g_relay);

const uint8_t kMac[6] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x01};
const uint8_t kIp[4] = {192, 168, 10, 60};
const uint8_t kGateway[4] = {192, 168, 10, 1};
const uint8_t kSubnet[4] = {255, 255, 255, 0};

bool g_servo_ready = false;

}  // namespace

void App::Begin() {
  diag::DiagLog::Init();

  Serial.begin(config::kConsoleBaud);
  const uint32_t started = millis();
  while (!Serial && millis() - started < 2000) {
  }

  Bridge.begin();

  Serial1.begin(config::kServoBaud);
  g_driver.pSerial = &Serial1;
  delay(600);

  g_servo_ready = g_controller.Begin(
      config::kMultiTurnEnabled, config::kAngleResolution,
      config::kDeadbandCounts, config::kTorqueLimit,
      config::kMinStartForce);

  Serial.println();
  Serial.println(F("Servo Control - MCU side"));
  Serial.print(F("  servo id "));
  Serial.print(static_cast<int>(config::kServoId));
  Serial.print(F(" @ "));
  Serial.print(static_cast<unsigned long>(config::kServoBaud));
  Serial.println(F(" baud"));
  Serial.print(F("  servo: "));
  Serial.println(g_servo_ready ? F("ready") : F("NOT RESPONDING"));

  const bool net_ready = g_relay.Begin(kMac, kIp, kGateway, kSubnet);
  Serial.print(F("  ethernet: "));
  Serial.println(net_ready ? F("W5500 ready") : F("no shield detected"));

  g_api.Register();
  Serial.println(F("  bridge: callbacks registered"));
  Serial.println(F("ready"));
}

void App::Tick() {
  g_relay.Poll();
  g_api.DrainDiagLog();

  // Yield to Bridge RPC thread per RELAY_NOTES.md rule 3.
  delay(1);
}

}  // namespace app
