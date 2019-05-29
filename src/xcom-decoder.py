from SerialMessage import SerialMessage, parse_data_len

log_bytes = open("xcom_log.txt", "rb").read()

def write_csv_line(line):
    with open("output.csv", "a") as file:
        file.write(line+"\n")


while len(log_bytes) > 0:
    header_bytes = log_bytes[:14]
    datalen = parse_data_len(header_bytes)

    msg_bytes = log_bytes[:14+datalen+2]

    msg = SerialMessage.from_bytes(msg_bytes)

    write_csv_line(msg.format_csv_line())

    print(msg.to_bytes())
    print(msg.to_str(0))

    log_bytes = log_bytes[datalen+14+2:]
