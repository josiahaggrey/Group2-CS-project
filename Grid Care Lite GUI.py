from tkinter import* 
from tkinter  import messagebox
window= Tk() #creates an instance of a window
window.title("GridCare-Lite") #This is the title of the gui
window.geometry("420x420")
window.config(background="#333333")# This is used when you want to make any changes to the code
# pack() places it in the centre , grid() places it at the position used. 
def login():
    username="admin1"
    password="admin123"
    if username_entry.get()==username and password_entry.get()==password:
        messagebox.showinfo(title="Login Success",message="You successfully logged in.")
    else:
        messagebox.showerror(title="Error",message="Invalid Login.")
frame= Frame(bg="#333333")# Put all objects inside
login_label= Label(frame,text="Login",bg="#333333",fg="#FFFFFF",font=("Arial",30))
username_label=Label(frame,text="Username",bg="#333333",fg="#FFFFFF",font=("Arial",16))
username_entry=Entry(frame,font=("Arial",16))
password_entry=Entry(frame,show="*",font=("Arial",16))
password_label=Label(frame,text="Password",bg="#333333",fg="#FFFFFF",font=("Arial",16))
login_button= Button(frame,text="Login",bg="#FF3399",fg="#FFFFFF",command=login)
frame.pack()
login_label.grid(row=0,column=0,columnspan=2,sticky="news",pady=40)  # This mean we are telling the grid to take up space in all 4 directions which is north,west,east,south and the pady creates space between each word
username_label.grid(row=1,column=0)
username_entry.grid(row=1,column=1,pady=20)
password_label.grid(row=2,column=0)
password_entry.grid(row=2,column=1,pady=20)
login_button.grid(row=3,column=0,columnspan=2,pady=30)

 


window.mainloop() #This is used to create the window
 
