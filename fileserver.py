import socket
import threading
import os
import tqdm
import time
from concurrent.futures import ThreadPoolExecutor

HOST = 'localhost'
PORT = 7072
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
    conn.send(str(filesize).encode(FORMAT))
    
    with open(file_path, "rb") as file:
        data = file.read() + b"<END>"
        conn.sendall(data)

def file_upload(conn):
    selectedFile = conn.recv(SIZE).decode(FORMAT)
    file_size = conn.recv(SIZE).decode(FORMAT)
    file_path = f"./Server/{selectedFile}"

    with open(file_path, "wb") as file:
        progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=float(file_size))
        data_bytes = b""
        while True:
            data = conn.recv(SIZE)
            if data_bytes[-5:] == b"<END>":
                break
            file.write(data)
            data_bytes += data
            progress.update(len(data))
    print("File received successfully.")

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
