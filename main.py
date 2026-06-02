"""
Smart Lab Management System — CLIENT 2 (Mahasiswa / Android)
=============================================================
Protokol  : TCP Raw Socket ke server port 9000
Framework : Kivy 2.3
Storage   : profile.json (lokal) + history.json (lokal)
Auth      : JWT (diterima dari server saat REGISTER)
"""

import socket
import threading
import json
import os
import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock

# ─────────────────────────────────────────
# KONFIGURASI DEFAULT
# ─────────────────────────────────────────
PROFILE_FILE = "profile_mahasiswa.json"
HISTORY_FILE = "history_mahasiswa.json"
TCP_PORT     = 9000
RECV_SIZE    = 4096

# ─────────────────────────────────────────
# STORAGE LOKAL
# ─────────────────────────────────────────
def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return None

def save_profile(data):
    data["last_sync"] = datetime.datetime.now().isoformat()
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history_entry(entry_type, payload, response):
    history = load_history()
    history.append({
        "type":     entry_type,
        "payload":  payload,
        "response": response,
        "ts":       datetime.datetime.now().isoformat()
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-100:], f, indent=2)

# ─────────────────────────────────────────
# KIVY SCREENS
# ─────────────────────────────────────────
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=24, spacing=15)

        layout.add_widget(Label(text="Login Smart Lab", font_size="24sp", bold=True, size_hint=(1, 0.2)))

        self.nim_input = TextInput(hint_text="NIM", text="13220033", multiline=False, font_size="16sp", size_hint=(1, 0.15))
        layout.add_widget(self.nim_input)

        self.nama_input = TextInput(hint_text="Nama Lengkap", text="Muhammad Al-Faaris", multiline=False, font_size="16sp", size_hint=(1, 0.15))
        layout.add_widget(self.nama_input)

        self.ip_input = TextInput(hint_text="IP Server", text="127.0.0.1", multiline=False, font_size="16sp", size_hint=(1, 0.15))
        layout.add_widget(self.ip_input)

        btn_login = Button(text="Masuk Aplikasi", font_size="18sp", size_hint=(1, 0.2), background_color=(0.2, 0.6, 1, 1))
        btn_login.bind(on_press=self.do_login)
        layout.add_widget(btn_login)

        layout.add_widget(Label(size_hint=(1, 0.15))) # Spacer bawah
        self.add_widget(layout)

    def do_login(self, instance):
        app = App.get_running_app()
        # Simpan data dari form ke memori aplikasi
        app.nim = self.nim_input.text.strip()
        app.nama = self.nama_input.text.strip()
        app.server_ip = self.ip_input.text.strip()

        # Update teks header di Main Screen, lalu pindah halaman
        main_screen = self.manager.get_screen('main')
        main_screen.update_header()
        self.manager.current = 'main'


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=16, spacing=10)

        # Header
        self.header_label = Label(text="Smart Lab", font_size="16sp", bold=True, size_hint=(1, 0.07), halign="center")
        layout.add_widget(self.header_label)

        # Status
        self.status_label = Label(text="Status: Belum terhubung", font_size="14sp", size_hint=(1, 0.07), halign="center")
        layout.add_widget(self.status_label)

        # Input Lab ID
        lab_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.10), spacing=8)
        lab_row.add_widget(Label(text="Lab ID:", size_hint=(0.3, 1)))
        self.lab_input = TextInput(text="LAB-A", hint_text="Contoh: LAB-A", multiline=False, font_size="15sp", size_hint=(0.7, 1))
        lab_row.add_widget(self.lab_input)
        layout.add_widget(lab_row)

        # Tombol Connect
        self.btn_connect = Button(text="🔌 Connect & Register", size_hint=(1, 0.11), font_size="15sp")
        self.btn_connect.bind(on_press=self.on_connect_press)
        layout.add_widget(self.btn_connect)

        # Tombol Fitur (Disabled by default)
        btn_grid = GridLayout(cols=2, size_hint=(1, 0.22), spacing=6)

        self.btn_presence = Button(text="📋 POST PRESENCE", font_size="14sp", disabled=True)
        self.btn_presence.bind(on_press=lambda x: App.get_running_app().send_presence())
        btn_grid.add_widget(self.btn_presence)

        self.btn_get_booking = Button(text="📅 GET BOOKING", font_size="14sp", disabled=True)
        self.btn_get_booking.bind(on_press=lambda x: App.get_running_app().send_get_booking())
        btn_grid.add_widget(self.btn_get_booking)

        self.btn_post_booking = Button(text="✅ POST BOOKING", font_size="14sp", disabled=True)
        self.btn_post_booking.bind(on_press=lambda x: App.get_running_app().show_booking_popup())
        btn_grid.add_widget(self.btn_post_booking)

        self.btn_announce = Button(text="📢 GET ANNOUNCE", font_size="14sp", disabled=True)
        self.btn_announce.bind(on_press=lambda x: App.get_running_app().send_get_announce())
        btn_grid.add_widget(self.btn_announce)

        layout.add_widget(btn_grid)

        # Feed Notifikasi
        layout.add_widget(Label(text="─── Notifikasi & Respons ───", font_size="12sp", size_hint=(1, 0.05)))
        scroll = ScrollView(size_hint=(1, 0.38))
        self.notif_label = Label(text="(Belum ada notifikasi)", font_size="12sp", size_hint_y=None, halign="left", valign="top", text_size=(None, None), markup=True)
        self.notif_label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
        scroll.add_widget(self.notif_label)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def update_header(self):
        app = App.get_running_app()
        self.header_label.text = f"Smart Lab — {app.nama} ({app.nim})"
        self.lab_input.text = app.lab_id_active

    def on_connect_press(self, instance):
        app = App.get_running_app()
        lab_id = self.lab_input.text.strip() or "LAB-A"
        app.init_network(lab_id)


