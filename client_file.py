import socket
import os
import tqdm
import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, Scrollbar, Toplevel
import threading

BUFFER_SIZE = 4096
HOST = 'localhost'
PORT = 7072
FORMAT = 'utf-8'

class FileClientApp:
    def __init__(self, root, client_name):
        self.root = root
        self.client_name = client_name
        self.root.title(f"File Client - {self.client_name}")
        self.root.geometry("500x500")

        self.style_gui()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((HOST, PORT))

    def style_gui(self):
        # Apply styling to the main window
        self.root.configure(bg="lightblue")

        # Center the buttons in the main window
        self.button_frame = tk.Frame(self.root, bg="lightblue")
        self.button_frame.pack(expand=True)

        self.download_button = tk.Button(self.button_frame, text="Download", command=self.show_download_window, bg="lightpink", fg="black")
        self.download_button.pack(pady=10)

        self.upload_button = tk.Button(self.button_frame, text="Upload", command=self.upload_file, bg="lightpink", fg="black")
        self.upload_button.pack(pady=10)

        self.collaborate_button = tk.Button(self.button_frame, text="Collaborate", command=self.show_collab_window, bg="lightpink", fg="black")
        self.collaborate_button.pack(pady=10)

    def show_download_window(self):
        download_window = Toplevel(self.root)
        download_window.title("Download File")
        download_window.geometry("500x500")
        download_window.configure(bg="lightblue")

        scrollbar = Scrollbar(download_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = Listbox(download_window, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(expand=True, fill=tk.BOTH)

        self.client_socket.send("download".encode(FORMAT))
        files = self.client_socket.recv(1024).decode(FORMAT).split("\n")

        for file in files:
            self.file_listbox.insert(tk.END, file)

        scrollbar.config(command=self.file_listbox.yview)

        button_frame = tk.Frame(download_window, bg="lightblue")
        button_frame.pack(pady=10)

        download_button = tk.Button(button_frame, text="Download Selected", command=self.download_selected_file, bg="lightpink", fg="black")
        download_button.pack(side=tk.LEFT, padx=5)

        manual_download_button = tk.Button(button_frame, text="Enter File Name", command=self.download_manual_file, bg="lightpink", fg="black")
        manual_download_button.pack(side=tk.LEFT, padx=5)

        close_button = tk.Button(button_frame, text="Close", command=download_window.destroy, bg="lightpink", fg="black")
        close_button.pack(side=tk.LEFT, padx=5)

    def download_selected_file(self):
        selected_file = self.file_listbox.get(tk.ACTIVE)
        if selected_file:
            self.client_socket.send(selected_file.encode(FORMAT))
            self.receive_file(selected_file)

    def download_manual_file(self):
        selected_file = simpledialog.askstring("Download File", "Enter the file name to download:")
        if selected_file:
            self.client_socket.send(selected_file.encode(FORMAT))
            self.receive_file(selected_file)

    def receive_file(self, filename):
        file_size = self.client_socket.recv(1024).decode()
        print(f"File size: {file_size} bytes")

        downloads_dir = "./Downloads/"
        os.makedirs(downloads_dir, exist_ok=True)

        file_path = os.path.join(downloads_dir, filename)
        with open(file_path, "wb") as file:
            progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=float(file_size))
            data_bytes = b""
            while True:
                data = self.client_socket.recv(1024)
                if data_bytes[-5:] == b"<END>":
                    break
                file.write(data)
                data_bytes += data
                progress.update(len(data))
        print("File received successfully.")

    def upload_file(self):
        self.client_socket.send("upload".encode(FORMAT))
        filename = simpledialog.askstring("Upload File", "Enter the file name to upload:")

        if filename and os.path.isfile(filename):
            filesize = str(os.path.getsize(filename))
            self.client_socket.send(filename.encode(FORMAT))
            self.client_socket.send(filesize.encode(FORMAT))

            with open(filename, "rb") as file:
                data = file.read() + b"<END>"
                self.client_socket.sendall(data)
            print("File sent successfully.")
        else:
            messagebox.showerror("Error", "File not found!")

    def show_collab_window(self):
        collab_window = Toplevel(self.root)
        collab_window.title("Select File to Collaborate [PDFs cannot be edited]")
        collab_window.geometry("300x300")
        collab_window.configure(bg="lightblue")

        scrollbar = Scrollbar(collab_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = Listbox(collab_window, yscrollcommand=scrollbar.set)
        listbox.pack(expand=True, fill=tk.BOTH)

        self.client_socket.send("collaborate".encode(FORMAT))
        files = self.client_socket.recv(1024).decode(FORMAT).split("\n")
        for file in files:
            listbox.insert(tk.END, file)

        scrollbar.config(command=listbox.yview)

        def on_file_select():
            selected_file = listbox.get(tk.ACTIVE)
            if selected_file:
                self.open_collab_editor(selected_file)

        select_button = tk.Button(collab_window, text="Select", command=on_file_select, bg="lightpink", fg="black")
        select_button.pack(pady=5)

    def open_collab_editor(self, filename):
        self.client_socket.send(filename.encode(FORMAT))
        initial_content = self.client_socket.recv(1024).decode(FORMAT)

        editor_window = Toplevel(self.root)
        editor_window.title("Collaborate on File")
        editor_window.geometry("500x500")
        editor_window.configure(bg="lightblue")

        collab_text = tk.Text(editor_window, wrap=tk.WORD, bg="white", fg="black")
        collab_text.insert(tk.END, initial_content)
        collab_text.pack(expand=True, fill=tk.BOTH)

        def on_text_change(event):
            current_content = collab_text.get(1.0, tk.END).strip()
            self.client_socket.send(f"edit:{current_content}".encode(FORMAT))

        collab_text.bind("<KeyRelease>", on_text_change)

        threading.Thread(target=self.receive_collab_updates, args=(collab_text,)).start()

    def receive_collab_updates(self, text_widget):
        while True:
            try:
                update = self.client_socket.recv(1024).decode(FORMAT)
                if update.startswith("update:"):
                    new_content = update[len("update:"):]
                    text_widget.delete(1.0, tk.END)
                    text_widget.insert(tk.END, new_content)
            except Exception as e:
                print(f"Error receiving collaboration update: {e}")
                break

def get_client_name():
    name_window = tk.Tk()
    name_window.title("Enter Name")
    name_window.geometry("300x150")
    name_window.configure(bg="lightblue")

    tk.Label(name_window, text="Enter your name:", bg="lightblue", fg="black").pack(pady=20)

    name_var = tk.StringVar()
    name_entry = tk.Entry(name_window, textvariable=name_var, bg="white", fg="black")
    name_entry.pack(pady=10)

    def submit_name():
        client_name = name_var.get()
        if client_name:
            name_window.destroy()
            root = tk.Tk()
            app = FileClientApp(root, client_name)
            root.mainloop()
        else:
            messagebox.showwarning("Input Error", "Name cannot be empty")

    submit_button = tk.Button(name_window, text="Submit", command=submit_name, bg="lightpink", fg="black")
    submit_button.pack(pady=10)

    name_window.mainloop()

if __name__ == "__main__":
    get_client_name()
