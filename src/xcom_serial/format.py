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


def format_object(object_type, object_id, prop_id, prop_data):
    object_string = "\n\t\t" + "\n\t\t".join([
        "Object type: 0x{:04x} - {}".format(object_type, OBJECT_TYPE[object_type]),
        "Object id: 0x{:04x} - {}".format(object_id, object_id),
        "Property id: 0x{:04x}".format(prop_id),
        "Property Data: {}".format(prop_data)
    ])
    return object_string


def format_service_frame(service_flags, service_id, object_string):
    sf_string = "\n\t" + "\n\t".join([
        "Service flags: 0x{:02X} - {}".format(service_flags, SERVICE_FLAGS[service_flags]),
        "Service id: 0x{:02X} - {}".format(service_id, SERVICE[service_id]),
        "Object: {}".format(object_string)
    ])
    return sf_string


def format_message(service_frame_string, datalen, src_address, dest_address, is_consistent):
    return "Data length: {} bytes\nSource: {}\nDestination: {}\nFrame data:{}\nConsistent:{}\n".format(datalen, src_address, dest_address, service_frame_string, is_consistent)

