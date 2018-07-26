#!/usr/bin/env python3

import serial
import sys, binascii, base64, struct

def main(argv):
    if len(argv) < 2:
        print("Usage: sniff_receiver.py [serial_port_name] [-c ADV_CHANNEL]", file=sys.stderr)
        return

    ser = serial.Serial(argv[1], 460800)

    # command sync
    ser.write(b'@@@@@@@@\r\n')

    # very crude argument handling for now since I only have one option
    if len(argv) >= 4 and argv[2] == "-c":
        advChan = int(argv[3])
        if not (37 <= advChan <= 39):
            print("advChan out of bounds")
        advCmd = bytes([0x01, 0x10, advChan])
        advMsg = base64.b64encode(advCmd) + b'\r\n'
        ser.write(advMsg)

    while True:
        pkt = ser.readline()
        try:
            data = base64.b64decode(pkt.rstrip())
        except binascii.Error as e:
            print("Ignoring message:", e, file=sys.stderr)
            continue
        print_message(data)

def print_message(data):
    if data[0] == 0x10:
        print_packet(data[1:])
    elif data[0] == 0x11: # debug print
        print("DEBUG:", str(data[1:], encoding='utf-8'))
        return
    else:
        print("Unknown message type!", file=sys.stderr)

    print()

def print_packet(data):
    ts, l, rssi, chan = struct.unpack("<LBbB", data[:7])
    body = data[7:]

    if len(body) != l:
        print("Incorrect length field!", file=sys.stderr)
        return

    print("Timestamp: %.6f\tLength: %i\tRSSI: %i\tChannel: %i" % (
        ts / 1000000., l, rssi, chan))
    if chan >= 37:
        decode_advert(body)
    else:
        decode_data(body)

def _safe_asciify(c):
    if 32 <= c <= 126:
        return chr(c)
    return " "

def print_hexdump(data):
    ascstr = "  ".join([_safe_asciify(b) for b in data])
    hexstr = " ".join(["%02X" % b for b in data])
    print(hexstr)
    print(ascstr)

def decode_advert(body):
    pdu_type = body[0] & 0xF
    ChSel = (body[0] >> 5) & 1
    TxAdd = (body[0] >> 6) & 1
    RxAdd = (body[0] >> 7) & 1
    length = body[1]

    adv_pdu_types = ["ADV_IND", "ADV_DIRECT_IND", "ADV_NONCONN_IND", "SCAN_REQ",
            "SCAN_RSP", "CONNECT_IND", "ADV_SCAN_IND", "ADV_EXT_IND"]
    if pdu_type < len(adv_pdu_types):
        print("Ad Type: %s" % adv_pdu_types[pdu_type])
    else:
        print("Ad Type: RFU")
    print("ChSel: %i" % ChSel, "TxAdd: %i" % TxAdd, "RxAdd: %i" % RxAdd,
            "Ad Length: %i" % length)

    print_hexdump(body)

def decode_data(body):
    LLID = body[0] & 0x3
    NESN = (body[0] >> 2) & 1
    SN = (body[0] >> 3) & 1
    MD = (body[0] >> 4) & 1
    length = body[1]

    data_pdu_types = ["RFU", "LL DATA", "LL DATA CONT", "LL CONTROL"]
    print("LLID: %s" % data_pdu_types[LLID])
    print("NESN: %i" % NESN, "SN: %i" % SN, "MD: %i" % MD,
            "Data Length: %i" % length)

    print_hexdump(body)

if __name__ == "__main__":
    main(sys.argv)
