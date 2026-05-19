import sys
import os
import webbrowser
from datetime import datetime, date
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem

# Import UI generated from .ui file
from .data_viewer_dialog_ui import Ui_DataViewerDialog

class DataViewerDialog(QtWidgets.QDialog, Ui_DataViewerDialog):
    """
    Dialog hiển thị danh sách kết quả kiểm tra, thống kê và quản lý Google Sheets.
    Giao diện được tải từ file data_viewer_dialog.ui
    """
    def __init__(self, data_manager, sheets_url=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.sheets_url = sheets_url
        self.main_win = parent
        
        # Khởi tạo giao diện từ file UI đã convert
        self.setupUi(self)
        
        # Mặc định chọn ngày hiện tại cho QDateEdit
        self.cb_date.setDate(QtCore.QDate.currentDate())
        
        # Cấu hình bảng
        self.setup_table_config()
        
        # Load dữ liệu ban đầu
        self.refresh_filters()
        self.do_refresh()
        
        # Kết nối signals
        self.btn_refresh.clicked.connect(self.do_refresh)
        self.btn_export.clicked.connect(self.handle_export)
        self.btn_sheets.clicked.connect(self.handle_open_sheets)
        self.btn_close.clicked.connect(self.close)
        self.btn_sync_sheets.clicked.connect(self.handle_sync_sheets)
        
        # Kết nối bộ lọc
        # cb_date bây giờ là QDateEdit
        self.cb_date.dateChanged.connect(self.do_refresh)
        self.cb_model.currentIndexChanged.connect(self.do_refresh)
        
        # Cập nhật trạng thái Sheets định kỳ
        self.status_timer = QtCore.QTimer(self)
        self.status_timer.timeout.connect(self.refresh_sheet_status)
        self.status_timer.start(2000) # Cập nhật mỗi 2 giây
        self.refresh_sheet_status()

    def setup_table_config(self):
        """Cấu hình chi tiết cho QTableWidget."""
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed) # STT
        self.table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed) # Ngày
        self.table.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed) # Thời gian
        self.table.setColumnWidth(2, 100)
        
        # Các cột số lượng
        for i in range(3, 6):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
            self.table.setColumnWidth(i, 60)
            
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.Stretch) # Kết quả
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.Stretch) # Model AI

    def refresh_filters(self):
        """Cập nhật danh sách model vào combobox."""
        # 1. Model filter
        self.cb_model.blockSignals(True)
        self.cb_model.clear()
        self.cb_model.addItem("🤖 Tất cả model", None)
        models = self.data_manager.get_available_models()
        for m in models:
            self.cb_model.addItem(m, m)
        self.cb_model.blockSignals(False)

    def do_refresh(self):
        """Lấy dữ liệu từ DataManager theo bộ lọc và hiển thị lên bảng."""
        # Lấy ngày từ QDateEdit
        q_date = self.cb_date.date()
        date_filter = q_date.toString("yyyy-MM-dd")
        
        model_filter = self.cb_model.currentData()
        
        # Lấy dữ liệu
        data = self.data_manager.get_filtered_data(date_filter, model_filter)
        
        # Hiển thị
        self.table.setRowCount(0)
        stats = {
            'total': 0, 'ok': 0, 'ng': 0,
            'ng_l': 0, 'ng_h': 0, 'missing': 0
        }
        
        for i, item in enumerate(data):
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            
            # 1. STT
            self.table.setItem(row_pos, 0, QTableWidgetItem(str(i + 1)))
            
            # 2. Ngày
            d_obj = datetime.strptime(item['date'], '%Y-%m-%d')
            self.table.setItem(row_pos, 1, QTableWidgetItem(d_obj.strftime('%d/%m/%Y')))
            
            # 3. Thời gian
            self.table.setItem(row_pos, 2, QTableWidgetItem(item['time']))
            
            # 4. Tổng
            self.table.setItem(row_pos, 3, QTableWidgetItem(str(item['total'])))
            
            # 5. Đạt
            self.table.setItem(row_pos, 4, QTableWidgetItem(str(item['passed'])))
            
            # 6. Lỗi
            self.table.setItem(row_pos, 5, QTableWidgetItem(str(item['failed'])))
            
            # 7. Kết quả (Màu sắc)
            res_item = QTableWidgetItem(item['result'])
            res_item.setTextAlignment(QtCore.Qt.AlignCenter)
            if item['result'] == "OK":
                res_item.setForeground(QtGui.QColor("#006100"))
                res_item.setBackground(QtGui.QColor("#c6efce"))
                stats['ok'] += 1
            elif item['result'] == "NG_L":
                res_item.setForeground(QtGui.QColor("#9c6500"))
                res_item.setBackground(QtGui.QColor("#fff2cc"))
                stats['ng_l'] += 1
                stats['ng'] += 1
            elif item['result'] == "NG_H":
                res_item.setForeground(QtGui.QColor("#9c0006"))
                res_item.setBackground(QtGui.QColor("#ffc7ce"))
                stats['ng_h'] += 1
                stats['ng'] += 1
            elif item['result'] == "MISSING":
                res_item.setForeground(QtGui.QColor("#853d00"))
                res_item.setBackground(QtGui.QColor("#ffd699"))
                stats['missing'] += 1
                stats['ng'] += 1
                
            self.table.setItem(row_pos, 6, res_item)
            
            # 8. Model
            self.table.setItem(row_pos, 7, QTableWidgetItem(item.get('model_name', 'N/A')))
            
            stats['total'] += 1

        # Cập nhật thống kê
        self.lbl_val_total.setText(str(stats['total']))
        self.lbl_val_ok.setText(str(stats['ok']))
        self.lbl_val_ng.setText(str(stats['ng']))
        self.lbl_val_ngl.setText(str(stats['ng_l']))
        self.lbl_val_ngh.setText(str(stats['ng_h']))
        self.lbl_val_missing.setText(str(stats['missing']))
        
        rate = (stats['ok'] / stats['total'] * 100) if stats['total'] > 0 else 0
        self.lbl_val_rate.setText(f"{rate:.1f}%")
        
        self.lbl_status.setText(f"Hiển thị {len(data)} bản ghi.")

    def refresh_sheet_status(self):
        """Cập nhật trạng thái kết nối Google Sheets lên UI."""
        status = self.data_manager.get_sheets_status()
        
        # Badge color
        if not status.get('enabled', False):
            self.lbl_sheets_badge.setText("Google Sheets: Tắt")
            self.lbl_sheets_badge.setStyleSheet("padding: 4px 10px; border-radius: 12px; background-color: #9e9e9e; color: white;")
        elif status.get('connected', False):
            self.lbl_sheets_badge.setText("Google Sheets: Đã kết nối")
            self.lbl_sheets_badge.setStyleSheet("padding: 4px 10px; border-radius: 12px; background-color: #4caf50; color: white;")
        else:
            self.lbl_sheets_badge.setText("Google Sheets: Error")
            self.lbl_sheets_badge.setStyleSheet("padding: 4px 10px; border-radius: 12px; background-color: #f44336; color: white;")
            
        self.lbl_sheets_queue.setText(f"Hàng chờ: {status.get('queue_size', 0)}")
        
        error_text = status.get('last_error', '') or 'Không có'
        self.lbl_sheets_error.setText(f"Lỗi: {error_text}")

    def handle_sync_sheets(self):
        """Kích hoạt đồng bộ thủ công ngay lập tức."""
        status = self.data_manager.get_sheets_status()
        
        # 1. Nếu có hàng chờ, ưu tiên đẩy hàng chờ
        if status.get('queue_size', 0) > 0:
            count = self.data_manager.force_sync_sheets()
            if count > 0:
                QMessageBox.information(self, "Đồng bộ", f"Đã gửi thành công {count} bản ghi từ hàng chờ lên Google Sheets.")
            else:
                QMessageBox.warning(self, "Đồng bộ", f"Không thể đồng bộ. Lỗi: {status.get('last_error')}")
        
        # 2. Nếu hàng chờ trống, hỏi xem có muốn đẩy lại ngày hiện tại không
        else:
            q_date = self.cb_date.date()
            date_str = q_date.toString("yyyy-MM-dd")
            display_date = q_date.toString("dd/MM/yyyy")
            
            reply = QMessageBox.question(
                self, "Đồng bộ lịch sử",
                f"Hàng chờ đang trống.\nBạn có muốn đẩy lại toàn bộ dữ liệu của ngày {display_date} lên Google Sheets không?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.lbl_status.setText(f"Đang đẩy dữ liệu ngày {display_date}...")
                QtWidgets.QApplication.processEvents() # Cập nhật UI ngay
                
                count = self.data_manager.sync_history_to_sheets(date_str)
                if count > 0:
                    QMessageBox.information(self, "Thành công", f"Đã đẩy thành công {count} bản ghi ngày {display_date} lên Google Sheets.")
                else:
                    QMessageBox.warning(self, "Thất bại", "Không có dữ liệu hoặc lỗi kết nối. Kiểm tra tab 'Lỗi' phía trên.")
        
        self.refresh_sheet_status()

    def handle_export(self):
        """Xuất dữ liệu đang hiển thị ra file Excel."""
        # Lấy ngày từ QDateEdit
        date_filter = self.cb_date.date().toString("yyyy-MM-dd")
        model_filter = self.cb_model.currentData()
        
        # Gợi ý tên file
        default_name = f"KetQua_KiemTra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        path, _ = QFileDialog.getSaveFileName(
            self.main_win, "Lưu file Excel", default_name, "Excel Files (*.xlsx)"
        )
        
        if path:
            success, msg = self.data_manager.export_to_excel(path, date_filter, model_filter)
            if success:
                QMessageBox.information(self.main_win, "Thành công", f"Đã xuất dữ liệu ra:\n{path}")
            else:
                QMessageBox.critical(self.main_win, "Lỗi", f"Không thể xuất file:\n{msg}")

    def handle_open_sheets(self):
        """Mở liên kết Google Sheets"""
        if self.sheets_url and self.sheets_url.startswith("http"):
            status = self.data_manager.get_sheets_status()
            if not status.get('connected', False) and status.get('last_error'):
                QMessageBox.warning(self.main_win, "Cảnh báo Google Sheets", f"Google Sheets chưa kết nối: {status.get('last_error')}\nBạn vẫn có thể mở link để kiểm tra cấu hình.")
            webbrowser.open(self.sheets_url)
        else:
            QMessageBox.warning(self.main_win, "Thông báo", "Đường dẫn Google Sheets chưa được cấu hình trong config.py")
