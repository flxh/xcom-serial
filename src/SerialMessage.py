import struct


def parse_data_len(header_bytes):
    return convert_bytes_to_int(header_bytes[10:12])

def calculate_checksum(data_bytes):
    a = 0xFF
    b = 0
    for byte in data_bytes:
        a = (a + byte) % 0x100
        b = (a + b) % 0x100

    return bytes([a,b])


def convert_int_to_bytes(i, n_bytes):
    return i.to_bytes(n_bytes, "little")


def convert_bytes_to_int(bytes):
    x = 0
    for i in range(len(bytes)):
        x += bytes[i] << 8*i
    return x


def convert_bytes_to_float(b):
    return struct.unpack("<f", bytes.fromhex(b))[0]


def convert_float_to_bytes(f):
    return struct.pack("<f", f)


def _parse_service_frame(data):
    service_flags_byte = data[0]
    service_id = data[1]
    service_data = data[2:]

    return service_flags_byte, service_id, service_data


def _parse_object(service_data):
    object_type = convert_bytes_to_int(service_data[:2])
    object_id = convert_bytes_to_int(service_data[2:6])
    property_id =convert_bytes_to_int( service_data[6:8])
    property_data_bytes = service_data[8:]

    return object_type, object_id, property_id, property_data_bytes


def _parse_header(header_bytes):
    frame_flag_byte = header_bytes[1]
    src_address = convert_bytes_to_int(header_bytes[2:6])
    dest_address = convert_bytes_to_int(header_bytes[6:10])
    datalen = parse_data_len(header_bytes)
    return frame_flag_byte, src_address, dest_address, datalen


class SerialMessage:
    FRAME_FLAGS_RESPONSE = 0b00110110

    SID_READ = 0x01
    SID_WRITE = 0x02

    SERVICE_FLAGS_IS_RESPONSE = 0b00000010
    SERVICE_FLAGS_ERROR = 0b00000001

    def __init__(self, frame_flags, src_address, dest_address, service_flags, service_id, object_type, object_id, property_id, property_data_bytes):
        self.frame_flags = frame_flags
        self.src_address = src_address
        self.dest_address = dest_address
        self.service_flags = service_flags
        self.service_id = service_id
        self.object_type = object_type
        self.object_id = object_id
        self.property_id = property_id
        self.property_data_bytes = property_data_bytes

    @staticmethod
    def from_bytes(message_bytes):
        header_bytes = message_bytes[:14]
        if header_bytes[0] is not 0xAA:
            raise ValueError("Message bytes do not start with byte 0xAA. Data inconsistent.")

        frame_flag_byte, src_address, dest_address, datalen = _parse_header(header_bytes)

        data_bytes = message_bytes[14:14+datalen]
        checksum_bytes = message_bytes[14+datalen:14+datalen+2]

        if checksum_bytes != calculate_checksum(data_bytes):
            raise ValueError("Checksum is incorrect. Data inconsistent.")

        service_flag_byte, service_id, service_data_bytes = _parse_service_frame(data_bytes)
        object_type, object_id, property_id, property_data_bytes = _parse_object(service_data_bytes)

        return SerialMessage(frame_flag_byte, src_address, dest_address, service_flag_byte, service_id, object_type, object_id, property_id, property_data_bytes)

    def to_bytes(self):
        data_bytes = self.service_flags.to_bytes(1, "little")
        data_bytes += self.service_id.to_bytes(1, "little")
        data_bytes += self.object_type.to_bytes(2, "little")
        data_bytes += self.object_id.to_bytes(4, "little")
        data_bytes += self.property_id.to_bytes(2, "little")
        if self.property_data_bytes is not None:
            data_bytes += self.property_data_bytes

        start_byte = b'\xaa'
        header = self.frame_flags.to_bytes(1, "little")
        header += self.src_address.to_bytes(4, "little")
        header += self.dest_address.to_bytes(4, "little")
        header += len(data_bytes).to_bytes(2, "little")

        return start_byte + header + calculate_checksum(header) + data_bytes + calculate_checksum(data_bytes)

    OBJECT_TYPE = {
        0x0001: "USER_INFO",
        0x0002: "PARAMETER",
        0x0003: "MESSAGE",
        0x0101: "FILE_TRANSFER"
    }

    SERVICE = {
        0x01: "READ",
        0x02: "WRITE",
    }

    SERVICE_FLAGS = {
        0 : "REQUEST",
        0x02: "RESPONSE",
        0x03: "ERROR"
    }

    def total_len(self):
        return 14 + 10 + (len(self.property_data_bytes) if self.property_data_bytes else 0 ) + 2 # header + common fields + property data + checksum

    def _format_object(self):
        object_string = "\n\t\t" + "\n\t\t".join([
            "Object type: 0x{:04x} - {}".format(self.object_type, SerialMessage.OBJECT_TYPE[self.object_type]),
            "Object id: 0x{:04x} - {}".format(self.object_id, self.object_id),
            "Property id: 0x{:04x}".format(self.property_id),
            "Property Data: {}".format(self.property_data_bytes)
        ])
        return object_string

    def _format_service_frame(self):
        object_string = self._format_object()

        sf_string = "\n\t" + "\n\t".join([
            "Service flags: 0b{:08b} - {}".format(self.service_flags, SerialMessage.SERVICE_FLAGS[self.service_flags]),
            "Service id: 0x{:02X} - {}".format(self.service_id, SerialMessage.SERVICE[self.service_id]),
            "Object: {}".format(object_string)
        ])
        return sf_string

    def format_csv_line(self):
        line = "{};{};".format(self.src_address, self.dest_address)
        line += "{};".format(SerialMessage.SERVICE_FLAGS[self.service_flags] if self.service_flags in SerialMessage.SERVICE_FLAGS else self.service_flags)
        line += "{};".format(SerialMessage.SERVICE[self.service_id] if self.service_id in SerialMessage.SERVICE else self.service_id)
        line += "{};".format(SerialMessage.OBJECT_TYPE[self.object_type] if self.object_type in SerialMessage.OBJECT_TYPE else self.object_type)
        line += "{};".format(self.object_id)
        line += "0x{:04x};".format(self.property_id)
        line += "0x{};".format(self.property_data_bytes)

        return line

    def to_str(self, indent):
        service_frame_string = self._format_service_frame()

        indent_str = " " * indent

        msg_string = "Total Bytes: {} bytes\nSource: {}\nDestination: {}\nFrame data:{}\n".format(
            self.total_len(),
            self.src_address,
            self.dest_address,
            service_frame_string)

        msg_string = indent_str + msg_string.replace("\n", "\n"+indent_str)

        return msg_string

