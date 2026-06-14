# -*- coding: utf-8 -*-
import json
import urllib.request
import socket
import threading
import time
import os
from datetime import datetime

from jnius import autoclass

API_FIELDS = 'status,message,country,regionName,city,isp,org,as,query,hosting,proxy,timezone,offset'

# Android classes
WindowManager = autoclass('android.view.WindowManager')
LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
Gravity = autoclass('android.view.Gravity')
Color = autoclass('android.graphics.Color')
View = autoclass('android.view.View')
ViewGroup = autoclass('android.view.ViewGroup')
MotionEvent = autoclass('android.view.MotionEvent')
LinearLayout = autoclass('android.widget.LinearLayout')
TextView = autoclass('android.widget.TextView')
Resources = autoclass('android.content.res.Resources')
Context = autoclass('android.content.Context')
Intent = autoclass('android.content.Intent')
PendingIntent = autoclass('android.app.PendingIntent')
Notification = autoclass('android.app.Notification')
NotificationChannel = autoclass('android.app.NotificationChannel')
NotificationManager = autoclass('android.app.NotificationManager')
Build = autoclass('android.os.Build')
PythonService = autoclass('org.kivy.android.PythonService')
Point = autoclass('android.graphics.Point')

Activity = PythonService.mService

if Build.VERSION.SDK_INT >= 26:
    LAYOUT_TYPE = LayoutParams.TYPE_APPLICATION_OVERLAY
else:
    LAYOUT_TYPE = LayoutParams.TYPE_PHONE


def dp2px(dp):
    return int(dp * Resources.getSystem().getDisplayMetrics().density + 0.5)


# ---- network helpers ----

def get_geo_info():
    for url in [
        'http://ip-api.com/json/?lang=zh-CN&fields=' + API_FIELDS,
        'http://ip-api.com/json/?lang=en&fields=' + API_FIELDS,
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
            return '企业专线'

    residential_kw = ['telecom', 'unicom', 'mobile', 'china telecom',
                      'broadband', 'cable', 'dsl', 'ftth', 'fiber',
                      'residential', 'chinanet',
                      '中国电信', '中国联通', '中国移动', '宽带', '电信', '联通', '移动']
    for kw in residential_kw:
        if kw in combined:
            return '家庭宽带'
    return '家庭宽带'


def get_computer_name():
    return socket.gethostname()


def get_tz_info():
    now = datetime.now().astimezone()
    tz = now.tzinfo
    if tz is None:
        return '未知', '', None
    tz_name = str(tz)
    offset = now.utcoffset()
    if offset is not None:
        hours = offset.total_seconds() / 3600
        tz_offset = 'UTC{0:+.0f}'.format(hours)
    else:
        tz_offset = ''
    return tz_name, tz_offset, offset


# ---- overlay ----

_overlay_wm = None
_overlay_view = None
_overlay_params = None
_val_labels = {}

TEXT_COLOR = 0xFFCDD6F4
ACCENT_COLOR = 0xFF89B4FA
DIM_COLOR = 0xFF6C7086
BG_COLOR = 0xE01E1E2E
BAR_COLOR = 0xFF313244
GREEN_COLOR = 0xFFA6E3A1
YELLOW_COLOR = 0xFFF9E2AF
RED_COLOR = 0xFFF38BA8

LABEL_KEYS = [
    '公网 IP', '所在地', 'IP 类型', '运营商',
    '计算机名', '时区', '时区一致性', '当前时间'
]

_drag_start_x = 0
_drag_start_y = 0
_drag_win_x = 0
_drag_win_y = 0


def create_overlay():
    global _overlay_wm, _overlay_view, _overlay_params

    wm = Activity.getSystemService(Context.WINDOW_SERVICE)

    # root vertical layout
    root = LinearLayout(Activity)
    root.setOrientation(LinearLayout.VERTICAL)
    root.setPadding(dp2px(12), dp2px(6), dp2px(12), dp2px(6))
    root.setBackgroundColor(int(BG_COLOR))

     # title bar (draggable) — horizontal layout
    title_bar = LinearLayout(Activity)
    title_bar.setOrientation(LinearLayout.HORIZONTAL)
    title_bar.setBackgroundColor(int(BAR_COLOR))
    title_bar_lp = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, dp2px(36)
    )

    title = TextView(Activity)
    title.setText('IP 信息')
    title.setTextColor(int(TEXT_COLOR))
    title.setTextSize(14.0)
    title.setPadding(dp2px(6), dp2px(6), 0, dp2px(6))
    title.setGravity(Gravity.CENTER_VERTICAL)
    title_lp2 = LinearLayout.LayoutParams(
        0, ViewGroup.LayoutParams.MATCH_PARENT, 1.0
    )
    title_bar.addView(title, title_lp2)

    refresh_btn = TextView(Activity)
    refresh_btn.setText('↻')
    refresh_btn.setTextColor(int(TEXT_COLOR))
    refresh_btn.setTextSize(18.0)
    refresh_btn.setGravity(Gravity.CENTER)
    refresh_btn.setPadding(dp2px(4), 0, dp2px(8), 0)
    btn_lp = LinearLayout.LayoutParams(dp2px(40), ViewGroup.LayoutParams.MATCH_PARENT)
    title_bar.addView(refresh_btn, btn_lp)

    root.addView(title_bar, title_bar_lp)

    # info rows
    for key in LABEL_KEYS:
        row = LinearLayout(Activity)
        row.setOrientation(LinearLayout.HORIZONTAL)
        row.setPadding(0, dp2px(3), 0, dp2px(3))

        key_tv = TextView(Activity)
        key_tv.setText(key)
        key_tv.setTextColor(int(DIM_COLOR))
        key_tv.setTextSize(12.0)
        kw = dp2px(80)
        key_lp = LinearLayout.LayoutParams(kw, ViewGroup.LayoutParams.WRAP_CONTENT)
        row.addView(key_tv, key_lp)

        val_tv = TextView(Activity)
        val_tv.setText('加载中...')
        val_tv.setTextColor(int(ACCENT_COLOR))
        val_tv.setTextSize(13.0)
        val_lp = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0)
        row.addView(val_tv, val_lp)

        row_lp = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        )
        root.addView(row, row_lp)
        _val_labels[key] = val_tv

    # drag handling on title bar
    class TouchHandler:
        def __init__(self):
            self.sx = 0
            self.sy = 0
            self.wx = 0
            self.wy = 0

        def onTouch(self, view, event):
            action = event.getAction()
            if action == MotionEvent.ACTION_DOWN:
                self.sx = int(event.getRawX())
                self.sy = int(event.getRawY())
                self.wx = _overlay_params.x
                self.wy = _overlay_params.y
                return True
            elif action == MotionEvent.ACTION_MOVE:
                dx = int(event.getRawX()) - self.sx
                dy = int(event.getRawY()) - self.sy
                _overlay_params.x = self.wx + dx
                _overlay_params.y = self.wy + dy
                wm.updateViewLayout(root, _overlay_params)
                return True
            return False

    handler = TouchHandler()
    title_bar.setOnTouchListener(handler)

    # refresh button click
    class RefreshClickHandler:
        def onClick(self, view):
            refresh_data()
    refresh_btn.setOnClickListener(RefreshClickHandler())

    # window layout params
    display = wm.getDefaultDisplay()
    p = Point()
    display.getRealSize(p)

    w = dp2px(270)
    params = LayoutParams(
        w, ViewGroup.LayoutParams.WRAP_CONTENT,
        LAYOUT_TYPE,
        LayoutParams.FLAG_NOT_FOCUSABLE |
        LayoutParams.FLAG_NOT_TOUCH_MODAL |
        LayoutParams.FLAG_LAYOUT_IN_SCREEN,
        -2  # PixelFormat.TRANSLUCENT
    )
    params.gravity = Gravity.TOP | Gravity.LEFT
    params.x = p.x - w - dp2px(12)
    params.y = dp2px(80)

    wm.addView(root, params)
    _overlay_wm = wm
    _overlay_view = root
    _overlay_params = params