# ─────────────────────────────────────────
# LOGIKA UTAMA APLIKASI
# ─────────────────────────────────────────
class SmartLabApp(App):
    def build(self):
        self.client_socket  = None
        self.connected      = False
        self.client_id      = None
        self.token          = None
        self.server_ip      = "127.0.0.1"
        self.lab_id_active  = "LAB-A"

        # Load profil lokal jika ada
        profile = load_profile()
        if profile:
            self.nim        = profile.get("nim", "13220033")
            self.nama       = profile.get("name", "Muhammad Al-Faaris")
            self.client_id  = profile.get("client_id")
            self.token      = profile.get("token")
            self.lab_id_active = profile.get("lab_id", "LAB-A")
        else:
            self.nim  = "13220033"
            self.nama = "Muhammad Al-Faaris"

        # Setup ScreenManager
        self.sm = ScreenManager()
        self.login_screen = LoginScreen(name='login')
        self.main_screen = MainScreen(name='main')

        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.main_screen)

        return self.sm

    # ─────────────────────────────────────
    # CONNECT & REGISTER & SUBSCRIBE
    # ─────────────────────────────────────
    def init_network(self, lab_id):
        self.lab_id_active = lab_id
        target_ip = self.server_ip

        if not target_ip:
            self.update_status("IP tidak boleh kosong!")
            return

        self.update_status(f"Menghubungkan ke {target_ip}:{TCP_PORT}...")
        self.main_screen.btn_connect.disabled = True

        threading.Thread(
            target=self._connect_thread,
            args=(target_ip, lab_id),
            daemon=True
        ).start()

    def _connect_thread(self, server_ip, lab_id):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_ip, TCP_PORT))
            self.client_socket = sock
            self.connected = True

            Clock.schedule_once(lambda dt: self.update_status(f"Terhubung ke {server_ip}"), 0)

            # REGISTER
            reg_msg = json.dumps({
                "type": "REGISTER",
                "name": self.nama,
                "nim":  self.nim,
                "role": "user"
            }).encode("utf-8")
            sock.sendall(reg_msg)

            reg_resp_raw = sock.recv(RECV_SIZE)
            reg_resp     = json.loads(reg_resp_raw.decode("utf-8"))

            if reg_resp.get("status") == "OK":
                self.client_id = reg_resp["client_id"]
                self.token     = reg_resp["token"]

                save_profile({
                    "client_id": self.client_id,
                    "name":      self.nama,
                    "nim":       self.nim,
                    "lab_id":    lab_id,
                    "token":     self.token
                })
                save_history_entry("REGISTER", {"nim": self.nim}, reg_resp)

                Clock.schedule_once(lambda dt: self.update_status(f"Register OK — {self.client_id}"), 0)
            else:
                Clock.schedule_once(lambda dt: self.update_status(f"Register gagal: {reg_resp.get('message')}"), 0)
                return

            # SUBSCRIBE
            sub_msg = json.dumps({
                "type":   "SUBSCRIBE",
                "lab_id": lab_id
            }).encode("utf-8")
            sock.sendall(sub_msg)

            sub_resp_raw = sock.recv(RECV_SIZE)
            sub_resp     = json.loads(sub_resp_raw.decode("utf-8"))

            if sub_resp.get("status") == "OK":
                Clock.schedule_once(lambda dt: self.update_status(f"Subscribe ke {lab_id} berhasil"), 0)
                Clock.schedule_once(lambda dt: self.enable_buttons(), 0)
                self._add_notif(f"[Subscribe] Terhubung ke {lab_id}")
            else:
                Clock.schedule_once(lambda dt: self.update_status(f"Subscribe gagal: {sub_resp.get('message')}"), 0)

            # Looop Terima Pesan
            while self.connected:
                try:
                    data = sock.recv(RECV_SIZE)
                    if not data:
                        break
                    incoming = json.loads(data.decode("utf-8"))
                    
                    if incoming.get("type") == "PUSH_NOTIF":
                        event = incoming.get("event", "INFO")
                        msg   = incoming.get("message", "Ada notifikasi baru")
                        ts    = incoming.get("ts", "")[:19]
                        self._add_notif(f"[{event}] {msg} | {ts}")
                    else:
                        status = incoming.get("status", "?")
                        self._add_notif(f"[ACK] status={status} | {json.dumps(incoming)[:80]}")
                except Exception:
                    break

        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Error koneksi: {e}"), 0)
        finally:
            self.connected = False
            if self.client_socket:
                self.client_socket.close()
            Clock.schedule_once(lambda dt: self.update_status("Terputus dari server"), 0)
            Clock.schedule_once(lambda dt: self.reset_buttons(), 0)

    # ─────────────────────────────────────
    # KIRIM PESAN TCP
    # ─────────────────────────────────────
    def _send_tcp(self, payload_dict):
        if not self.connected or not self.client_socket:
            self._add_notif("[!] Belum terhubung ke server")
            return
        try:
            data = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")
            self.client_socket.sendall(data)
        except Exception as e:
            self._add_notif(f"[!] Gagal kirim: {e}")

    # ─────────────────────────────────────
    # FITUR TOMBOL
    # ─────────────────────────────────────
    def send_presence(self):
        now = datetime.datetime.now().isoformat()
        payload = {
            "type":      "PRESENCE",
            "nim":       self.nim,
            "name":      self.nama,
            "lab_id":    self.lab_id_active,
            "course":    "EL3015",
            "status":    "HADIR",
            "timestamp": now
        }
        self._send_tcp(payload)
        save_history_entry("POST_PRESENCE", payload, {"sent": True})
        self._add_notif(f"[PRESENCE] Terkirim — {self.nama} HADIR di {self.lab_id_active}")

    def send_get_booking(self):
        payload = {
            "type":   "GET_BOOKING",
            "lab_id": self.lab_id_active
        }
        self._send_tcp(payload)
        save_history_entry("GET_BOOKING", payload, {"sent": True})
        self._add_notif(f"[GET_BOOKING] Request dikirim untuk {self.lab_id_active}")

    def show_booking_popup(self):
        content = BoxLayout(orientation="vertical", padding=12, spacing=8)
        content.add_widget(Label(text="Tanggal (YYYY-MM-DD):"))
        date_input = TextInput(text="2026-06-05", multiline=False, font_size="14sp", size_hint=(1, None), height=40)
        content.add_widget(date_input)

        content.add_widget(Label(text="Slot waktu (HH:MM-HH:MM):"))
        slot_input = TextInput(text="08:00-10:00", multiline=False, font_size="14sp", size_hint=(1, None), height=40)
        content.add_widget(slot_input)

        btn_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=44, spacing=8)
        btn_ok     = Button(text="Booking")
        btn_cancel = Button(text="Batal")
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(title=f"POST Booking — {self.lab_id_active}", content=content, size_hint=(0.9, 0.55))

        def do_booking(_):
            payload = {
                "type":   "POST_BOOKING",
                "nim":    self.nim,
                "lab_id": self.lab_id_active,
                "course": "EL3015",
                "date":   date_input.text.strip(),
                "slot":   slot_input.text.strip()
            }
            self._send_tcp(payload)
            save_history_entry("POST_BOOKING", payload, {"sent": True})
            self._add_notif(f"[POST_BOOKING] {self.lab_id_active} {date_input.text} {slot_input.text}")
            popup.dismiss()

        btn_ok.bind(on_press=do_booking)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def send_get_announce(self):
        payload = {
            "type":   "GET_ANNOUNCE",
            "lab_id": self.lab_id_active
        }
        self._send_tcp(payload)
        save_history_entry("GET_ANNOUNCE", payload, {"sent": True})
        self._add_notif(f"[GET_ANNOUNCE] Request dikirim untuk {self.lab_id_active}")

    # ─────────────────────────────────────
    # UI HELPERS (Akses via MainScreen)
    # ─────────────────────────────────────
    def _add_notif(self, text):
        def _update(dt):
            ts  = datetime.datetime.now().strftime("%H:%M:%S")
            cur = self.main_screen.notif_label.text
            if cur == "(Belum ada notifikasi)":
                cur = ""
            self.main_screen.notif_label.text = f"[{ts}] {text}\n{cur}"
            lines = self.main_screen.notif_label.text.split("\n")
            if len(lines) > 30:
                self.main_screen.notif_label.text = "\n".join(lines[:30])
        Clock.schedule_once(_update, 0)

    def update_status(self, text):
        self.main_screen.status_label.text = f"Status: {text}"

    def enable_buttons(self):
        self.main_screen.btn_presence.disabled    = False
        self.main_screen.btn_get_booking.disabled = False
        self.main_screen.btn_post_booking.disabled = False
        self.main_screen.btn_announce.disabled    = False

    def reset_buttons(self):
        self.main_screen.btn_connect.disabled     = False
        self.main_screen.btn_presence.disabled    = True
        self.main_screen.btn_get_booking.disabled = True
        self.main_screen.btn_post_booking.disabled = True
        self.main_screen.btn_announce.disabled    = True

if __name__ == "__main__":
    SmartLabApp().run()