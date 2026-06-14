import json
import urllib.request
import threading
import socket
import os
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.text import LabelBase

API_FIELDS = 'status,message,country,regionName,city,isp,org,as,query,hosting,proxy,timezone,offset'

# ===================== font setup =====================

def _setup_cjk_font():
    """Try Android system fonts first (no bundled font needed)."""
    if platform == 'android':
        candidates = [
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/DroidSansFallback.ttf',
            '/system/fonts/NotoSansSC-Regular.otf',
            '/system/fonts/NotoSansMonoCJKsc-Regular.otf',
            '/system/fonts/FZLanTingHeiS-R-GB.ttf',
            '/system/fonts/Miui-Regular.ttf',
            '/data/data/org.test.ipfloater/files/app/font_sc.ttf',
        ]
        for fp in candidates:
            if os.path.exists(fp):
                LabelBase.register(name='CJK', fn_regular=fp)
                return 'CJK'
    # Desktop: look for a bundled font file
    for fname in ('NotoSansSC_small.ttf', 'font_sc.ttf', 'NotoSansSC.ttf'):
        bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
        if os.path.exists(bundled):
            LabelBase.register(name='CJK', fn_regular=bundled)
            return 'CJK'
    return None

FONT_NAME = _setup_cjk_font()

# ===================== network / data helpers =====================

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

    vpn_kw = ['vpn', 'proxy', 'tor', 'relay', 'v2ray', 'xray', 'shadowsocks',
              'trojan', 'hysteria', 'tunnel', '翻墙', '机场']
    for kw in vpn_kw:
        if kw in combined:
            return '代理/VPN 节点'
    if proxy:
        return '代理/VPN 节点'

    cloud_kw = ['amazon', 'aws', 'google', 'microsoft', 'azure', 'alibaba',
                'aliyun', 'tencent', 'huawei', 'digitalocean', 'vultr',
                'linode', 'oracle cloud', 'cloudflare', 'cdn',
                'compute', 'cloud', 'server', 'hosting', 'idc', '机房租用']
    for kw in cloud_kw:
        if kw in combined:
            return 'IDC / 数据中心'
    if hosting:
        return 'IDC / 数据中心'

    enterprise_kw = ['enterprise', 'business', 'corporate', 'dedicated',
                     '专线', '企业', '集团']
    for kw in enterprise_kw:
        if kw in combined:
            return '企业专线 / 商业宽带'

    residential_kw = ['telecom', 'unicom', 'mobile', 'china telecom',
                      '中国电信', '中国联通', '中国移动', 'broadband',
                      'cable', 'dsl', 'ftth', 'fiber', 'residential',
                      'chinanet', '宽带', '电信', '联通', '移动']
    for kw in residential_kw:
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


BG = (0.118, 0.118, 0.180, 1)
BAR_BG = (0.192, 0.196, 0.267, 1)
BTN_BG = (0.157, 0.157, 0.239, 1)
TEXT = (0.804, 0.839, 0.957, 1)
ACCENT = (0.537, 0.706, 0.980, 1)
GREEN = (0.651, 0.890, 0.631, 1)
YELLOW = (0.976, 0.886, 0.686, 1)
RED = (0.953, 0.545, 0.659, 1)
DIM = (0.424, 0.443, 0.529, 1)


def _font(size):
    kw = {'font_size': size}
    if FONT_NAME:
        kw['font_name'] = FONT_NAME
    return kw


class InfoRow(BoxLayout):
    def __init__(self, key_text, val_text='加载中...', val_color=ACCENT, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(42), **kw)
        self.key_label = Label(
            text=key_text,
            color=DIM,
            size_hint_x=0.30,
            halign='right',
            valign='middle',
            **_font(dp(15)),
        )
        self.key_label.bind(size=self.key_label.setter('text_size'))
        self.val_label = Label(
            text=val_text,
            color=val_color,
            size_hint_x=0.70,
            halign='left',
            valign='middle',
            **_font(dp(17)),
        )
        self.val_label.bind(size=self.val_label.setter('text_size'))
        self.add_widget(self.key_label)
        self.add_widget(self.val_label)

    def set_value(self, text, color=None):
        self.val_label.text = text
        if color:
            self.val_label.color = color