def set_label(key, text, color=None):
    if key in _val_labels:
        tv = _val_labels[key]
        tv.setText(str(text))
        if color is not None:
            tv.setTextColor(int(color))


def refresh_data():
    def _do():
        data = get_geo_info()
        if data and data.get('status') == 'success':
            loc = '{} {} {}'.format(
                data.get('country', ''),
                data.get('regionName', ''),
                data.get('city', '')
            ).strip()
            ip_type = classify_ip_type(data)
            isp = data.get('isp', '') or data.get('org', '') or ''

            set_label('公网 IP', data.get('query', ''))
            set_label('所在地', loc or '未知')

            if 'IDC' in ip_type or '数据中心' in ip_type:
                tc = YELLOW_COLOR
            elif '代理' in ip_type or 'VPN' in ip_type:
                tc = RED_COLOR
            elif '家庭' in ip_type:
                tc = GREEN_COLOR
            else:
                tc = ACCENT_COLOR
            set_label('IP 类型', ip_type, tc)
            set_label('运营商', isp)
            set_label('计算机名', get_computer_name())

            tz_name, tz_offset, local_off = get_tz_info()
            set_label('时区', '{} ({})'.format(tz_name, tz_offset))

            ip_tz = data.get('timezone', '')
            ip_off = data.get('offset')
            if local_off is not None and ip_tz and ip_off is not None:
                lh = int(local_off.total_seconds() / 3600)
                ih = int(ip_off / 3600)
                if lh == ih:
                    set_label('时区一致性', '一致 ({})'.format(ip_tz), GREEN_COLOR)
                else:
                    set_label('时区一致性',
                              '不一致 -> {} (UTC{:+d})'.format(ip_tz, ih), RED_COLOR)
        else:
            for k in ['公网 IP', '所在地', 'IP 类型', '运营商']:
                set_label(k, '获取失败')
    threading.Thread(target=_do, daemon=True).start()


def update_time():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    set_label('当前时间', now)


# ---- service lifecycle ----

def start_service():
    # notification channel (API 26+)
    if Build.VERSION.SDK_INT >= 26:
        channel = NotificationChannel(
            'ip_floater', 'IP Floater',
            NotificationManager.IMPORTANCE_LOW
        )
        nm = Activity.getSystemService(Context.NOTIFICATION_SERVICE)
        nm.createNotificationChannel(channel)

    # build notification
    if Build.VERSION.SDK_INT >= 26:
        nb = Notification.Builder(Activity, 'ip_floater')
    else:
        nb = Notification.Builder(Activity)
    nb.setContentTitle('IP Floater')
    nb.setContentText('IP 信息悬浮窗运行中')
    nb.setSmallIcon(Activity.getApplicationInfo().icon)
    nb.setOngoing(True)
    nb.setPriority(Notification.PRIORITY_LOW)
    Activity.startForeground(1, nb.build())

    # create overlay
    create_overlay()
    refresh_data()

    # background loops
    threading.Thread(target=_time_loop, daemon=True).start()
    threading.Thread(target=_refresh_loop, daemon=True).start()


def _time_loop():
    while True:
        update_time()
        time.sleep(1)


def _refresh_loop():
    while True:
        time.sleep(300)
        refresh_data()


if __name__ == '__main__':
    start_service()
