from bs4 import BeautifulSoup as soup
from urllib.request import urlopen as uReq
import re
from plyer import notification
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QDialog, QFormLayout, QSpinBox
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer
from PyQt5.QtGui import QIcon
import os

################################################################
#Sample product URLs
#https://remixshop.com/bg/mens-clothes-shirts-pr30569734.html
#https://remixshop.com/bg/mens-clothes-shirts-marc-o'polo-pr30569738.html
################################################################

root = os.path.split(__file__)[0]
images = os.path.join(root, 'images/unnamed.png')

class ProductParser(QRunnable):
    def __init__(self, urls):
        super(ProductParser, self).__init__()
        self.urls = urls

    def run(self):
        parse_urls(self.urls)

def parse_urls(urls):
    products = []

    for url in urls:
        try:
            uClient = uReq(url)
            page_soup = soup(uClient.read(), 'html.parser')
            uClient.close()

            containers = page_soup.find('div', {'class': 'col-md-6 col-lg-4 d-flex'})
            promo_div = containers.div.find('span', {'class': 'promo badge'})
            promo_per = re.sub(r'[^\d]', '', promo_div.text)

            if int(promo_per) >= 50:
                product = 'This product ' + url + ' is ' + promo_per + '% off!'
                products.append(product)
                notification.notify(
                    title="Remix Checker",
                    message=product,
                    #app_icon = 'icon',
                    timeout=10
                )
        except Exception as e:
            print(f"An error occurred while parsing {url}: {e}")

class TimerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timer Settings")
        self.timer_duration = QSpinBox(self)
        self.timer_duration.setRange(1, 60)
        self.timer_duration.setValue(5)  # Default timer duration is 5 minutes

        start_button = QPushButton("Start Timer")
        start_button.clicked.connect(self.start_timer)

        layout = QFormLayout(self)
        layout.addRow("Timer Duration (minutes):", self.timer_duration)
        layout.addRow(start_button)

    def start_timer(self):
        timer_duration_minutes = self.timer_duration.value()
        # Convert minutes to milliseconds for QTimer
        timer_duration_ms = timer_duration_minutes * 60 * 1000

        self.accept()
        self.parent().start_timer(timer_duration_ms)

class ProductNotifier(QWidget):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.dark_mode = False

        self.init_ui()

    def init_ui(self):
        vbox = QVBoxLayout(self)

        label = QLabel("Enter product URLs:")
        vbox.addWidget(label)

        self.entry = QLineEdit()
        self.entry.setFixedHeight(30)
        vbox.addWidget(self.entry)

        add_button = QPushButton("Add URL")
        add_button.clicked.connect(self.on_add_url_clicked)
        vbox.addWidget(add_button)

        self.list_widget = QListWidget()
        vbox.addWidget(self.list_widget)

        remove_button = QPushButton("Remove URL")
        remove_button.clicked.connect(self.on_remove_url_clicked)
        vbox.addWidget(remove_button)

        parse_button = QPushButton("Parse URLs")
        parse_button.clicked.connect(self.on_parse_urls_clicked)
        vbox.addWidget(parse_button)

        self.timer_label = QLabel("Timer: 0:00")
        vbox.addWidget(self.timer_label)

        timer_button = QPushButton("Set Timer")
        timer_button.clicked.connect(self.on_timer_settings_clicked)
        vbox.addWidget(timer_button)

        dark_mode_button = QPushButton("Dark Mode")
        dark_mode_button.clicked.connect(self.on_dark_mode_clicked)
        vbox.addWidget(dark_mode_button)

        self.setLayout(vbox)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_label)

    def on_add_url_clicked(self):
        url = self.entry.text()
        self.urls.append(url)
        self.list_widget.addItem(url)
        self.entry.clear()

    def on_remove_url_clicked(self):
        selected_row = self.list_widget.currentRow()
        if selected_row >= 0:
            self.list_widget.takeItem(selected_row)
            self.urls.pop(selected_row)

    def on_parse_urls_clicked(self):
        if self.urls:
            # Create a ProductParser instance and pass the URLs
            product_parser = ProductParser(self.urls)
            # Start the parsing task in the background
            QThreadPool.globalInstance().start(product_parser)

    def on_timer_settings_clicked(self):
        timer_window = TimerWindow(self)
        timer_window.exec_()

    def on_dark_mode_clicked(self):
        self.dark_mode = not self.dark_mode
        self.set_dark_mode(self.dark_mode)

    def set_dark_mode(self, dark_mode):
        if dark_mode:
            self.setStyleSheet("background-color: #303030; color: white;")
        else:
            self.setStyleSheet("")

    def start_timer(self, timer_duration_ms):
        self.timer_duration_ms = timer_duration_ms
        self.timer_countdown = timer_duration_ms
        self.timer.start(1000)  # Update the timer label every 1 second

    def update_timer_label(self):
        minutes = self.timer_countdown // 60000
        seconds = (self.timer_countdown // 1000) % 60
        self.timer_label.setText(f"Timer: {minutes}:{seconds:02}")

        self.timer_countdown -= 1000

        if self.timer_countdown < 0:
            self.timer.stop()
            self.on_parse_urls_clicked()
            self.start_timer(self.timer_duration_ms)  # Restart the timer

if __name__ == "__main__":
    app = QApplication([])
    app_icon = QIcon(images)
    app.setWindowIcon(app_icon)

    window = ProductNotifier()
    window.setWindowTitle("Remix Checker")
    window.show()
    app.exec_()