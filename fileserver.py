import socket
import threading
import os
import tqdm
import time
from concurrent.futures import ThreadPoolExecutor

HOST = 'localhost'
PORT = 7070
SIZE = 1024
FORMAT = 'utf-8'
MAX_CONNECTIONS = 5

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

# Dictionary to store clients and the file they are working on
file_sessions = {}
file_locks = {}

def broadcast_updates(filename, content, exclude_conn):
    for conn in file_sessions:
        if file_sessions[conn] == filename and conn != exclude_conn:
            try:
                conn.send(f"update:{content}".encode(FORMAT))
            except Exception as e:
                print(f"Error broadcasting to {conn}: {e}")

def file_collab(conn):
    # conn.send("Select a file to collaborate on:".encode(FORMAT))
    arr = os.listdir("./Server")
    send_data = "\n".join(arr)
    conn.send(send_data.encode(FORMAT))

    filename = conn.recv(SIZE).decode(FORMAT)
    file_path = f"./Server/{filename}"
    print(filename + file_path)
    file_sessions[conn] = file_path

    # Sending the initial content of the file
    with open(file_path, "r") as file:
        content = file.read()
        conn.send(content.encode(FORMAT))

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        if data == "quit":
            break
        if data.startswith("edit:"):
            _, new_content = data.split(":", 1)
            with open(file_path, "w") as file:
                file.write(new_content)
            broadcast_updates(file_path, new_content, conn)

def file_download(conn):
    arr = os.listdir("./Server")
    send_data = "\n".join(arr)
    conn.send(send_data.encode(FORMAT))

    filename = conn.recv(SIZE).decode(FORMAT)
    if filename == "quit":
        return
    file_path = f"./Server/{filename}"
    filesize = os.path.getsize(file_path)
    # conn.send(str(filesize).encode(FORMAT))
    
    ### Send with implemented TCP Flow Control and TCP Conjestion control


    seq_num = 0
    cwnd = 1
    ssthresh = 1024
    # ack = conn.recv(1024).decode()

    file = open(file_path, "rb")
    window_size = 4  # set the window size to 4
    packets = []
    current_packet = 0
    total_packets = (filesize // 1024) + 1
    
    print(total_packets)
    # conn.send(str(total_packets).encode(FORMAT))

    for i in range(total_packets):
        file_data = file.read(1024)
        packets.append(file_data)
    conn.send(f"{total_packets}".encode())
    # print(basename)
    ackk = conn.recv(1024).decode()
    if ackk == "sz":
        while current_packet < total_packets:
            for i in range(total_packets):
                conn.send(packets[i])
                print(packets[i])
                try:
                    ack = conn.recv(1024).decode()
                    if ack == "ACK":
                        current_packet += 1
                        if seq_num == len(file_data):
                            # All packets have been acknowledged
                            break
                        if cwnd < ssthresh:
                            cwnd *= 2
                        else:
                            cwnd += 1
                    print(cwnd)
                    print(f"Packet {current_packet} acknowledged.")
                except:
                    ssthresh=max(cwnd/2,1)
                    cwnd=1

                    continue
    else:
        print('sz not rcvd')
    file.close()

    print(f" Total {current_packet} Packet acknowledged.")
    print("Data has been transmitted successfully...")
    # send_btn.destroy()
    # Label(window, text=f'Data has been transmitted successfully...', font=('Acumin Variable Concept', 13,),
        #   bg='#7FFFD4', fg="#000").place(
        # x=90, y=350)
        
    # conn.close()

def file_upload(conn):
    
    # filename = conn.recv(1024).decode()
    # print(filename)
    # filesize = os.path.getsize(filename)
    # file_size = conn.recv(1024).decode("utf-8")
    # print(file_size)
    name = ".\\Server\\new_file.pdf"
    file = open(name, "wb")

    sz = conn.recv(1024).decode()
    print(sz)
    sz = int(sz)
    conn.send("sz".encode())
    file = open(name, "wb")

    current_packet = 0
    while True:
        if current_packet == sz:
            break
        try:
            file_data = conn.recv(1024)
            if not file_data:
                break
            file.write(file_data)
            conn.send("ACK".encode())  # sending ACK for each packet received
            current_packet += 1
            print(f"Packet {current_packet} received.")
        except:
            continue
    file.close()

    print(f"Total {current_packet} Packet  received.")
    print("file has been received successfully..")
    # rr.destroy()
    # Label(main, text=f'File has been received successfully.....', font=('Acumin Variable Concept', 13,),
    #         bg='#7FFFD4', fg="#000").place(x=90, y=360)

    print("File received successfully.")

def file_upload(conn):
    selectedFile = conn.recv(SIZE).decode(FORMAT)
    file_size = conn.recv(SIZE).decode(FORMAT)
    conn.send("sz".encode())
    file_path = f"./Server/{selectedFile}"
    file = open(file_path, "wb")
    
    current_packet = 0
    while True:
        if current_packet == file_size:
            break
        try:
            file_data = conn.recv(1024)
            if not file_data:
                break
            file.write(file_data)
            conn.send("ACK".encode())  # sending ACK for each packet received
            current_packet += 1
            print(f"Packet {current_packet} received.")
        except:
            continue
    file.close()

    print(f"Total {current_packet} Packet  received.")
    print("file has been received successfully..")

def handle_client(conn, address):
    print(f"[NEW CONNECTION] Connected to {address}")
    option = conn.recv(SIZE).decode(FORMAT)
    if option == "download":
        file_download(conn)
    elif option == "upload":
        file_upload(conn)
    elif option == "collaborate":
        file_collab(conn)
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")    
    with ThreadPoolExecutor(max_workers=MAX_CONNECTIONS) as executor:
        while True:
            client_conn, address = server.accept()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            executor.submit(handle_client, client_conn, address)

print("[STARTING] Server is starting...")
start()
