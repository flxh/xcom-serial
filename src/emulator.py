from serial import Serial
import serial
import datetime

from SerialMessage import SerialMessage, parse_data_len
from threading import Thread

BAUDRATE = 38400
PARITY = serial.PARITY_EVEN
PORT_XCOM = "COM3" #TODO
PORT_MANAGEMENT = "COM2"#TODO

overwrite_factor = 1.


class ResponseNotConfiguredError(ValueError):
    pass


class Emulator:
    def __init__(self, xcom_port, management_port):
        self.xcom_port = xcom_port
        self.management_port = management_port

    static_responses = {
        (5101, 5): b'\xaa6\xf5\x01\x00\x00\x01\x00\x00\x00\x0e\x00:\x04\x02\x01\x02\x00\xed\x13\x00\x00\x05\x00\x02\x00\x00\x00\x0bF', # Logger aktiv
        (1610, 5): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0b\x00\xa5K\x02\x01\x02\x00J\x06\x00\x00\x05\x00\x00Y`', # definierte Phasenverschiebung
        (1623, 5): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x02\x00W\x06\x00\x00\x05\x00\x00\x00\x00\x00f\xed', # cos phi AP
        (1613, 5): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x02\x00M\x06\x00\x00\x05\x00\x00\x00HB\xe6[', # Position AP
        (1622, 5): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x02\x00V\x06\x00\x00\x05\x00\x00\x00\x00\x00e\xe3', # cos phi 0%
        (1624, 5): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x02\x00X\x06\x00\x00\x05\x00\x00\xc0\xcc=0\x0c', # cos phi bie 100%

        (3124, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x004\x0c\x00\x00\x01\x00\x00\x00\x80?\x03\xe0', # ID Type
        (3125, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x005\x0c\x00\x00\x01\x00\x00@\x9cEf\xe8', # ID Power
        (3126, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x006\x0c\x00\x00\x01\x00\x00\x00fC\xef\xc4',
        (3127, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x007\x0c\x00\x00\x01\x00\x00\x00@B\xc9\x81',
        (3128, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x008\x0c\x00\x00\x01\x00\x00\x00\xb0A9j',
        (3129, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x009\x0c\x00\x00\x01\x00\x00P E\xfeH',
        (3130, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x00:\x0c\x00\x00\x01\x00\x00\x00\x80C\r ',
        (3131, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x00;\x0c\x00\x00\x01\x00\x00\xc0\xc3D\x12\xf1',
        (3132, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x00<\x0c\x00\x00\x01\x00\x00\x00\x00D\x905',
        (3156, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x00T\x0c\x00\x00\x01\x00\x00\xe0\x8aF\x14\xdb',
        (3157, 1): b'\xaa6d\x00\x00\x00\x01\x00\x00\x00\x0e\x00\xa8Q\x02\x01\x01\x00U\x0c\x00\x00\x01\x00\x00@\x10D\xf9\x0f'
    }

    read_messages_response = b'\xaa6\xf5\x01\x00\x00\x01\x00\x00\x00\x1c\x00H \x02\x01\x03\x00\x00\x00\x00\x00\x00\x00\xd0\x03\x00\x00\x03\x00e\x00\x00\x00\xd3\xa8\x89\\\x00\x00\x00\x00\xa0p'

    def emulate_response(self, request_msg):
        """
        
        if request_msg.service_id == 0x02: # write request
            return SerialMessage(
                SerialMessage.FRAME_FLAGS_RESPONSE,
                request_msg.dest_address,
                request_msg.src_address,
                SerialMessage.SERVICE_FLAGS_IS_RESPONSE,
                request_msg.service_id,
                request_msg.object_type,
                request_msg.object_id,
                request_msg.property_id,
                None
            )"""

        if request_msg.service_id == 0x01 and request_msg.object_type in (1, 2): # normal read requests

            if (request_msg.object_id, request_msg.property_id) in Emulator.static_responses:
                return SerialMessage.from_bytes(
                    Emulator.static_responses[(request_msg.object_id, request_msg.property_id)])
                '''
            elif object_id == 3000 and property_id == 0x0001:
                current_voltage = 1.# TODO
                property_data = convert_float_to_bytes(current_voltage)
    
            elif object_id == 3005 and property_id == 0x0001:
                current_current = 1.# TODO
                property_data = convert_float_to_bytes(current_current)
    
            elif object_id == 3137 and property_id == 0x0001: # Eingang Wirkleistung
                effective_input_power = 1.# TODO
                property_data = convert_float_to_bytes(effective_input_power)
    
            elif object_id == 3136 and property_id == 0x0001: # Ausgang Wirkleistung
                effective_output_power = 1.# TODO
                property_data = convert_float_to_bytes(effective_output_power)
    
            elif object_id == 3049 and property_id == 0x0001: # Inverter Aktiv
                inverter_active = 1# TODO
                property_data = inverter_active.to_bytes(2, "little")
    
            elif object_id == 3028 and property_id == 0x0001: # Laden / Entlade
                operating_mode = 2# TODO
                property_data = operating_mode.to_bytes(2, "little")
            '''

            else:
                raise ResponseNotConfiguredError()

            return SerialMessage(
                SerialMessage.FRAME_FLAGS_RESPONSE,
                request_msg.dest_address,
                request_msg.src_address,
                SerialMessage.SERVICE_FLAGS_IS_RESPONSE,
                request_msg.service_id,
                request_msg.object_type,
                request_msg.object_id,
                request_msg.property_id,
                property_data_bytes
            )

        elif request_msg.service_id == 0x01 and request_msg.object_type == 3:
            return SerialMessage.from_bytes(Emulator.read_messages_response)

        else:
            raise ResponseNotConfiguredError()


    def forward_message_to_xcom(self, request_msg):
        self.xcom_port.write(request_msg.to_bytes())
        self.xcom_port.flush()

        header_bytes = self.xcom_port.read(14)
        if header_bytes[0] is not 0xAA:
            raise Exception("Response message does not start with 0xAA. Data inconsistent.")

        datalen = parse_data_len(header_bytes)

        data_bytes = self.xcom_port.read(datalen)
        checksum_bytes = self.xcom_port.read(2)

        message_bytes = header_bytes + data_bytes + checksum_bytes
        response = SerialMessage.from_bytes(message_bytes)
        return response
        

    def receive_request_loops(self):
        while True:
            header_bytes = self.management_port.read(14)
            if header_bytes[0] is not 0xAA:
                raise Exception("Next message does not start with 0xAA. Data inconsistent.")

            datalen = parse_data_len(header_bytes)

            data_bytes = self.management_port.read(datalen)
            checksum_bytes = self.management_port.read(2)

            request_msg = SerialMessage.from_bytes(header_bytes+data_bytes+checksum_bytes)

            print("Request: ")
            print(request_msg.to_str(0))

            if request_msg.service_flags is not 0:
                raise Exception("Message is not a request")

            try:
                response = self.emulate_response(request_msg)
                print("EMULATED Response:")
            except ResponseNotConfiguredError:
                print("FORWARDED Response:")
                response = self.forward_message_to_xcom(request_msg)

            print(response.to_str(4))

            self.management_port.write(response.to_bytes())
            self.management_port.flush()
            
            with open("log3.csv","a") as file:
                ts = datetime.datetime.now().isoformat()
                file.write("Request;{};{}\n".format(ts,request_msg.format_csv_line()))
                file.write("Response;{};{}\n".format(ts,response.format_csv_line()))



def input_loop():
    while True:
        global overwrite_factor
        overwrite_factor = float(input())


if __name__ == "__main__":
    with Serial(port=PORT_XCOM, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_xcom, \
            Serial(port=PORT_MANAGEMENT, baudrate=BAUDRATE, parity=PARITY, timeout=None) as p_management:
        emulator = Emulator(p_xcom, p_management)

        t_emulator = Thread(target=emulator.receive_request_loops)
        t_input = Thread(target=input_loop)

        t_emulator.start()
        t_input.start()

        t_emulator.join()
        t_input.join()

