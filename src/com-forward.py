from serial import Serial
import serial
from xcom_serial.parse import parse_header, is_data_constistent
from xcom_serial.format import format_message
from threading import Thread

BAUDRATE = 192000
PARITY = serial.PARITY_EVEN
PORT_XCOM = "" #TODO
PORT_MANAGEMENT = ""#TODO


def filter(header_bytes, data_bytes, checksum_bytes):
    return header_bytes, data_bytes, checksum_bytes


def forward(port_from, port_to, filter):
    with Serial(port=port_from, baudrate=BAUDRATE, parity=PARITY, timeout=60) as p_from, \
            Serial(port=port_to, baudrate=BAUDRATE, parity=PARITY, timeout=60) as p_to:

        while True:
            header_bytes = p_from.read(14)
            if header_bytes[0] is not 0xAA:
                raise Exception("Next message does not start with 0xAA. Data inconsistent.")

            datalen, dest_address, src_address = parse_header(header_bytes)

            data_bytes = p_from.read(datalen)
            checksum_bytes = p_from.read(2)

            #header_bytes, data_bytes, checksum_bytes = filter(header_bytes, data_bytes, checksum_bytes)

            is_consistent = is_data_constistent(data_bytes, checksum_bytes)

            if not is_consistent:
                raise Exception("Checksum incorrect.")

            p_to.write(header_bytes + data_bytes + checksum_bytes)
            p_to.flush()

            message_string = format_message("", datalen, src_address, dest_address, is_consistent)
            print("{} -> {}".format(port_from, port_to))
            print(message_string)


if __name__ == "__main__":
    thread1 = Thread(target=forward, args=(PORT_XCOM, PORT_MANAGEMENT, filter))
    thread2 = Thread(target=forward, args=(PORT_MANAGEMENT, PORT_XCOM, filter))
    thread1.start()
    thread2.start()
