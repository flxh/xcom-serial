from serial import Serial
import serial

from SerialMessage import SerialMessage, parse_data_len, convert_float_to_bytes, convert_bytes_to_float
from threading import Thread

BAUDRATE = 38400
PARITY = serial.PARITY_EVEN
PORT_XCOM = "COM3" #TODO
PORT_MANAGEMENT = "COM2"#TODO

overwrite_factor = 1.


def overwrite_func(msg):
    if msg.service_flags == SerialMessage.SERVICE_FLAGS_IS_RESPONSE and msg.object_id == 3005:
        global overwrite_factor
        val = convert_bytes_to_float(msg.property_data_bytes)
        val *= overwrite_factor

        print("Overwritten. Factor = {} Value = {}".format(overwrite_factor, val))
        msg.property_data_bytes = convert_float_to_bytes(val)

        return msg

    else:
        raise ValueError


def forward(p_from, p_to, overwrite):
    print("{} -> {}".format(p_from.port, p_to.port))

    while True:
        header_bytes = p_from.read(14)

        datalen = parse_data_len(header_bytes)

        data_bytes = p_from.read(datalen)
        checksum_bytes = p_from.read(2)

        msg = SerialMessage.from_bytes(header_bytes+data_bytes+checksum_bytes)

        try:
            msg = overwrite(msg)

            print("Data org: {}".format(data_bytes))
            print("Data owr: {}".format(msg.to_bytes()[14:-2]))
        except ValueError as e:
            pass

        p_to.write(msg.to_bytes())
        p_to.flush()

        if (msg.object_id == 3005 and msg.service_flag_byte == 0x02) or (msg.object_id == 1138 and msg.service_flag_byte == 0): #Antwort wenn Strom gelesen wird oder request wenn strom geschireben wird
            print(msg.to_str(0))


def input_loop():
    while True:
        global overwrite_factor
        overwrite_factor = float(input())
        
        
if __name__ == "__main__":
    with Serial(port=PORT_XCOM, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_xcom, \
            Serial(port=PORT_MANAGEMENT, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_management:
        thread1 = Thread(target=forward, args=(p_xcom, p_management, overwrite_func))
        thread2 = Thread(target=forward, args=(p_management, p_xcom, overwrite_func))
        thread3 = Thread(target=input_loop)
        thread1.start()
        thread2.start()
        thread3.start()
        thread1.join()
        thread2.join()
        thread3.join()

