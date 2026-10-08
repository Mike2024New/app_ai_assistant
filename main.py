import customtkinter as ctk

root = ctk.CTk()
root.geometry('300x200+600+300')
label = ctk.CTkLabel(root, text_color='tomato', text='Заглушка', font=('roboto', 18))
label.pack(padx=10, pady=10)
btn = ctk.CTkButton(root, text='выйти', command=lambda: root.destroy())
btn.pack()
root.mainloop()
