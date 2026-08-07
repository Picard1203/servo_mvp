Arduino libraries vendored for the air-gapped board, referenced by
sketch/sketch.yaml so nothing is fetched at build time.

Put two folders here:

1. Ethernet/     The PATCHED Ethernet 2.0.2.
                 Copy it off the dev board after applying the IPAddress fix:
                     cp -r ~/.arduino15/internal/Ethernet_2.0.2_*/Ethernet ./
                 The patch: the Zephyr core ships its own arduino::IPAddress,
                 which makes IPAddress(0ul) ambiguous against three
                 constructors. Fix is an explicit cast at each call site:
                     IPAddress(0ul)          -> IPAddress((uint32_t)0)
                     IPAddress(0xFFFFFFFFul) -> IPAddress((uint32_t)0xFFFFFFFF)
                 Found in EthernetClient.cpp (both branches of the
                 ESP8266/ESP32 #if). Re-derivable in minutes from the
                 compiler error if this copy is ever lost.

2. SCServo/      Waveshare's SCSTServoLibrary, unzipped.
                 Provides the SMS_STS class. Use SMS_STS, never SCSCL -
                 that is the SC series and its register map differs
                 (mode is at address 19 there, 33 here).

The folder NAME here must match the entry in sketch/sketch.yaml.