class IPFloaterApp(App):
    def build(self):
        self.title = 'IP Info'

        is_android = platform == 'android'
        if is_android:
            Window.fullscreen = 'auto'
        else:
            Window.size = (440, 520)
            Window.topmost = True

        Window.clearcolor = BG

        root = FloatLayout()
        from kivy.graphics import Color, Rectangle
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(self._bg, 'pos', v),
                  size=lambda i, v: setattr(self._bg, 'size', v))

        # --- title bar ---
        bar_h = dp(50)
        title_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=bar_h,
            pos_hint={'top': 1},
        )
        with title_bar.canvas.before:
            Color(*BAR_BG)
            self._bar_bg = Rectangle(pos=title_bar.pos, size=title_bar.size)
        title_bar.bind(pos=lambda i, v: setattr(self._bar_bg, 'pos', v),
                       size=lambda i, v: setattr(self._bar_bg, 'size', v))

        title_lbl = Label(
            text='IP 信息',
            color=TEXT,
            halign='left',
            valign='middle',
            padding=(dp(16), 0),
            size_hint_x=0.6,
            bold=True,
            **_font(dp(18)),
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))

        refresh_icon = Button(
            text='↻',
            color=TEXT,
            size_hint_x=None,
            width=dp(56),
            font_size=dp(26),
            background_normal='',
            background_color=BAR_BG,
        )
        refresh_icon.bind(on_release=lambda _: self.refresh_network())

        title_bar.add_widget(title_lbl)
        title_bar.add_widget(refresh_icon)
        root.add_widget(title_bar)

        # --- info rows ---
        self.content = BoxLayout(
            orientation='vertical',
            pos_hint={'top': 1},
            padding=(dp(16), dp(12), dp(16), dp(12)),
            spacing=dp(2),
            size_hint=(1, None),
        )
        self.content.bind(minimum_height=self.content.setter('height'))

        self.rows = {}
        fields = [
            ('公网 IP', '查询中...'),
            ('所在地', '查询中...'),
            ('IP 类型', '分析中...'),
            ('运营商', '查询中...'),
            ('计算机名', '加载中...'),
            ('时区', '加载中...'),
            ('时区一致性', '等待数据...'),
            ('当前时间', '加载中...'),
        ]
        for key, val in fields:
            row = InfoRow(key, val)
            self.rows[key] = row
            self.content.add_widget(row)

        def reposition(*_):
            self.content.y = title_bar.y - self.content.height
        self.content.bind(height=lambda *_: reposition())
        title_bar.bind(pos=lambda *_: reposition())
        root.add_widget(self.content)

        # --- refresh button ---
        refresh_btn = Button(
            text='刷新网络信息',
            color=TEXT,
            size_hint=(0.9, None),
            height=dp(48),
            pos_hint={'center_x': 0.5, 'y': 0.02},
            **_font(dp(16)),
            background_normal='',
            background_color=BTN_BG,
        )
        refresh_btn.bind(on_release=lambda _: self.refresh_network())
        root.add_widget(refresh_btn)

        self.update_static()
        self.refresh_network()
        Clock.schedule_interval(self.refresh_time, 1)

        return root

    def update_static(self):
        self.rows['计算机名'].set_value(get_computer_name())
        tz_name, tz_offset, _ = get_timezone_info()
        self.rows['时区'].set_value(f'{tz_name} ({tz_offset})')

    def refresh_time(self, dt):
        self.rows['当前时间'].set_value(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def refresh_network(self):
        def fetch():
            data = get_geo_info()
            Clock.schedule_once(lambda dt: self.apply_geo(data), 0)
        threading.Thread(target=fetch, daemon=True).start()

    def apply_geo(self, data):
        if data and data.get('status') == 'success':
            location = f'{data.get("country", "")} {data.get("regionName", "")} {data.get("city", "")}'.strip()
            isp = data.get('isp', '') or data.get('org', '') or '未知'
            ip_type = classify_ip_type(data)

            if data.get('query'):
                self.rows['公网 IP'].set_value(data['query'])
            self.rows['所在地'].set_value(location or '未知')

            if 'IDC' in ip_type or '数据中心' in ip_type:
                tc = YELLOW
            elif '代理' in ip_type or 'VPN' in ip_type:
                tc = RED
            elif '家庭' in ip_type:
                tc = GREEN
            else:
                tc = ACCENT
            self.rows['IP 类型'].set_value(ip_type, tc)
            self.rows['运营商'].set_value(isp)

            ip_tz = data.get('timezone', '')
            ip_offset_sec = data.get('offset')
            self._check_tz(ip_tz, ip_offset_sec)
        else:
            for k in ['公网 IP', '所在地', 'IP 类型', '运营商']:
                self.rows[k].set_value('获取失败')
            self.rows['时区一致性'].set_value('无法判断')

    def _check_tz(self, ip_tz_name, ip_offset_sec):
        _, _, local_offset = get_timezone_info()
        if local_offset is None or not ip_tz_name or ip_offset_sec is None:
            self.rows['时区一致性'].set_value('无法判断')
            return
        local_h = int(local_offset.total_seconds() / 3600)
        ip_h = int(ip_offset_sec / 3600)
        if local_h == ip_h:
            self.rows['时区一致性'].set_value(f'一致 ({ip_tz_name})', GREEN)
        else:
            self.rows['时区一致性'].set_value(
                f'不一致 → {ip_tz_name} (UTC{ip_h:+d})', RED
            )


if __name__ == '__main__':
    IPFloaterApp().run()
