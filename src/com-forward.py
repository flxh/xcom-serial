from serial import Serial
import serial
from xcom_serial.parse import parse_header, is_data_constistent
from xcom_serial.format import format_message
from threading import Thread

BAUDRATE = 38400
PARITY = serial.PARITY_EVEN
PORT_XCOM = "COM20" #TODO
PORT_MANAGEMENT = "COM19"#TODO


def filter(header_bytes, data_bytes, checksum_bytes):
    return header_bytes, data_bytes, checksum_bytes


def forward(p_from, p_to, filter):
    print("{} -> {}".format(p_from.port, p_to.port))

    while True:
        header_bytes = p_from.read(14)
        print(header_bytes)
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
        print("{} -> {}".format(p_from.port, p_to.port))
        print(message_string)


if __name__ == "__main__":
    with Serial(port=PORT_XCOM, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_xcom, \
            Serial(port=PORT_MANAGEMENT, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_management:
        thread1 = Thread(target=forward, args=(p_xcom, p_management, filter))
        thread2 = Thread(target=forward, args=(p_management, p_xcom, filter))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

