# menu_panel.py
# See fail sisaldab KÜLGMENÜÜ koodi
# Külgmenüü on see paneel vasakul, kust kasutaja saab valida fookusaja, pauside pikkuse, sessioonide arvu jne.
# Paneeli saab avada ja sulgeda nupuga "MENU"
# Põhiprogramm (focuspet.py) ei pea teadma, kuidas see töötab. Ta lihtsalt kasutab seda klassi

from typing import List, Callable, Optional
import tkinter as tk
from tkinter import ttk

class SideMenu:
    """
    See klass loob külgmenüü
    Kuidas see töötab:
    - Kui paneel on kinni, siis on ainult kitsas riba tekstiga MENU
    - Kui kasutaja vajutab MENU, siis paneel libiseb lahti ja näitab seadeid
    - Paneel annab peaprogrammile tagasi mõned olulised elemendid, et neid saaks mujal kasutada

    Paneel ei otsusta midagi ise, ta lihtsalt näitab valikuid
    """

    def __init__(
        self,
        parent: tk.Widget,                                        # Parent on põhiaken peaprogrammist
        assets_path,                                             
        focus_choices: List[float],                               # Võimalikud fookusaja valikud
        sessions_choices: List[int],                              # Sessioonide valikud
        break_choices: List[float],                               # Pausi valikud
        initial_points: float,                                    # Esialgne punktide arv
        on_update_scene: Optional[Callable[[], None]] = None,     # Funktsioon põhipildile värskendamiseks
        on_music_change: Optional[Callable[[bool], None]] = None  # Callback muusika ON/OFF jaoks
    ) -> None:

        # Salvestame parent ja update funktsiooni
        self.parent = parent
        self.on_update_scene = on_update_scene                    # kutsume välja pärast menüü avamist/sulgemist
        # Salvestame ka muusika callbacki
        self.on_music_change = on_music_change

        # Kui paneel on kinni, siis tema laius on väga väike
        self.closed_width = 40
        # Kui paneel avatakse, siis muutub laius suureks
        self.open_width = 320

        # Me hoiame siin muutujat, mis ütleb, kas paneel on avatud või mitte
        self.is_open = False

        # Loome peamise raami (paneeli), mis on ekraani vasakul
        # bg = taustavärv
        self.frame = tk.Frame(parent, bg="#D2CDC2")

        # place() paneb selle täpselt vasakule serva
        # width=self.closed_width tähendab, et paneel algab väikese ribana
        self.frame.place(x=0, y=0, relheight=1.0, width=self.closed_width)

        # ----- ttk stiilide loomine -----
        # ttk.Style võimaldab meil muuta kõiki Label'eid ja Comboboxe korraga, et menüü näeks ilus välja
        style = ttk.Style()

        # Stiil siltidele ("Focus", "Break", "Points")
        style.configure(
            "Menu.TLabel",
            background="#D2CDC2",                      # sama värv kui paneeli taust
            foreground="#000000",                      # must tekst
            font=("Bernoru SemiCondensed", 14),          # valitud font
        )

        # Stiil comboboxidele (valikukastid)
        style.configure(
            "Menu.TCombobox",
            fieldbackground="#FFFFFF",                 # valge taust
            background="#FFFFFF",
            foreground="#000000",
            padding=4,
            font=("Bernoru SemiCondensed", 12),
        )

        # Stiil comboboxide eri olekutele (mitteaktiivne, aktiivne)
        style.map(
            "Menu.TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            foreground=[
                ("disabled", "#777777"),               # kui valik on keelatud
                ("!disabled", "#000000"),              # kui valik on lubatud
            ],
        )

        # ----- MENU nupp -----
        # See nupp on kogu aeg nähtav. Vajutades paneel avaneb/sulgub
        self.toggle_btn = tk.Button(
            self.frame,
            text="MENU",                                 # nupu tekst
            font=("Bernoru SemiCondensed", 10, "bold"),
            bg="#D2CDC2",                              # taust sama tooniga kui paneel
            fg="#000000",
            bd=0,                                        # ilma piirjoonteta
            relief="flat",
            command=self.toggle,                         # käsk avada/sulgeda
        )

        # Paigutame nupu paneeli ülemisse serva
        self.toggle_btn.place(relx=0.5, rely=0.02, anchor="n")

        # ----- SISEMINE PANEEL -----
        # Siia tulevad kõik seaded (comboboxid ja sildid)
        self.inner = tk.Frame(self.frame, bg="#D2CDC2")
        # Alguses inner ei ole nähtav. Näitame ainult siis, kui kasutaja avab paneeli

        # ----- Loome kõik valikud, mis ilmuvad menüüs -----

        # ----- FOCUS (min) -----
        ttk.Label(
            self.inner,
            text="Focus (min)",
            style="Menu.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.focus_cb = ttk.Combobox(
            self.inner,
            width=6,
            state="readonly",                            # kasutaja ei saa suvalist teksti sisestada
            values=[str(x) for x in focus_choices],
            style="Menu.TCombobox",
        )
        self.focus_cb.set(str(focus_choices[0]))         # vaikimisi võtab esimese väärtuse
        self.focus_cb.grid(row=1, column=0, sticky="w", pady=(0, 10))

        # ----- SESSIONS -----
        ttk.Label(
            self.inner,
            text="Sessions",
            style="Menu.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))

        self.sessions_cb = ttk.Combobox(
            self.inner,
            width=6,
            state="readonly",
            values=[str(x) for x in sessions_choices],
            style="Menu.TCombobox",
        )
        self.sessions_cb.set(str(sessions_choices[0]))
        self.sessions_cb.grid(row=3, column=0, sticky="w", pady=(0, 10))

        # ----- BREAK (min) -----
        ttk.Label(
            self.inner,
            text="Break (min)",
            style="Menu.TLabel",
        ).grid(row=4, column=0, sticky="w", pady=(0, 2))

        self.break_cb = ttk.Combobox(
            self.inner,
            width=6,
            state="readonly",
            values=[str(x) for x in break_choices],
            style="Menu.TCombobox",
        )
        self.break_cb.set(str(break_choices[0]))
        self.break_cb.grid(row=5, column=0, sticky="w", pady=(0, 14))

        # ----- POINTS (näitab kasutaja teenitud punkte) -----
        self.points_label = ttk.Label(
            self.inner,
            text=f"Points: {initial_points:.1f}",
            style="Menu.TLabel",
        )
        self.points_label.grid(row=6, column=0, sticky="w", pady=(0, 8))

        # ----- STATUS (näitab sõnumit: "Ready to start", "Session done!") -----
        self.status_label = ttk.Label(
            self.inner,
            text="Ready to start",
            foreground="#2e7d32",               # roheline tekst, kui kõik OK
            wraplength=260,                       # tekst murdub paneeli sees
            justify="left",
            style="Menu.TLabel",
        )
        self.status_label.grid(row=7, column=0, sticky="w")

        # ----- MUUSIKA BLOKK -----
        # Siin teeme samas stiilis väikse "Music" teksti ja all valiku ON/OFF
        ttk.Label(
            self.inner,
            text="Music",
            style="Menu.TLabel",
        ).grid(row=8, column=0, sticky="w", pady=(12, 2))

        # StringVar hoiab praegust väärtust ("on" või "off")
        # vaikimisi paneme "off", et muusika ei hakkaks ise mängima
        self.music_var = tk.StringVar(value="off")

        # Väike combobox, mis näeb välja sarnane teistele valikutele
        self.music_cb = ttk.Combobox(
            self.inner,
            width=6,
            state="readonly",
            values=["on", "off"],
            textvariable=self.music_var,
            style="Menu.TCombobox",
        )
        self.music_cb.grid(row=9, column=0, sticky="w", pady=(0, 10))
        self.music_cb.set("off")  # igaks juhuks paneme veel korra

        # Kui kasutaja muudab ON/OFF, siis käivitame sisemise funktsiooni, mis teavitab põhiprogrammi (kui callback on antud)
        self.music_cb.bind("<<ComboboxSelected>>", self._handle_music_change)

    # ----- MUUSIKA VALIKU KÄITLUS -----
    def _handle_music_change(self, _event=None) -> None:
        """
        See funktsioon käivitub siis, kui kasutaja valib comboboxist "on" või "off". Siin anname
        info edasi peaprogrammile, kui on_music_change callback on olemas.
        """
        value = self.music_var.get().lower()   # "on" või "off"
        is_on = value == "on"                  # True kui "on", muidu False

        # Kui peaprogramm andis meile funktsiooni, kutsume seda
        if self.on_music_change is not None:
            self.on_music_change(is_on)

    # ----- PANEELI AVAMINE / SULGEMINE -----

    def toggle(self) -> None:
        """
        Kui kasutaja vajutab MENU, siis see funktsioon kas avab paneeli või sulgeb.
        Lihtne loogika:
        - kui praegu on avatud -> sulgeme
        - kui praegu on suletud -> avame

        """

        if self.is_open:
            # ----- SULGEME PANEELI -----
            self.is_open = False
            self.inner.place_forget()             # peidame sisu ära
            self.frame.place_configure(width=self.closed_width)

        else:
            # ----- AVAME PANEELI -----
            self.is_open = True
            self.frame.place_configure(width=self.open_width)

            # Paigutame sisu nähtavale (natuke paremale)
            self.inner.place(x=10, y=40)

        # Kui põhiprogramm tahab midagi ümber joonistada (nt pilti värskendada), siis kutsume vastava funktsiooni välja
        if self.on_update_scene is not None:
            self.on_update_scene()
