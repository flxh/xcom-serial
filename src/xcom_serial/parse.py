import struct


def calculate_checksum(data_bytes):
    a = 0xFF
    b = 0
    for byte in data_bytes:
        a = (a + byte) % 0x100
        b = (a + b) % 0x100

    return bytes([a,b])


def is_data_constistent(data_bytes, checksum):

    return checksum == calculate_checksum(data_bytes)


def convert_bytes_to_int(bytes):
    x = 0
    for i in range(len(bytes)):
        x += bytes[i] << 8*i
    return x


def convert_bytes_to_float(b):
    return struct.unpack("<f", bytes.fromhex(b))[0]


def convert_float_to_bytes(f):
    return struct.pack("<f", f)


def parse_service_frame(data):
    service_flag_byte = data[0]
    service_id = data[1]
    service_data = data[2:]

    return service_flag_byte, service_id, service_data


def parse_object(service_data):
    object_type = convert_bytes_to_int(service_data[:2])
    object_id = convert_bytes_to_int(service_data[2:6])
    property_id =convert_bytes_to_int( service_data[6:8])
    property_data = ''.join('{:02X}'.format(x) for x in service_data[8:])

    return object_type, object_id, property_id, property_data


def parse_next_message(log_bytes):
    header_bytes = log_bytes[0:14]
    datalen, dest_address, src_address = parse_header(header_bytes)

    begin_checksum = 14+datalen
    data = log_bytes[14:begin_checksum]

    checksum_bytes = log_bytes[begin_checksum:begin_checksum+2]
    is_consistent = is_data_constistent(data, checksum_bytes)

    return src_address, dest_address, datalen, data, is_consistent


def parse_header(header_bytes):
    datalen_bytes = header_bytes[10:12]
    src_address = header_bytes[2:6]
    dest_address = header_bytes[6:10]
    datalen = convert_bytes_to_int(datalen_bytes)
    src_address = convert_bytes_to_int(src_address)
    dest_address = convert_bytes_to_int(dest_address)
    return datalen, dest_address, src_address
