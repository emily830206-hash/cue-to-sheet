import csv
import os
import re
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
import webbrowser


CATEGORY_ORDER = [
    ("MT_首頁_編輯精選", ["MT_首頁_編輯精選"]),
    ("MT_熱門文章下_文字連結", ["MT_熱門文章下_文字連結"]),
    ("MT_分頻道_文末延伸閱讀_文字廣告2", ["MT_分頻道_文末延伸閱讀_文字廣告2"]),
    ("MT_AABAR", ["AABAR"]),
    ("MT_每日學管理電子報_選文", ["MT_每日學管理電子報_選文"]),
    ("MT_瀑布流", ["MT_瀑布流"]),
    ("MT_Facebook PO文", ["MT_Facebook PO文"]),
]


@dataclass
class CueRow:
    original_index: int
    placement: str
    channel: str
    start: str
    end: str
    sheet_placement: str
    period: str
    category_index: int


def clean_text(value):
    return (value or "").strip()


def mmdd(date_text):
    text = clean_text(date_text)
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        return f"{int(match.group(2)):02d}{int(match.group(3)):02d}"
    match = re.search(r"(\d{1,2})[-/](\d{1,2})", text)
    if match:
        return f"{int(match.group(1)):02d}{int(match.group(2)):02d}"
    return text


def date_sort_key(date_text):
    text = clean_text(date_text)
    match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = re.search(r"(\d{1,2})[-/](\d{1,2})", text)
    if match:
        return (9999, int(match.group(1)), int(match.group(2)))
    return (9999, 99, 99)


def category_index(placement):
    for index, (_, keywords) in enumerate(CATEGORY_ORDER):
        if any(keyword in placement for keyword in keywords):
            return index
    return len(CATEGORY_ORDER)


def sheet_placement_name(placement, channel):
    if channel:
        return f"{placement} - {channel}"
    return placement


