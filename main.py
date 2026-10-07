"""Лабораторная работа 1. Цветовые модели: CMYK - RGB - HSV / HLS.

Запуск:  python main.py
Цвет можно задавать тремя способами в каждой модели:
  1) полями ввода (точные значения),
  2) ползунками (плавное изменение),
  3) палитрой (квадрат насыщенность/яркость + полоса оттенка, диалог выбора цвета).
При изменении любой координаты все остальные модели пересчитываются автоматически.
"""
import tkinter as tk
from tkinter import ttk, colorchooser

import colormodels as cm

# модель -> [(имя компоненты, мин, макс, подпись)]
MODELS = {
    "RGB": [("R", 0, 255, "Red (красный)"), ("G", 0, 255, "Green (зелёный)"),
            ("B", 0, 255, "Blue (синий)")],
    "CMYK": [("C", 0, 100, "Cyan (голубой), %"), ("M", 0, 100, "Magenta (пурпурный), %"),
             ("Y", 0, 100, "Yellow (жёлтый), %"), ("K", 0, 100, "Key/Black (чёрный), %")],
    "HSV": [("H", 0, 360, "Hue (оттенок), °"), ("S", 0, 100, "Saturation (насыщенность), %"),
            ("V", 0, 100, "Value (яркость), %")],
    "HLS": [("H", 0, 360, "Hue (оттенок), °"), ("L", 0, 100, "Lightness (светлота), %"),
            ("S", 0, 100, "Saturation (насыщенность), %")],
}
TITLES = {"RGB": "RGB", "CMYK": "CMYK", "HSV": "HSV", "HLS": "HLS"}
TO_RGB = {"RGB": lambda *v: v, "CMYK": cm.cmyk_to_rgb,
          "HSV": cm.hsv_to_rgb, "HLS": cm.hls_to_rgb}

