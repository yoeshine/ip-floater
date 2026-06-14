import socket
import json
import urllib.request
import threading
import tkinter as tk
from tkinter import font
from datetime import datetime

API_FIELDS = 'status,message,country,regionName,city,isp,org,as,query,hosting,proxy,timezone,offset'


def get_geo_info():
    for url in [
        f'http://ip-api.com/json/?lang=zh-CN&fields={API_FIELDS}',
        f'http://ip-api.com/json/?lang=en&fields={API_FIELDS}',
    ]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            continue
    return None


def classify_ip_type(data):
    if not data:
        return '未知'

    hosting = data.get('hosting', False)
    proxy = data.get('proxy', False)
    org = (data.get('org', '') or '').lower()
    isp = (data.get('isp', '') or '').lower()
    as_name = (data.get('as', '') or '').lower()

    combined = f'{org} {isp} {as_name}'

    vpn_keywords = ['vpn', 'proxy', 'tor', 'relay', 'v2ray', 'xray', 'shadowsocks',
                    'trojan', 'hysteria', 'tunnel', '翻墙', '机场']
    for kw in vpn_keywords:
        if kw in combined:
            return '代理/VPN 节点'

    if proxy:
        return '代理/VPN 节点'

    cloud_keywords = ['amazon', 'aws', 'google', 'microsoft', 'azure', 'alibaba',
                      'aliyun', 'tencent', 'huawei', 'digitalocean', 'vultr',
                      'linode', 'oracle cloud', 'cloudflare', 'cdn',
                      'compute', 'cloud', 'server', 'hosting', 'idc', '机房租用']
    for kw in cloud_keywords:
        if kw in combined:
            return 'IDC / 数据中心'

    if hosting:
        return 'IDC / 数据中心'

    enterprise_keywords = ['enterprise', 'business', 'corporate', 'dedicated',
                           '专线', '企业', '集团']
    for kw in enterprise_keywords:
        if kw in combined:
            return '企业专线 / 商业宽带'

    residential_keywords = ['telecom', 'unicom', 'mobile', 'china telecom',
                            '中国电信', '中国联通', '中国移动', 'broadband',
                            'cable', 'dsl', 'ftth', 'fiber', 'residential',
                            'chinanet', '宽带', '电信', '联通', '移动']
    for kw in residential_keywords:
        if kw in combined:
            return '家庭宽带'

    return '家庭宽带 / 普通网络'


def get_computer_name():
    return socket.gethostname()


def get_timezone_info():
    now = datetime.now().astimezone()
    tz = now.tzinfo
    if tz is None:
        return '未知', '', None
    tz_name = str(tz)
    offset = now.utcoffset()
    if offset is not None:
        hours = offset.total_seconds() / 3600
        tz_offset = f'UTC{hours:+.0f}'
    else:
        tz_offset = ''
    return tz_name, tz_offset, offset


class FloatingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('IP Info')
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.88)

        bg_color = '#1e1e2e'
        fg_color = '#cdd6f4'
        accent = '#89b4fa'
        green = '#a6e3a1'
        yellow = '#f9e2af'
        red = '#f38ba8'

        self.root.configure(bg=bg_color)

        title_font = font.Font(family='Microsoft YaHei UI', size=8, weight='bold')
        label_font = font.Font(family='Microsoft YaHei UI', size=8)

        self.title_bar = tk.Frame(self.root, bg='#313244', height=24)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        self.title_label = tk.Label(
            self.title_bar, text='  IP 信息',
            bg='#313244', fg=fg_color, font=title_font, anchor='w'
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        close_btn = tk.Label(
            self.title_bar, text=' ✕ ', bg='#313244', fg=fg_color,
            font=label_font, cursor='hand2'
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self.root.destroy())

        refresh_btn = tk.Label(
            self.title_bar, text=' ↻ ', bg='#313244', fg=fg_color,
            font=label_font, cursor='hand2'
        )
        refresh_btn.pack(side=tk.RIGHT)
        refresh_btn.bind('<Button-1>', lambda e: self.refresh_network_info())

        min_btn = tk.Label(
            self.title_bar, text=' ─ ', bg='#313244', fg=fg_color,
            font=label_font, cursor='hand2'
        )
        min_btn.pack(side=tk.RIGHT)
        min_btn.bind('<Button-1>', lambda e: self.toggle_content())

        self.content_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=6)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.rows = []

        self.create_info_row('公网 IP', '查询中...', accent)
        self.create_info_row('所在地', '查询中...', accent)
        self.create_info_row('IP 类型', '分析中...', accent)
        self.create_info_row('运营商', '查询中...', accent)
        self.create_info_row('计算机名', '加载中...', accent)
        self.create_info_row('时区', '加载中...', accent)
        self.create_info_row('时区一致性', '等待数据...', accent)
        self.create_info_row('当前时间', '加载中...', accent)

        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<ButtonRelease-1>', self.stop_move)
        self.title_bar.bind('<B1-Motion>', self.do_move)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<ButtonRelease-1>', self.stop_move)
        self.title_label.bind('<B1-Motion>', self.do_move)

        self.x = 0
        self.y = 0
        self.content_visible = True
        self.colors = {'accent': accent, 'green': green, 'yellow': yellow, 'red': red}

        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f'+{screen_width - 280}+80')

        self.update_static_info()
        self.refresh_time()
        self.refresh_network_info()

    def create_info_row(self, label_text, value_text, color):
        row_frame = tk.Frame(self.content_frame, bg='#1e1e2e')
        row_frame.pack(fill=tk.X, pady=1)

        key_label = tk.Label(
            row_frame, text=label_text, bg='#1e1e2e',
            fg='#6c7086', font=font.Font(family='Microsoft YaHei UI', size=8),
            anchor='w', width=8
        )
        key_label.pack(side=tk.LEFT)

        val_label = tk.Label(
            row_frame, text=value_text, bg='#1e1e2e',
            fg=color, font=font.Font(family='Microsoft YaHei UI', size=8),
            anchor='w'
        )
        val_label.pack(side=tk.LEFT, padx=(6, 0))

        self.rows.append(val_label)

    def update_static_info(self):
        self.rows[4].config(text=get_computer_name())
        tz_name, tz_offset, offset = get_timezone_info()
        self.rows[5].config(text=f'{tz_name} ({tz_offset})')

    def refresh_time(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.rows[7].config(text=now)
        self.root.after(1000, self.refresh_time)

    def refresh_network_info(self):
        def fetch():
            geo_data = get_geo_info()
            self.root.after(0, lambda: self.apply_geo(geo_data))

        t = threading.Thread(target=fetch, daemon=True)
        t.start()
        self.root.after(300000, self.refresh_network_info)

    def apply_geo(self, data):
        if data and data.get('status') == 'success':
            location = f'{data.get("country", "")} {data.get("regionName", "")} {data.get("city", "")}'.strip()
            isp = data.get('isp', '') or data.get('org', '') or '未知'
            ip_type = classify_ip_type(data)

            if data.get('query'):
                self.rows[0].config(text=data['query'])

            self.rows[1].config(text=location or '未知')

            type_color = self.colors['accent']
            if 'IDC' in ip_type or '数据中心' in ip_type:
                type_color = self.colors['yellow']
            elif '代理' in ip_type or 'VPN' in ip_type:
                type_color = self.colors['red']
            elif '家庭' in ip_type:
                type_color = self.colors['green']
            self.rows[2].config(text=ip_type, fg=type_color)

            self.rows[3].config(text=isp)

            ip_tz_name = data.get('timezone', '')
            ip_offset_sec = data.get('offset')
            self._check_tz_match(ip_tz_name, ip_offset_sec)
        else:
            self.rows[0].config(text='获取失败')
            self.rows[1].config(text='获取失败')
            self.rows[2].config(text='获取失败')
            self.rows[3].config(text='获取失败')
            self.rows[6].config(text='无法判断', fg=self.colors['accent'])

    def _check_tz_match(self, ip_tz_name, ip_offset_sec):
        _, _, local_offset = get_timezone_info()

        if local_offset is None or not ip_tz_name or ip_offset_sec is None:
            self.rows[6].config(text='无法判断', fg=self.colors['accent'])
            return

        local_hours = int(local_offset.total_seconds() / 3600)
        ip_hours = int(ip_offset_sec / 3600)

        if local_hours == ip_hours:
            self.rows[6].config(text=f'一致 ({ip_tz_name})', fg=self.colors['green'])
        else:
            self.rows[6].config(
                text=f'不一致 → {ip_tz_name} (UTC{ip_hours:+d})',
                fg=self.colors['red']
            )

    def toggle_content(self):
        if self.content_visible:
            self.content_frame.pack_forget()
            self.root.geometry('')
        else:
            self.content_frame.pack(fill=tk.BOTH, expand=True)
        self.content_visible = not self.content_visible

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = 0
        self.y = 0

    def do_move(self, event):
        dx = event.x_root - self.x
        dy = event.y_root - self.y
        self.root.geometry(f'+{dx}+{dy}')

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = FloatingWindow()
    app.run()
