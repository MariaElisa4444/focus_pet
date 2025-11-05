import customtkinter as ctk
from PIL import Image, ImageTk

# Настройки CustomTkinter
ctk.set_appearance_mode("light")

# Главное окно
root = ctk.CTk()
root.title("Focus Pet 🐾")
root.geometry("1536x1024")

# Фон приложения
background_image = Image.open("images/focuspet1.png")
bg = ImageTk.PhotoImage(background_image)
bg_label = ctk.CTkLabel(master=root, image=bg, text="")
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# === Картинки кота ===
# 19 картинок: нейтральные, учеба, сон, радость, промежуточные кадры
CAT_IMAGES = {
    "neutral": ["images/cat1.png"],
    "study": ["images/cat2.png", "images/cat3.png", "images/cat4.png"],
    "sleep": ["images/cat5.png", "images/cat6.png", "images/cat7.png"],
    "happy": ["images/cat8.png", "images/cat9.png", "images/cat10.png"],
    "to_sleep": ["images/cat11.png", "images/cat12.png"],
    "to_happy": ["images/cat13.png", "images/cat14.png"],
    "to_neutral": ["images/cat15.png", "images/cat16.png"],
    "study_intermediate": ["images/cat17.png"],
    "happy_intermediate": ["images/cat18.png"],
    "sleep_intermediate": ["images/cat19.png"]
}

# === Функция загрузки картинки кота ===
def load_image(path):
    img = Image.open(path)
    return ImageTk.PhotoImage(img)

# === Показ кота на экране ===
cat_label = None
def show_cat(img_path):
    global cat_label
    img = load_image(img_path)
    cat_label.configure(image=img)
    cat_label.image = img

# === Анимация кота (последовательность кадров) ===
def animate_sequence(sequence, delay=500):
    """sequence — список путей к картинкам кота"""
    def next_frame(i=0):
        if i < len(sequence):
            show_cat(sequence[i])
            root.after(delay, next_frame, i+1)
    next_frame()

# === Реакция кнопок ===
def start_session():
    print("Учёба началась!")
    # пример: нейтральный → промежуточный → учеба
    frames = CAT_IMAGES["neutral"] + CAT_IMAGES["study_intermediate"] + CAT_IMAGES["study"]
    animate_sequence(frames)

def pause_session():
    print("Перерыв!")
    frames = CAT_IMAGES["study"] + CAT_IMAGES["to_sleep"] + CAT_IMAGES["sleep_intermediate"] + CAT_IMAGES["sleep"]
    animate_sequence(frames)

def stop_session():
    print("Сессия завершена!")
    frames = CAT_IMAGES["neutral"] + CAT_IMAGES["to_happy"] + CAT_IMAGES["happy_intermediate"] + CAT_IMAGES["happy"]
    animate_sequence(frames)

# === Стили кнопок ===
button_font = ("Arimo", 30)
normal_color = "#a6a6a6"
pressed_color = "#7a7a7a"

# === Стартовый экран ===
def show_start_screen():
    for widget in root.winfo_children():
        widget.place_forget()
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Название приложения
    title = ctk.CTkLabel(
        master=root,
        text="Focus Pet 🐾",
        font=("Arimo", 100, "bold"),
        text_color="#ffffff",
        bg_color="transparent"
    )
    title.place(relx=0.5, rely=0.3, anchor="center")

    # Кнопка START
    start_button = ctk.CTkButton(
        master=root,
        text="START",
        font=("Arimo", 60),
        text_color="#ffffff",
        fg_color=normal_color,
        hover_color=pressed_color,
        corner_radius=60,
        width=300,
        height=100,
        command=show_main_screen
    )
    start_button.place(relx=0.5, rely=0.7, anchor="center")

# === Экран с котом и кнопками ===
def show_main_screen():
    for widget in root.winfo_children():
        widget.place_forget()
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    global cat_label
    # Показываем кота в нейтральном состоянии
    img = load_image(CAT_IMAGES["neutral"][0])
    cat_label = ctk.CTkLabel(master=root, image=img, text="")
    cat_label.image = img
    cat_label.place(relx=0.5, rely=0.5, anchor="center")

    # Кнопки START / PAUSE / STOP в правом нижнем углу
    start_btn = ctk.CTkButton(
        master=root,
        text="START",
        font=button_font,
        text_color="#ffffff",
        fg_color=normal_color,
        hover_color=pressed_color,
        corner_radius=50,
        width=160,
        height=70,
        command=start_session
    )
    pause_btn = ctk.CTkButton(
        master=root,
        text="PAUSE",
        font=button_font,
        text_color="#ffffff",
        fg_color=normal_color,
        hover_color=pressed_color,
        corner_radius=50,
        width=160,
        height=70,
        command=pause_session
    )
    stop_btn = ctk.CTkButton(
        master=root,
        text="STOP",
        font=button_font,
        text_color="#ffffff",
        fg_color=normal_color,
        hover_color=pressed_color,
        corner_radius=50,
        width=160,
        height=70,
        command=stop_session
    )

    # Размещаем кнопки в ряд в правом нижнем углу
    start_btn.place(relx=0.65, rely=0.85, anchor="center")
    pause_btn.place(relx=0.78, rely=0.85, anchor="center")
    stop_btn.place(relx=0.91, rely=0.85, anchor="center")

# === Запуск приложения ===
show_start_screen()
root.mainloop()