import pandas as pd
import struct
import socket
from scapy.all import IP, TCP, Raw, send


# ============================= Helper Functions =============================

def validate_csv_format(df):
    """
    Make sure the CSV file contains all required columns.
    This prevents runtime errors later in the process.
    """
    expected_columns = [
        "msg_id",
        "app_protocol",
        "src_app",
        "dst_app",
        "message",
        "timestamp"
    ]
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError(f"Missing expected column: {col}")


def checksum(data: bytes) -> int:
    """
    Calculate Internet checksum (used by IP/TCP).
    The data is processed as 16-bit words.
    """
    if len(data) % 2:
        data += b'\0'

    res = sum(struct.unpack('!%dH' % (len(data) // 2), data))

    # Handle carry bits
    while res >> 16:
        res = (res & 0xFFFF) + (res >> 16)

    return ~res & 0xFFFF


def build_tcp_header(src_ip, dst_ip, src_port, dst_port, payload=b''):
    """
    Build a raw TCP header manually, including checksum calculation.
    This is done for learning and demonstration purposes.
    """
    seq_num = 0
    ack_num = 0

    data_offset = 5  # TCP header length (5 * 4 = 20 bytes)
    flags = 0x18     # PSH + ACK
    offset_and_flags = (data_offset << 12) | flags

    window_size = 8192
    checksum_tcp = 0
    urgent_pointer = 0

    # Initial TCP header with checksum set to zero
    tcp_header = struct.pack(
        "!HHLLHHHH",
        src_port,
        dst_port,
        seq_num,
        ack_num,
        offset_and_flags,
        window_size,
        checksum_tcp,
        urgent_pointer
    )

    # Pseudo header is required for TCP checksum calculation
    pseudo_header = struct.pack(
        "!4s4sBBH",
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
        0,
        socket.IPPROTO_TCP,
        len(tcp_header) + len(payload)
    )

    # Calculate the real TCP checksum
    checksum_tcp = checksum(pseudo_header + tcp_header + payload)

    # Rebuild TCP header with correct checksum
    tcp_header = struct.pack(
        "!HHLLHHHH",
        src_port,
        dst_port,
        seq_num,
        ack_num,
        offset_and_flags,
        window_size,
        checksum_tcp,
        urgent_pointer
    )

    return tcp_header


def build_ip_header(src_ip, dst_ip, payload_length):
    """
    Build a raw IPv4 header manually.
    """
    version = 4
    ihl = 5
    version_ihl = (version << 4) | ihl

    tos = 0
    total_length = 20 + payload_length
    identification = 54321
    flags_fragment = 0
    ttl = 64
    protocol = socket.IPPROTO_TCP
    checksum_ip = 0

    src_ip_bytes = socket.inet_aton(src_ip)
    dst_ip_bytes = socket.inet_aton(dst_ip)

    # Initial IP header with checksum set to zero
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        tos,
        total_length,
        identification,
        flags_fragment,
        ttl,
        protocol,
        checksum_ip,
        src_ip_bytes,
        dst_ip_bytes
    )

    # Calculate IP checksum
    checksum_ip = checksum(ip_header)

    # Rebuild IP header with correct checksum
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        tos,
        total_length,
        identification,
        flags_fragment,
        ttl,
        protocol,
        checksum_ip,
        src_ip_bytes,
        dst_ip_bytes
    )

    return ip_header


# ============================= Stage 1: CSV Processing =============================

filename = "group01_http_input.csv"
messages_df = pd.read_csv(filename)

# Display first rows for verification
print(messages_df.head())

# Replace missing messages with empty strings
messages_df['message'] = messages_df['message'].fillna('')

# Validate CSV structure before continuing
validate_csv_format(messages_df)


# ============================= TCP Preparation =============================

SRC_PORT = 50000
DST_PORT = 80

# Print TCP preparation details (for demonstration)
for index, row in messages_df.iterrows():
    message = row["message"]
    print("Preparing TCP segment:")
    print(f"  src_port = {SRC_PORT}")
    print(f"  dst_port = {DST_PORT}")
    print(f"  payload  = {message}")
    print("-" * 40)

# Build a sample TCP header (without payload)
tcp = build_tcp_header(
    "127.0.0.1",
    "127.0.0.1",
    SRC_PORT,
    DST_PORT,
    b""
)

print(len(tcp))
print(tcp)


# ============================= Packet Sending =============================

# Send packets using Scapy (actual transmission)
# Manual headers above are for learning; Scapy handles real sending
for index, row in messages_df.iterrows():
    message = row["message"].encode()

    packet = IP(src="127.0.0.1", dst="127.0.0.1") / \
             TCP(sport=50000, dport=80, flags="PA") / \
             Raw(load=message)

    send(packet, verbose=False)
