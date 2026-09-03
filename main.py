import socket
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import mainthread

class NetworkScannerApp(App):
    def build(self):
        self.title = "S.B. INFOTECH - CCTV Tool"
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = Label(
            text="S.B. INFOTECH\nCCTV Diagnostic Tool (+91 9924757111)",
            size_hint_y=None, height=60, halign="center", bold=True
        )
        main_layout.add_widget(header)
        
        # Subnet Input & Scan Button
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
        self.subnet_input = TextInput(text="192.168.1", multiline=False, hint_text="Subnet (e.g. 192.168.1)")
        scan_btn = Button(text="Scan Network", background_color=(0, 0.55, 0.73, 1))
        scan_btn.bind(on_press=self.start_scan)
        
        input_layout.add_widget(self.subnet_input)
        input_layout.add_widget(scan_btn)
        main_layout.add_widget(input_layout)
        
        # Results Scroll Area
        scroll = ScrollView()
        self.results_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.results_grid.bind(minimum_height=self.results_grid.setter('height'))
        scroll.add_widget(self.results_grid)
        
        main_layout.add_widget(scroll)
        return main_layout

    def start_scan(self, instance):
        self.results_grid.clear_widgets()
        self.results_grid.add_widget(Label(text="Scanning network...", size_hint_y=None, height=40))
        subnet = self.subnet_input.text.strip()
        
        def run_scan():
            found_devices = []
            with ThreadPoolExecutor(max_workers=30) as executor:
                for i in range(1, 255):
                    ip = f"{subnet}.{i}"
                    executor.submit(self.ping_ip, ip, found_devices)
            self.update_ui(found_devices)

        import threading
        threading.Thread(target=run_scan, daemon=True).start()

    def ping_ip(self, ip, found_devices):
        param = "-c" if platform.system().lower() != "windows" else "-n"
        cmd = ["ping", param, "1", "-w", "1", ip]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
            if res.returncode == 0:
                found_devices.append(ip)
        except Exception:
            pass

    @mainthread
    def update_ui(self, devices):
        self.results_grid.clear_widgets()
        if not devices:
            self.results_grid.add_widget(Label(text="No active devices found.", size_hint_y=None, height=40))
            return

        for ip in sorted(devices, key=lambda x: tuple(map(int, x.split('.')))):
            row = Label(
                text=f"Online: {ip}",
                size_hint_y=None, height=40,
                color=(0, 1, 0, 1)
            )
            self.results_grid.add_widget(row)

if __name__ == "__main__":
    NetworkScannerApp().run()
