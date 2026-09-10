#!/usr/bin/env python3
"""
TouchOSC -> MIDI CC Bridge (Float 0.0-1.0 input, scaled to 0-127)
- Left side: 16 faders for Elektron Digitakt II (CH1-16, CC#95)
- Right side: 12 faders for Boss RC-600 (CH11, various CCs)

TouchOSC fader config:
  - Response: ABSOLUTE
  - Value x: float 0.0 to 1.0 (native fader range)
  - OSC Trigger: x
  - OSC Arguments: f (float)
  - OSC Scale: 0 to 1 (or just leave default)
  - OSC address: two constants "/" + fader name
  - Grid: 13 (optional, for snap positions)
"""
import sys
import rtmidi
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

midi_out = rtmidi.MidiOut()
midi_out.open_virtual_port("TouchOSC Bridge")

print("-> TouchOSC MIDI Bridge (float 0.0-1.0 -> MIDI 0-127)")
print("-> Poslušam na vratih 8001... qpwgraph povezuje MIDI.")

dispatcher = Dispatcher()


def pretvori_v_midi(address, *args):
    if not args:
        return
    try:
        raw = float(args[0])
    except (ValueError, TypeError, IndexError):
        return

    # Convert to MIDI 0-127 (TouchOSC sends 0.0-127.0 with scale set to 0-127)
    vrednost = int(round(raw))
    vrednost = max(0, min(127, vrednost))

    addr_lower = address.lower()

    # --- LEVA STRAN: Digitakt II ---
    # /dt_track 1 ... /dt_track 16 -> CH1-CH16, CC#95
    if addr_lower.startswith("/dt_track"):
        try:
            stevilka = int(address.split()[-1])
            if 1 <= stevilka <= 16:
                status_byte = 0xB0 + (stevilka - 1)
                midi_out.send_message([status_byte, 95, vrednost])
                print(f"[DT2] Track {stevilka} -> CH{stevilka} CC#95 = {vrednost}")
                return
        except (ValueError, IndexError):
            pass

    # --- DESNA STRAN: Boss RC-600 ---
    # All on CH11 (0xBA = 186)
    cc = None
    if addr_lower == "/inst1":          cc = 5
    elif addr_lower == "/inst2":        cc = 6
    elif addr_lower == "/mic_l":        cc = 8
    elif addr_lower == "/mic_r":        cc = 9
    elif addr_lower == "/phones":       cc = 4
    elif addr_lower == "/main_out":     cc = 2
    elif addr_lower.startswith("/track "):
        try:
            n = int(address.split()[-1])
            if 1 <= n <= 6:
                cc = 9 + n
        except (ValueError, IndexError):
            pass

    if cc is not None:
        midi_out.send_message([0xBA, cc, vrednost])
        print(f"[RC600] {address} -> CH11 CC#{cc} = {vrednost}")


dispatcher.set_default_handler(pretvori_v_midi)

try:
    server = BlockingOSCUDPServer(("0.0.0.0", 8001), dispatcher)
    print("Server zagnan. Ctrl+C za ustavitev.")
    server.serve_forever()
except KeyboardInterrupt:
    print("\nUstavljam...")
    sys.exit(0)
