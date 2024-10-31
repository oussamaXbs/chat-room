import tkinter as tk
import socket
import threading
from tkinter import PhotoImage, messagebox

window = tk.Tk()
window.title("ChatRoom Server")
window.resizable(False, False)

# Frame 1 (2 buttons)
topFrame = tk.Frame(window)
btnStart = tk.Button(topFrame, text="Connect", font=('Tekton Pro', 11), command=lambda: start_server(), width=8, bd=4, fg='green')
btnStart.pack(side=tk.LEFT, pady=(7, 0))
btnStop = tk.Button(topFrame, text="Stop", font=('Tekton Pro', 11), command=lambda: stop_server(), width=8, bd=4, fg='red', state=tk.DISABLED)
btnStop.pack(side=tk.LEFT, pady=(7, 0), padx=(15, 0))
topFrame.pack(side=tk.TOP, pady=(5, 0))

# Frame 2 (port and host)
middleFrame = tk.Frame(window)
lblHost = tk.Label(middleFrame, text="Host: unknown")
lblHost.pack(side=tk.LEFT)
lblPort = tk.Label(middleFrame, text="Port:XXXX")
lblPort.pack(side=tk.LEFT)
middleFrame.pack(side=tk.TOP, pady=(5, 0))

# Frame 3 (clients area)
clientFrame = tk.Frame(window)
lblLine = tk.Label(clientFrame, text="********Client List********", font=('Tekton Pro', 16)).pack()
scrollBar = tk.Scrollbar(clientFrame)
scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
tkDisplay = tk.Text(clientFrame, height=15, width=30)
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
scrollBar.config(command=tkDisplay.yview)
tkDisplay.config(yscrollcommand=scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
clientFrame.pack(side=tk.BOTTOM, pady=(5, 10))

server = None
HOST_ADDR = "127.0.0.1"
HOST_PORT = 55555
clients = []
clients_names = []
lock = threading.Lock()

def start_server():
    global server, HOST_ADDR, HOST_PORT
    try:
        btnStart.config(state=tk.DISABLED)
        btnStop.config(state=tk.NORMAL)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST_ADDR, HOST_PORT))
        server.listen(5)
        print("Server started on:", HOST_ADDR, "Port:", HOST_PORT)

        threading.Thread(target=accept_clients, args=(server,), daemon=True).start()

        lblHost["text"] = "Host: " + HOST_ADDR
        lblPort["text"] = "Port: " + str(HOST_PORT)
        
    except Exception as e:
        print("Error starting server:", e)

def stop_server():
    global server
    try:
        btnStart.config(state=tk.NORMAL)
        btnStop.config(state=tk.DISABLED)

        if server:
            server.close()
            print("Server stopped.")
        
    except Exception as e:
        print("Error stopping the server:", e)

def accept_clients(the_server):
    try:
        while True:
            client, addr = the_server.accept()
            print(f"Connection accepted from {addr}")

            with lock:
                clients.append(client)

            threading.Thread(target=send_receive_client_message, args=(client, addr), daemon=True).start()
    except Exception as e:
        print("Error accepting clients:", e)

def send_receive_client_message(client_connection, client_ip_addr):
    global clients, clients_names

    try:
        client_name = client_connection.recv(1024).decode()
        welcome_msg = f"Welcome {client_name}! Use 'exit' to quit the conversation."
        client_connection.send(welcome_msg.encode())

        with lock:
            clients_names.append(client_name)
            update_client_names_display(clients_names)

        for c in clients:
            if c != client_connection:
                add_msg = f"{client_name} joined the chat!!"
                c.send(add_msg.encode())

        while True:
            data = client_connection.recv(1024).decode()
            if not data:
                print(f"{client_name} disconnected unexpectedly.")
                break

            if data == "exit":
                print(f"{client_name} has exited the chat.")
                break

            for c in clients:
                if c != client_connection:
                    server_msg = f"{client_name} -> {data}"
                    c.send(server_msg.encode())

    except Exception as e:
        print(f"Error while handling client {client_name}: {e}")

    finally:
        with lock:
            if client_connection in clients:
                idx = clients.index(client_connection)
                client_name = clients_names[idx]
                del clients_names[idx]
                del clients[idx]

                for c in clients:
                    if c != client_connection:
                        add_msg = f"{client_name} left the chat!!"
                        c.send(add_msg.encode())

                update_client_names_display(clients_names)

        client_connection.close()

def update_client_names_display(name_list):
    tkDisplay.config(state=tk.NORMAL)
    tkDisplay.delete('1.0', tk.END)

    for c in name_list:
        tkDisplay.insert(tk.END, c + "\n")
    tkDisplay.config(state=tk.DISABLED)

p1 = PhotoImage(file='server.png')
window.iconphoto(False, p1)
window.mainloop()