PAL = 200          # размер палитры (пиксели)
EPS = 1e-6


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Цветовые модели: CMYK – RGB – HSV / HLS")
        self.resizable(False, False)
        ttk.Style(self).theme_use("clam")

        self.rgb = [52.0, 152.0, 219.0]   # главное состояние (float 0..255)
        self.hue = 204.0                  # запоминаем оттенок для серых цветов
        self._lock = False
        self._pal_hue = None
        self.scales, self.entries, self.vars = {}, {}, {}

        self.variant = tk.StringVar(value="HSV")
        self._build_ui()
        self.refresh(None, None)

    # ------------------------------------------------------------ интерфейс
    def _build_ui(self):
        pad = dict(padx=8, pady=6)
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="n", **pad)
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="n", **pad)

        # --- предпросмотр и HEX
        self.swatch = tk.Canvas(left, width=PAL + 20, height=60, highlightthickness=1,
                                highlightbackground="#888")
        self.swatch.grid(row=0, column=0, columnspan=2, pady=(0, 6))
        ttk.Label(left, text="HEX:").grid(row=1, column=0, sticky="e")
        self.hex_var = tk.StringVar()
        hex_e = ttk.Entry(left, textvariable=self.hex_var, width=10)
        hex_e.grid(row=1, column=1, sticky="w")
        hex_e.bind("<Return>", self._on_hex)
        hex_e.bind("<FocusOut>", self._on_hex)

        # --- палитра: квадрат S/V + полоса H
        self.sv = tk.Canvas(left, width=PAL, height=PAL, cursor="crosshair",
                            highlightthickness=1, highlightbackground="#888")
        self.sv.grid(row=2, column=0, columnspan=2, pady=(10, 4))
        self.sv_img = tk.PhotoImage(width=PAL, height=PAL)
        self.sv.create_image(0, 0, image=self.sv_img, anchor="nw")
        self.sv_mark = self.sv.create_oval(0, 0, 0, 0, outline="white", width=2)
        self.sv.bind("<Button-1>", self._on_sv)
        self.sv.bind("<B1-Motion>", self._on_sv)

        self.hbar = tk.Canvas(left, width=PAL, height=20, cursor="sb_h_double_arrow",
                              highlightthickness=1, highlightbackground="#888")
        self.hbar.grid(row=3, column=0, columnspan=2, pady=4)
        for x in range(PAL):
            self.hbar.create_line(x, 0, x, 20,
                                  fill=cm.rgb_to_hex(*cm.hsv_to_rgb(x / PAL * 360, 100, 100)))
        self.h_mark = self.hbar.create_rectangle(0, 0, 4, 20, outline="black", width=2)
        self.hbar.bind("<Button-1>", self._on_hbar)
        self.hbar.bind("<B1-Motion>", self._on_hbar)

        ttk.Button(left, text="Выбрать цвет…", command=self._dialog).grid(
            row=4, column=0, columnspan=2, pady=(8, 0), sticky="ew")

        # --- переключатель варианта
        vf = ttk.LabelFrame(right, text="Вариант")
        vf.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Radiobutton(vf, text="Чётный: CMYK – RGB – HSV", value="HSV",
                        variable=self.variant, command=self._switch).grid(sticky="w", padx=6)
        ttk.Radiobutton(vf, text="Нечётный: CMYK – RGB – HLS", value="HLS",
                        variable=self.variant, command=self._switch).grid(sticky="w", padx=6)

        # --- панели моделей
        self.frames = {}
        for i, name in enumerate(("RGB", "CMYK", "HSV", "HLS")):
            fr = ttk.LabelFrame(right, text=TITLES[name])
            fr.grid(row=1 + i, column=0, sticky="ew", pady=3)
            self.frames[name] = fr
            self._build_model(fr, name)
        self._switch()

    def _build_model(self, parent, model):
        for i, (comp, lo, hi, label) in enumerate(MODELS[model]):
            ttk.Label(parent, text=label, width=28).grid(row=i, column=0, sticky="w", padx=4)
            sc = ttk.Scale(parent, from_=lo, to=hi, length=170, orient="horizontal",
                           command=lambda _v, m=model: self._on_scale(m))
            sc.grid(row=i, column=1, padx=4, pady=2)
            var = tk.StringVar()
            en = ttk.Entry(parent, textvariable=var, width=7, justify="right")
            en.grid(row=i, column=2, padx=4)
            en.bind("<KeyRelease>", lambda _e, m=model: self._on_entry(m, final=False))
            en.bind("<Return>", lambda _e, m=model: self._on_entry(m, final=True))
            en.bind("<FocusOut>", lambda _e, m=model: self._on_entry(m, final=True))
            self.scales[(model, i)], self.entries[(model, i)], self.vars[(model, i)] = sc, en, var

    def _switch(self):
        """Показываем HSV или HLS в зависимости от варианта."""
        show = self.variant.get()
        other = "HLS" if show == "HSV" else "HSV"
        self.frames[show].grid()
        self.frames[other].grid_remove()

    # ------------------------------------------------------------ события
    def _read(self, model, final):
        """Читает значения модели из полей ввода; None, если текст некорректен."""
        vals = []
        for i, (_c, lo, hi, _l) in enumerate(MODELS[model]):
            try:
                v = float(self.vars[(model, i)].get().replace(",", "."))
            except ValueError:
                return None
            vals.append(cm.clamp(v, lo, hi))
        return vals

    def _on_entry(self, model, final):
        if self._lock:
            return
        vals = self._read(model, final)
        if vals is None:
            if final:
                self.refresh(None, None)    # вернуть последнее корректное значение
            return
        self.set_from(model, vals, model, "final" if final else "entry")

    def _on_scale(self, model):
        if self._lock:
            return
        vals = [float(self.scales[(model, i)].get()) for i in range(len(MODELS[model]))]
        self.set_from(model, vals, model, "scale")

    def _on_hex(self, _e=None):
        if self._lock:
            return
        try:
            self.rgb = list(cm.hex_to_rgb(self.hex_var.get()))
        except ValueError:
            pass
        self.refresh("HEX", None)

    def _on_sv(self, e):
        s = cm.clamp(e.x / (PAL - 1), 0, 1) * 100
        v = (1 - cm.clamp(e.y / (PAL - 1), 0, 1)) * 100
        self.set_from("HSV", [self.hue, s, v], "PAL", None)

    def _on_hbar(self, e):
        h = cm.clamp(e.x / (PAL - 1), 0, 1) * 359.99
        _h, s, v = cm.rgb_to_hsv(*self.rgb)
        self.set_from("HSV", [h, s, v], "PAL", None)

    def _dialog(self):
        res = colorchooser.askcolor(color=cm.rgb_to_hex(*self.rgb), parent=self,
                                    title="Выбор цвета")
        if res and res[0]:
            self.rgb = [float(x) for x in res[0]]
            self.refresh("DLG", None)

    # ------------------------------------------------------------ ядро
    def set_from(self, model, vals, source, kind):
        """Задан цвет в модели model -> пересчитываем RGB и обновляем остальное."""
        if model in ("HSV", "HLS"):
            self.hue = vals[0]
        r, g, b = TO_RGB[model](*vals)
        self.rgb = [cm.clamp(r, 0, 255), cm.clamp(g, 0, 255), cm.clamp(b, 0, 255)]
        self.refresh(source, kind)

    def refresh(self, source, kind):
        """Обновляет все виджеты. Модель-источник: при вводе текста не трогаем поля
        (чтобы не мешать печатать), при движении ползунка не трогаем ползунки."""
        r, g, b = self.rgb
        hsv = list(cm.rgb_to_hsv(r, g, b))
        if hsv[1] < EPS or hsv[2] < EPS:
            hsv[0] = self.hue                      # оттенок серого не определён
        else:
            self.hue = hsv[0]
        hls = list(cm.rgb_to_hls(r, g, b))
        if hls[2] < EPS or hls[1] < EPS or hls[1] > 100 - EPS:
            hls[0] = self.hue
        values = {"RGB": [r, g, b], "CMYK": list(cm.rgb_to_cmyk(r, g, b)),
                  "HSV": hsv, "HLS": hls}

        self._lock = True
        try:
            for model, vals in values.items():
                for i, v in enumerate(vals):
                    skip_scale = (model == source and kind == "scale")
                    skip_entry = (model == source and kind == "entry")
                    if not skip_scale:
                        self.scales[(model, i)].set(v)
                    if not skip_entry:
                        txt = "%d" % round(v) if model == "RGB" else "%.1f" % v
                        self.vars[(model, i)].set(txt)
            hx = cm.rgb_to_hex(r, g, b)
            self.hex_var.set(hx)
            self.swatch.configure(bg=hx)
            self._draw_palette(hsv)
        finally:
            self._lock = False

    def _draw_palette(self, hsv):
        h, s, v = hsv
        if self._pal_hue is None or abs(self._pal_hue - h) > 0.5:
            self._pal_hue = h
            for y in range(PAL):
                val = (1 - y / (PAL - 1)) * 100
                row = " ".join(cm.rgb_to_hex(*cm.hsv_to_rgb(h, x / (PAL - 1) * 100, val))
                               for x in range(PAL))
                self.sv_img.put("{%s}" % row, to=(0, y))
        x = s / 100 * (PAL - 1)
        y = (1 - v / 100) * (PAL - 1)
        self.sv.coords(self.sv_mark, x - 6, y - 6, x + 6, y + 6)
        hx = h / 360 * (PAL - 1)
        self.hbar.coords(self.h_mark, hx - 2, 0, hx + 2, 20)


if __name__ == "__main__":
    App().mainloop()