import tkinter as tk
import requests
import json
import time
import threading
from datetime import datetime

# -------------------------- 配置 --------------------------
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 200
UPDATE_INTERVAL = 60
BG_COLOR = "#1f2937"
TEXT_COLOR = "#ffffff"

# 多IP接口（和你最初能跑的一致）
IP_APIS = [
    "https://api.ipify.org?format=json",
    "https://httpbin.org/ip",
    "https://api4.ipify.org?format=json"
]
LOC_API = "https://ipapi.co/{}/json/"

# -------------------------- 获取IP信息 --------------------------
def get_public_ip():
    for url in IP_APIS:
        try:
            r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                d = r.json()
                if "ip" in d:
                    return d["ip"]
                elif "origin" in d:
                    return d["origin"]
        except Exception as e:
            continue
    return None

def get_ip_info():
    info = {
        "public_ip": "获取失败",
        "location": "获取失败",
        "isp": "获取失败",
        "ip_type": "未知类型"
    }
    ip = get_public_ip()
    if not ip:
        return info
    info["public_ip"] = ip

    try:
        r = requests.get(LOC_API.format(ip), timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            d = r.json()
            info["location"] = f"{d.get('country_name','')} {d.get('region','')} {d.get('city','')}".strip()
            info["isp"] = d.get("org", "未知运营商")

            # 判断IP类型
            org = info["isp"].lower()
            if any(k in org for k in ["机房", "数据中心", "cloud", "host", "vps", "proxy", "cdn"]):
                info["ip_type"] = "公共机场/代理/数据中心IP"
            elif any(k in org for k in ["教育", "大学", "edu"]):
                info["ip_type"] = "教育网IP"
            elif any(k in org for k in ["公司", "企业", "集团", "corp"]):
                info["ip_type"] = "企业专线IP"
            else:
                info["ip_type"] = "家庭个人宽带IP"
    except Exception as e:
        pass
    return info

# -------------------------- 浮窗 --------------------------
class FloatingWindow:
    def __init__(self, root):
        self.root = root
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=BG_COLOR)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # 默认右上角
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"+{sw-WINDOW_WIDTH}+0")

        # 拖动
        self.x = 0
        self.y = 0
        self.root.bind("<Button-1>", self.on_click)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<Double-1>", lambda e: self.root.destroy())

        # 右键退出
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="退出程序", command=self.root.destroy)
        self.root.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))

        # 文本
        self.label = tk.Label(
            root, text="加载中...",
            bg=BG_COLOR, fg=TEXT_COLOR,
            justify=tk.LEFT, font=("微软雅黑", 11),
            padx=20, pady=18
        )
        self.label.pack(expand=True, fill=tk.BOTH)

        # 刷新线程
        self.running = True
        self.thread = threading.Thread(target=self.loop_update, daemon=True)
        self.thread.start()

    def on_click(self, e):
        self.x, self.y = e.x, e.y

    def on_drag(self, e):
        self.root.geometry(f"+{self.root.winfo_x()+e.x-self.x}+{self.root.winfo_y()+e.y-self.y}")

    def update_info(self):
        ip_data = get_ip_info()
        tz = datetime.now().astimezone().tzname()
        text = (
            f"公网IP：{ip_data['public_ip']}\n"
            f"所在地：{ip_data['location']}\n"
            f"运营商：{ip_data['isp']}\n"
            f"IP类型：{ip_data['ip_type']}\n"
            f"时    区：{tz}"
        )
        self.label.config(text=text)

    def loop_update(self):
        while self.running:
            self.root.after(0, self.update_info)
            time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = FloatingWindow(root)
    root.mainloop()