def load_cue_rows(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["版位", "走期(開始)", "走期(結束)"]
        missing = [name for name in required if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CSV 缺少欄位：" + "、".join(missing))

        for index, row in enumerate(reader, start=1):
            placement = clean_text(row.get("版位"))
            if not placement:
                continue
            channel = clean_text(row.get("頻道"))
            start = clean_text(row.get("走期(開始)"))
            end = clean_text(row.get("走期(結束)"))
            rows.append(
                CueRow(
                    original_index=index,
                    placement=placement,
                    channel=channel,
                    start=start,
                    end=end,
                    sheet_placement=sheet_placement_name(placement, channel),
                    period=f"{mmdd(start)}-{mmdd(end)}",
                    category_index=category_index(placement),
                )
            )

    rows.sort(key=lambda item: (item.category_index, date_sort_key(item.start), item.original_index))
    return rows


def rows_to_tsv(rows):
    placements = "\t".join(row.sheet_placement for row in rows)
    periods = "\t".join(row.period for row in rows)
    return placements + "\n" + periods


def normalize_sheet_url(url):
    url = clean_text(url)
    match = re.search(r"/(?:spreadsheets/d|file/d)/([A-Za-z0-9_-]+)", url)
    if match:
        sheet_id = match.group(1)
        gid_match = re.search(r"[?#&]gid=(\d+)", url)
        gid_part = f"?gid={gid_match.group(1)}" if gid_match else ""
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit{gid_part}"
    return url


class CueToSheetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cue CSV 貼入 Google Sheet 小工具")
        self.geometry("980x640")
        self.minsize(860, 520)
        self.rows = []

        self.csv_path = tk.StringVar()
        self.sheet_url = tk.StringVar()
        self.start_cell = tk.StringVar(value="B9")
        self.status = tk.StringVar(value="請先選擇 cue CSV。")

        self.build_ui()

    def build_ui(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        source = ttk.LabelFrame(outer, text="資料來源")
        source.pack(fill="x")

        ttk.Label(source, text="Cue CSV").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(source, textvariable=self.csv_path).grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        ttk.Button(source, text="選擇檔案", command=self.choose_csv).grid(row=0, column=2, padx=8, pady=8)

        ttk.Label(source, text="Google Sheet URL").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(source, textvariable=self.sheet_url).grid(row=1, column=1, sticky="ew", padx=8, pady=8)
        ttk.Button(source, text="開啟 Sheet", command=self.open_sheet).grid(row=1, column=2, padx=8, pady=8)

        ttk.Label(source, text="貼上起始格").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(source, textvariable=self.start_cell, width=10).grid(row=2, column=1, sticky="w", padx=8, pady=8)
        source.columnconfigure(1, weight=1)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(12, 8))
        ttk.Button(actions, text="讀取並預覽", command=self.load_preview).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="複製可貼資料", command=self.copy_tsv).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="複製並開啟 Sheet", command=self.copy_and_open).pack(side="left")

        note = (
            "使用方式：讀取 CSV 後按「複製可貼資料」，到 Google Sheet 點選起始格（例如 B9），"
            "按 Ctrl+Shift+V / 只貼上值。這樣會保留原本的底色、格線、字體大小與公式。"
        )
        ttk.Label(outer, text=note, foreground="#555").pack(fill="x", pady=(0, 8))

        preview_frame = ttk.LabelFrame(outer, text="預覽：會貼到 Google Sheet 的順序")
        preview_frame.pack(fill="both", expand=True)

        columns = ("order", "category", "placement", "period")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=14)
        self.tree.heading("order", text="#")
        self.tree.heading("category", text="類型")
        self.tree.heading("placement", text="版位（含頻道）")
        self.tree.heading("period", text="宣傳走期")
        self.tree.column("order", width=50, anchor="center")
        self.tree.column("category", width=180)
        self.tree.column("placement", width=560)
        self.tree.column("period", width=130, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(outer, textvariable=self.status, anchor="w")
        status.pack(fill="x", pady=(8, 0))

    def choose_csv(self):
        path = filedialog.askopenfilename(
            title="選擇 cue CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_path.set(path)
            self.load_preview()

    def load_preview(self):
        path = self.csv_path.get().strip()
        if not path:
            messagebox.showwarning("尚未選擇檔案", "請先選擇 cue CSV。")
            return
        if not os.path.exists(path):
            messagebox.showerror("找不到檔案", path)
            return

        try:
            self.rows = load_cue_rows(path)
        except Exception as exc:
            messagebox.showerror("讀取失敗", str(exc))
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        category_labels = [name for name, _ in CATEGORY_ORDER] + ["其他"]
        for index, row in enumerate(self.rows, start=1):
            label = category_labels[row.category_index] if row.category_index < len(category_labels) else "其他"
            self.tree.insert("", "end", values=(index, label, row.sheet_placement, row.period))

        cell = self.start_cell.get().strip() or "B9"
        self.status.set(f"已讀取 {len(self.rows)} 筆，會產生 {len(self.rows)} 欄。請到 Google Sheet {cell} 使用 Ctrl+Shift+V 只貼值。")

    def copy_tsv(self):
        if not self.rows:
            self.load_preview()
            if not self.rows:
                return
        tsv = rows_to_tsv(self.rows)
        self.clipboard_clear()
        self.clipboard_append(tsv)
        self.update()
        self.status.set(f"已複製兩列、{len(self.rows)} 欄資料。請到 Google Sheet 點選起始格，按 Ctrl+Shift+V 只貼上值。")
        messagebox.showinfo(
            "已複製",
            f"資料已複製到剪貼簿，共 {len(self.rows)} 欄。\n\n到 Google Sheet 點選起始格後，請按 Ctrl+Shift+V，只貼上值以保留原本格式。",
        )

    def open_sheet(self):
        url = normalize_sheet_url(self.sheet_url.get())
        if not url:
            messagebox.showwarning("尚未填 URL", "請貼上 Google Sheet URL。")
            return
        self.sheet_url.set(url)
        webbrowser.open(url)

    def copy_and_open(self):
        self.copy_tsv()
        if self.sheet_url.get().strip():
            self.open_sheet()


if __name__ == "__main__":
    app = CueToSheetApp()
    app.mainloop()
