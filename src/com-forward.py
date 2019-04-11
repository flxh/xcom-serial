from serial import Serial
import serial
from xcom_serial.parse import parse_header, is_data_constistent, parse_service_frame, parse_object, convert_bytes_to_float, convert_float_to_bytes, calculate_checksum
from xcom_serial.format import format_message, format_object, format_service_frame
from threading import Thread

BAUDRATE = 38400
PARITY = serial.PARITY_EVEN
PORT_XCOM = "COM20" #TODO
PORT_MANAGEMENT = "COM19"#TODO

overwrite_factor = 1.


def overwrite_func(service_flag_byte, service_id, object_type, object_id, property_id, property_data):
    if service_flag_byte == 0x02 and object_id == 3005:
        global overwrite_factor
        val = convert_bytes_to_float(property_data)
        val *= overwrite_factor
        property_data = convert_float_to_bytes(val)

        ob_id_bytes = (object_id).to_bytes(2, "big")
        data_bytes = service_flag_byte + service_id + object_type + ob_id_bytes + property_id + property_data
        checksum_bytes = calculate_checksum(data_bytes)
        return data_bytes, checksum_bytes

    else:
        raise ValueError


def forward(p_from, p_to, overwrite):
    print("{} -> {}".format(p_from.port, p_to.port))

    while True:
        header_bytes = p_from.read(14)
        print(header_bytes)
        if header_bytes[0] is not 0xAA:
            raise Exception("Next message does not start with 0xAA. Data inconsistent.")

        datalen, dest_address, src_address = parse_header(header_bytes)

        data_bytes = p_from.read(datalen)
        checksum_bytes = p_from.read(2)

        service_flag_byte, service_id, service_data = parse_service_frame(data_bytes)
        object_type, object_id, property_id, property_data = parse_object(service_data)

        try:
            data_bytes, checksum_bytes = overwrite(service_flag_byte, service_id, object_type, object_id, property_id, property_data)
        except ValueError as e:
            pass

        is_consistent = is_data_constistent(data_bytes, checksum_bytes)

        if not is_consistent:
            raise Exception("Checksum incorrect.")

        p_to.write(header_bytes + data_bytes + checksum_bytes)
        p_to.flush()

        if (object_id == 3005 and service_flag_byte == 0x02) or (object_id == 1638 and service_flag_byte == 0): #Antwort wenn Strom gelesen wird oder request wenn strom geschireben wird
            object_string = format_object(object_type, object_id, property_id, convert_bytes_to_float(property_data))
            service_string = format_service_frame(service_flag_byte, service_id, object_string)
            message_string = format_message(service_string, datalen, src_address, dest_address, is_consistent)
            print("{} -> {} Original message:".format(p_from.port, p_to.port))
            print(message_string)


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

