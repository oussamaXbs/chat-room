import tkinter as tk
import socket
import threading
import os
from tkinter import messagebox, filedialog, PhotoImage

# Initialize the main window
window = tk.Tk()
window.resizable(False, False)
window.title("Client")

# Global variables
username = " "
client = None
HOST_ADDR = "127.0.0.1"
HOST_PORT = 55555

# Frame 1 (name and connect button)
topFrame = tk.Frame(window)
lblName = tk.Label(topFrame, text="Username:", font=('Tekton Pro', 11))
lblName.pack(side=tk.LEFT, padx=(0, 5))
entName = tk.Entry(topFrame, width=30, borderwidth=3)
entName.pack(side=tk.LEFT)
entName.bind("<Return>", (lambda event: connect()))
btnConnect = tk.Button(topFrame, text="Connect", font=('sans 11 bold'), command=lambda: connect(), width=8, bd=4, fg='green')
btnConnect.pack(side=tk.LEFT, pady=(7, 7), padx=(15, 0))
topFrame.pack(side=tk.TOP, pady=(10, 0))

# Frame 2 (text and display screens)
displayFrame = tk.Frame(window)
lblLine = tk.Label(displayFrame, text="messages", font=('Tekton Pro', 16)).pack(padx=(0, 0))
tkDisplay = tk.Text(displayFrame, height=20, width=55)
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 10))
tkDisplay.tag_config("tag_your_message", foreground="blue")
tkDisplay.config(background="#F4F6F7", highlightbackground="grey", state="disabled", highlightthickness=2)
displayFrame.pack(side=tk.TOP)

# Frame 3 (message zone and send button)
bottomFrame = tk.Frame(window)
tkMessage = tk.Text(bottomFrame, height=1, width=40, borderwidth=3)
tkMessage.pack(side=tk.LEFT, padx=(0, 0), pady=(5, 5))
tkMessage.config(highlightbackground="grey", state="disabled")
tkMessage.bind("<Return>", (lambda event: getChatMessage(tkMessage.get("1.0", tk.END))))
btntext = tk.Button(bottomFrame, text="send msg", font=('sans 11 bold'), width=8, bd=4, command=lambda: getChatMessage(tkMessage.get("1.0", tk.END)))
btntext.pack(side=tk.RIGHT, pady=(5, 5), padx=(20, 0))
btntext.config(state=tk.DISABLED)
bottomFrame.pack(side=tk.TOP)

# Frame 4 (file sending frame)
bottomFrame2 = tk.Frame(window)
fileLocation = tk.Label(bottomFrame2, text="choose file to send", width=33, bg="#DBE1E3")
fileLocation.pack(side=tk.LEFT, padx=(0, 0), pady=(5, 7))
btnfileSend = tk.Button(bottomFrame2, text="send file", font=('sans 11 bold'), width=8, bd=4)
btnfileSend.pack(side=tk.RIGHT, padx=(0, 0), pady=(5, 7))
btnfileSend.config(state=tk.DISABLED)
btnfileBrowse = tk.Button(bottomFrame2, text="browse", font=('sans 11 bold'), width=8, bd=4, command=lambda: browseFile())
btnfileBrowse.pack(side=tk.RIGHT, padx=(20, 5), pady=(5, 7))
btnfileBrowse.config(state=tk.DISABLED)
bottomFrame2.pack(side=tk.BOTTOM)

def connect():
    global username, client
    if len(entName.get()) < 1:
        messagebox.showerror(title="ERROR!!!", message="You MUST enter your first name <ex. oussama>")
    else:
        username = entName.get()
        connect_to_server(username)

def connect_to_server(name):
    global client, HOST_PORT, HOST_ADDR
    if not name:
        messagebox.showerror(title="ERROR", message="Username cannot be empty.")
        return

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST_ADDR, HOST_PORT))
        client.send(name.encode())

        entName.config(state=tk.DISABLED)
        btnConnect.config(state=tk.DISABLED)
        btntext.config(state=tk.NORMAL)
        btnfileSend.config(state=tk.NORMAL)
        btnfileBrowse.config(state=tk.NORMAL)
        tkMessage.config(state=tk.NORMAL)

        threading.Thread(target=receive_message_from_server, args=(client,), daemon=True).start()
    
    except Exception as e:
        messagebox.showerror(
            title="ERROR", 
            message=f"Cannot connect to host: {HOST_ADDR} on port: {HOST_PORT}. Server may be unavailable. Try again later."
        )

def receive_message_from_server(sck):
    while True:
        try:
            from_server = sck.recv(1024).decode()
            if not from_server:
                break

            # Schedule the UI update on the main thread
            window.after(0, update_display, from_server)

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

    sck.close()
    # Check if the window is still open before attempting to update the UI
    if window.winfo_exists():
        window.after(0, lambda: messagebox.showinfo("Disconnected", "You have been disconnected from the server."))
        window.after(0, window.destroy)

def update_display(message):
    texts = tkDisplay.get("1.0", tk.END).strip()
    tkDisplay.config(state=tk.NORMAL)

    if len(texts) < 1:
        tkDisplay.insert(tk.END, message)
    else:
        tkDisplay.insert(tk.END, "\n\n" + message)

    tkDisplay.config(state=tk.DISABLED)
    tkDisplay.see(tk.END)

def getChatMessage(msg):
    msg = msg.replace('\n', '').strip()

    if not msg:
        return

    texts = tkDisplay.get("1.0", tk.END).strip()
    tkDisplay.config(state=tk.NORMAL)

    if len(texts) < 1:
        tkDisplay.insert(tk.END, "You->" + msg, "tag_your_message")
    else:
        tkDisplay.insert(tk.END, "\n\n" + "You->" + msg, "tag_your_message")

    tkDisplay.config(state=tk.DISABLED)
    tkDisplay.see(tk.END)

    try:
        send_message_to_server(msg)
        tkMessage.delete('1.0', tk.END)
    except Exception as e:
        print(f"Failed to send message: {e}")
        messagebox.showerror("Error", "Message failed to send.")

def send_message_to_server(msg):
    global client

    try:
        client_msg = str(msg)
        client.send(client_msg.encode())

        if msg == "exit":
            client.send("disconnecting".encode())
            window.after(100, lambda: client.close())
            window.after(500, lambda: window.destroy())

        print("Sending message:", msg)
    except Exception as e:
        print("Error sending message:", e)
        messagebox.showerror("Error", "Failed to send message. Please check your connection.")

def browseFile():
    try:
        filename = filedialog.askopenfilename(
            initialdir="/",
            title="Select a file",
            filetypes=(("Text files", "*.txt*"), ("All files", "*.*"))
        )
        
        if filename:
            fileLocation.configure(text="File Opened: " + os.path.basename(filename))
            return filename
        else:
            fileLocation.configure(text="No file selected")
    except Exception as e:
        fileLocation.configure(text="Error opening file")
        print("Error:", e)

def on_closing():
    if client:
        print("Sending exit message to server.")
        client.send("exit".encode())
        client.close()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

p1 = PhotoImage(file='images.png')
window.iconphoto(False, p1)
window.mainloop()
