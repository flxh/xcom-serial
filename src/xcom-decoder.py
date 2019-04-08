from xcom_serial.parse import parse_next_message, parse_service_frame, parse_object
from xcom_serial.format import SERVICE_FLAGS, SERVICE, OBJECT_TYPE, format_message, format_service_frame, format_object

log_bytes = open("xcom_log.txt", "rb").read()


def write_csv_line(src, dest, service_flags, service_id, object_type, object_id, property_id, property_data):
    line = "{};{};".format(src, dest)
    line += "{};".format(SERVICE_FLAGS[service_flags] if service_flags in SERVICE_FLAGS else service_flags)
    line += "{};".format(SERVICE[service_id] if service_id in SERVICE else service_id)
    line += "{};".format(OBJECT_TYPE[object_type] if object_type in OBJECT_TYPE else object_type)
    line += "{};".format(object_id)
    line += "0x{:04x};".format(property_id)
    line += "0x{};".format(property_data)
    line += "\n"

    with open("output.csv", "a") as file:
        file.write(line)


while len(log_bytes) > 0:
    if log_bytes[0] == 0xAA:
        src_address, dest_address, datalen, data, is_consistent = parse_next_message(log_bytes)
        service_flags, service_id, service_data = parse_service_frame(data)
        object_type, object_id, property_id, property_data = parse_object(service_data)

        write_csv_line(src_address, dest_address, service_flags, service_id, object_type, object_id, property_id, property_data)

        object_string = format_object(object_type, object_id, property_id, property_data)
        service_frame_string = format_service_frame(service_flags,service_id, object_string)
        message_string = format_message(service_frame_string, datalen, src_address, dest_address, is_consistent)
        print(message_string)
    else:
        raise Exception("inconsistent data")

    log_bytes = log_bytes[datalen+14+2:]
