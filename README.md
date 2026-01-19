# Networks_Project


# Computer Networks – Client Server Project

This project was developed as part of the Computer Networks course.
It demonstrates low-level TCP communication, manual packet construction,
network traffic analysis, and an extended graphical chat application
implemented as a bonus part.

---

## Project Structure

.
├── basic_client_server/
│   ├── client.py
│   ├── server.py
│   ├── main.py
│   └── group01_http_input.csv
│
├── UI_client_server/
│   ├── GUI_client.py
│   └── serverUI.py
│
├── Wireshark_captures/
│   ├── group01_http_capture.pcapng
│   └── group02_tcp_capture.pcapng
│
├── project report.docx
├── requirements.txt
└── README.md

---

## Part 1 – Packet Construction & Traffic Analysis

In this part, application-layer messages are read from a CSV file and used
as payloads for manually constructed TCP packets.

- IP and TCP headers are built manually
- Checksums are calculated explicitly
- Packets are sent using Scapy
- Traffic is captured and analyzed using Wireshark

### Run:
python main.py

---

## Part 2 – Basic Client Server (CLI)

A multi-client chat system implemented using TCP sockets.

### Features:
- Thread-per-client server architecture
- Username registration with validation
- Public and private messaging
- Graceful client disconnection handling

### Run:
Server:
python server.py

Client:
python client.py

---

## Bonus – GUI Client Server

An extended version of the chat application with a graphical interface.

### Features:
- Graphical user interface using CustomTkinter
- User avatars with real-time updates
- Dynamic online users list
- Private messaging
- Ability to launch a local server from the UI
- Graceful server shutdown command

### Run:
Server:
python serverUI.py

Client:
python GUI_client.py

---

## Requirements

Install required Python packages:
pip install -r requirements.txt

### Required Libraries:
- pandas
- scapy
- customtkinter
- Pillow

---

## Notes

- The GUI extension is implemented as a bonus part.
- All communication is based on raw TCP sockets.
- No external networking frameworks were used.
- Wireshark capture files are included for analysis.

---

## Authors

Developed as part of an academic course in Computer Networks.
