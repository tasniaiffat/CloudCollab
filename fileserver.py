import socket
import threading
import os
import tqdm
import time

HOST = 'localhost'
PORT = 7071
SIZE = 1024
FORMAT = 'utf-8'
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

def file_download(conn):
    arr = os.listdir("./Server")
    send_data = "\n".join(arr)
    conn.send(send_data.encode(FORMAT))

    filename = conn.recv(SIZE).decode()
    print(filename)
    
    if filename == "quit":
        return

    filename = "./Server/" + filename  
    filesize = os.path.getsize(filename)
    
    conn.send(str(filesize).encode())
    
    with open(filename, "rb") as file:
        data = file.read() + b"<END>"
        conn.sendall(data)

def file_upload(conn):
    selectedFile = conn.recv(1024).decode()
    file_size = conn.recv(1024).decode("utf-8")
    name = "./Server/" + selectedFile
    print(name)

    with open(name, "wb") as file:
        progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=float(file_size))
        data_bytes = b""
        while True:
            data = conn.recv(1024)
            if data_bytes[-5:] == b"<END>":
                break
            file.write(data)
            data_bytes += data
            progress.update(len(data))
    print("File received successfully.")

def handle_client(conn, address):
    print(f"[NEW CONNECTION] Connected to {address}")
    time.sleep(2)
    option = conn.recv(1024).decode()
    print(option)
    if option == "download":
        file_download(conn)
    else:
        file_upload(conn)           
        
    conn.close()

def start():
    while True:
        server.listen()
        print(f"[LISTENING] Server is listening on {HOST}:{PORT}")    
        while True:
            client_conn, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_conn, address))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] Server is starting...")
start()
