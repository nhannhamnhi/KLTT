import os
import webbrowser
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QVBoxLayout, QMessageBox)

class DataViewerDialog(QDialog):
    def __init__(self, data_manager, sheets_url="", parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.sheets_url = sheets_url
        self.all_data = [] # Cache dữ liệu từ local
        
        self.init_ui()
        self.refresh_filters() # Load danh sách ngày/model vào combobox
        self.do_refresh() # Refresh bảng lần đầu

    def init_ui(self):
        self.setWindowTitle("📜 Nhật ký kết quả kiểm tra")
        self.setMinimumSize(1050, 650)
        self.resize(1100, 700)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # --- 1. Toolbar ---
        toolbar = QHBoxLayout()
        
        # Lọc ngày
        toolbar.addWidget(QLabel("📅 Lọc ngày:"))
        self.cb_date = QComboBox()
        self.cb_date.setMinimumWidth(180)
        toolbar.addWidget(self.cb_date)
        
        toolbar.addSpacing(15)
        
        # Lọc model
        toolbar.addWidget(QLabel("🤖 Model:"))
        self.cb_model = QComboBox()
        self.cb_model.setMinimumWidth(150)
        toolbar.addWidget(self.cb_model)
        
        toolbar.addStretch()
        
        # Các nút chức năng
        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_export = QPushButton("📥 Xuất Excel")
        self.btn_sheets = QPushButton("🔗 Mở Google Sheets")
        self.btn_close = QPushButton("✕ Đóng")
        
        # Styling buttons
        teal_style = """
            QPushButton { 
                background-color: #006666; color: white; border-radius: 4px; 
                padding: 6px 12px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #008080; }
            QPushButton:pressed { background-color: #004d4d; }
        """
        blue_style = teal_style.replace("#006666", "#1a73e8").replace("#008080", "#1e88e5")
        
        for btn in [self.btn_refresh, self.btn_export, self.btn_close]:
            btn.setStyleSheet(teal_style)
            toolbar.addWidget(btn)
            
        self.btn_sheets.setStyleSheet(blue_style)
        toolbar.insertWidget(toolbar.count()-1, self.btn_sheets)
        
        main_layout.addLayout(toolbar)

        # --- 2. Stats Bar ---
        stats_group = QGroupBox("📊 Thống kê nhanh (dựa trên dữ liệu đang hiển thị)")
        stats_layout = QHBoxLayout(stats_group)
        
        self.stats_labels = {}
        stats_config = [
            ("TỔNG LƯỢT", "total", "#f0f0f0", "black"),
            ("OK", "ok", "#c6efce", "#006100"),
            ("NG (TỔNG)", "ng", "#ffc7ce", "#9c0006"),
            ("NG_L", "ng_l", "#fff2cc", "#9c6500"),
            ("NG_H", "ng_h", "#ffc7ce", "#9c0006"),
            ("MISSING", "missing", "#ffd699", "#853d00"),
            ("TỶ LỆ ĐẠT", "rate", "#c6efce", "#006100")
        ]
        
        for title, key, bg, fg in stats_config:
            box = QGroupBox()
            box.setStyleSheet(f"QGroupBox {{ background-color: {bg}; border: 1px solid #ccc; border-radius: 5px; }}")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(5, 5, 5, 5)
            
            lbl_title = QLabel(title)
            lbl_title.setAlignment(QtCore.Qt.AlignCenter)
            lbl_title.setStyleSheet(f"color: {fg}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
            
            lbl_val = QLabel("0")
            lbl_val.setAlignment(QtCore.Qt.AlignCenter)
            lbl_val.setStyleSheet(f"color: {fg}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
            
            box_layout.addWidget(lbl_title)
            box_layout.addWidget(lbl_val)
            stats_layout.addWidget(box)
            self.stats_labels[key] = lbl_val
            
        main_layout.addWidget(stats_group)

        # --- 3. Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["STT", "Ngày", "Thời gian", "Tổng", "Đạt", "Lỗi", "Kết quả", "Model AI"])
        
        # Header style
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #006666; color: white;
                font-weight: bold; border: 1px solid #004d4d;
                height: 35px;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        
        main_layout.addWidget(self.table)

        # --- 4. Status Bar ---
        self.lbl_status = QLabel("Sẵn sàng")
        main_layout.addWidget(self.lbl_status)

        # Connect events
        self.cb_date.currentIndexChanged.connect(self.do_refresh)
        self.cb_model.currentIndexChanged.connect(self.do_refresh)
        self.btn_refresh.clicked.connect(self.handle_reload)
        self.btn_export.clicked.connect(self.handle_export)
        self.btn_sheets.clicked.connect(self.handle_open_sheets)
        self.btn_close.clicked.connect(self.accept)

    # --- LOGIC ---
    def refresh_filters(self):
        """Cập nhật danh sách ngày và model vào ComboBox"""
        # 1. Date filter
        self.cb_date.blockSignals(True)
        self.cb_date.clear()
        self.cb_date.addItem("📅 Tất cả — 90 ngày gần nhất", None)
        
        available_dates = self.data_manager.get_available_dates()
        for d_str in available_dates:
            try:
                d_obj = datetime.strptime(d_str, '%Y-%m-%d')
                display_date = d_obj.strftime('%d/%m/%Y')
                self.cb_date.addItem(display_date, d_str)
            except:
                continue
        self.cb_date.blockSignals(False)

        # 2. Model filter
        self.cb_model.blockSignals(True)
        self.cb_model.clear()
        self.cb_model.addItem("🤖 Tất cả model")
        
        # Lấy unique models từ data thực tế
        all_data = self.data_manager.get_all_records_as_list()
        models = sorted(list(set(r.get('model_name', 'N/A') for r in all_data)))
        self.cb_model.addItems(models)
        self.cb_model.blockSignals(False)
        
        self.all_data = all_data

    def handle_reload(self):
        """Tải lại dữ liệu từ file và refresh UI"""
        self.data_manager.data = self.data_manager.load_data()
        self.refresh_filters()
        self.do_refresh()

    def do_refresh(self):
        """Lọc và hiển thị dữ liệu lên bảng + stats"""
        target_date = self.cb_date.currentData()
        target_model = self.cb_model.currentText()
        
        # 1. Lọc dữ liệu
        filtered = []
        for r in self.all_data:
            # Chuyển dd/mm/yyyy thành YYYY-MM-DD để so sánh
            d_parts = r['date'].split('/')
            if len(d_parts) == 3:
                r_iso_date = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}"
            else:
                r_iso_date = ""
            
            if target_date and r_iso_date != target_date: continue
            if target_model != "🤖 Tất cả model" and r.get('model_name', 'N/A') != target_model: continue
            filtered.append(r)

        # 2. Cập nhật Stats
        stats = { 'total': 0, 'ok': 0, 'ng_l': 0, 'ng_h': 0, 'missing': 0 }
        for r in filtered:
            stats['total'] += 1
            res = r.get('result', '')
            if res == 'OK': stats['ok'] += 1
            elif res == 'NG_L': stats['ng_l'] += 1
            elif res == 'NG_H': stats['ng_h'] += 1
            elif res == 'MISSING': stats['missing'] += 1
            
        ng_total = stats['ng_l'] + stats['ng_h'] + stats['missing']
        rate = (stats['ok'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        self.stats_labels['total'].setText(str(stats['total']))
        self.stats_labels['ok'].setText(str(stats['ok']))
        self.stats_labels['ng'].setText(str(ng_total))
        self.stats_labels['ng_l'].setText(str(stats['ng_l']))
        self.stats_labels['ng_h'].setText(str(stats['ng_h']))
        self.stats_labels['missing'].setText(str(stats['missing']))
        self.stats_labels['rate'].setText(f"{rate:.1f}%")

        # 3. Hiển thị bảng
        self.table.setRowCount(0)
        for i, r in enumerate(filtered):
            self.table.insertRow(i)
            
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(r['date']))
            self.table.setItem(i, 2, QTableWidgetItem(r['time']))
            self.table.setItem(i, 3, QTableWidgetItem(str(r['total'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(r['passed'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(r['failed'])))
            
            res_item = QTableWidgetItem(r['result'])
            if r['result'] == 'OK': res_item.setBackground(QtGui.QColor("#c6efce"))
            elif 'NG' in r['result'] or r['result'] == 'MISSING': res_item.setBackground(QtGui.QColor("#ffc7ce"))
            
            self.table.setItem(i, 6, res_item)
            self.table.setItem(i, 7, QTableWidgetItem(r.get('model_name', 'N/A')))
            
            for col in range(8):
                item = self.table.item(i, col)
                if item: item.setTextAlignment(QtCore.Qt.AlignCenter)

        self.lbl_status.setText(f"Hiển thị {len(filtered)} bản ghi.")

    def handle_export(self):
        """Xuất Excel theo ngày đang chọn"""
        date_filter = self.cb_date.currentData()
        default_name = f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Lưu báo cáo Excel", default_name, "Excel Files (*.xlsx)")
        
        if path:
            success = self.data_manager.export_to_excel(path, date_filter=date_filter)
            if success:
                QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo tại:\n{path}")
            else:
                QMessageBox.critical(self, "Lỗi", "Không thể xuất file Excel. Vui lòng kiểm tra lại.")

    def handle_open_sheets(self):
        """Mở liên kết Google Sheets"""
        if self.sheets_url and self.sheets_url.startswith("http"):
            webbrowser.open(self.sheets_url)
        else:
            QMessageBox.warning(self, "Thông báo", "Đường dẫn Google Sheets chưa được cấu hình trong config.py")
