import sys
from PyQt6 import QtWidgets, uic

# Lớp chính của ứng dụng để quản lý giao diện
class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        # Load file giao diện từ Qt Designer
        uic.loadUi(r"d:\KL_2025\GUI_QT_PYTHON\untitled.ui", self)
        
        # Kết nối các sự kiện (ví dụ: bấm nút)
        self.pushButton.clicked.connect(self.on_button_click)

    def on_button_click(self):
        # Hàm xử lý khi người dùng nhấn vào nút pushButton
        print("Bạn đã nhấn nút trên giao diện!")
        QtWidgets.QMessageBox.information(self, "Thông báo", "Chào mừng bạn đến với ứng dụng Python GUI!")

# Hàm khởi chạy ứng dụng
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
