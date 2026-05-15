# -*- coding: utf-8 -*-
"""
Module quản lý dữ liệu - Lưu trữ JSON và Xuất Excel
Tác giả: Auto-generated
Mô tả: Quản lý việc lưu/load dữ liệu kết quả phát hiện, tự động dọn dẹp dữ liệu cũ và xuất Excel
"""

import os
import json
from datetime import datetime, timedelta
from threading import Thread, Lock

# --- Bổ sung: Import thư viện Google Sheets (tùy chọn) ---
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("[WARNING] Missing gspread/google-auth. Install with: pip install gspread google-auth")

# --- Bổ sung: Import cấu hình từ config.py ---
try:
    from . import config
    SPREADSHEET_ID = config.SPREADSHEET_ID
    SERVICE_ACCOUNT_FILE = config.SERVICE_ACCOUNT_FILE
    SHEET_NAME = config.SHEET_NAME
    DATA_RETENTION_DAYS = config.DATA_RETENTION_DAYS
    SHEETS_CONFIGURED = True # Đánh dấu đã có file config và đã load thành công
except ImportError:
    # Nếu không tìm thấy config.py hoặc lỗi, dùng giá trị mặc định và vô hiệu hóa Sheets
    SPREADSHEET_ID = ""
    SERVICE_ACCOUNT_FILE = "src/data/service_account.json"
    SHEET_NAME = "KLTT_Data"
    DATA_RETENTION_DAYS = 90 # Mặc định 90 ngày
    SHEETS_CONFIGURED = False
    print("[WARNING] Could not import src/data/config.py. Google Sheets feature disabled.")

# Resolve SERVICE_ACCOUNT_FILE to an absolute path relative to this module when possible.
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_service_account_path(service_account_file):
    if not service_account_file:
        return service_account_file

    if os.path.isabs(service_account_file):
        return service_account_file

    candidate = os.path.abspath(os.path.join(MODULE_DIR, service_account_file))
    if os.path.exists(candidate):
        return candidate

    alternate = os.path.abspath(service_account_file)
    if os.path.exists(alternate):
        return alternate

    return candidate


SERVICE_ACCOUNT_FILE = _resolve_service_account_path(SERVICE_ACCOUNT_FILE)

# Thư viện để xuất Excel với merge cell
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("[WARNING] Missing openpyxl. Install with: pip install openpyxl")


class DataManager:
    """
    Lớp quản lý dữ liệu kết quả phát hiện
    - Lưu/Load từ file JSON
    - Tự động xóa dữ liệu cũ
    - Xuất ra Excel với merge cell
    """

    def __init__(self, data_dir=None):
        """
        Khởi tạo DataManager

        Args:
            data_dir: Thư mục lưu dữ liệu. Mặc định là 'data/' trong cùng thư mục với file này
        """
        # Xác định thư mục lưu dữ liệu
        if data_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(current_dir, 'data')

        self.data_dir = data_dir
        self.json_file = os.path.join(data_dir, 'data_history.json')
        self.pending_queue_file = os.path.join(data_dir, 'pending_queue.json')

        # Lock để đảm bảo thread-safe khi ghi file
        self._lock = Lock()

        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Load dữ liệu và dọn dẹp dữ liệu cũ
        self.data = self.load_data()
        self.cleanup_old_data()

        # --- Bổ sung Google Sheets và hàng chờ ---
        self._gs_sheet = None
        self._pending_queue = self._load_pending_queue()
        self.sheets_status = {
            'enabled': False,
            'connected': False,
            'queue_size': len(self._pending_queue),
            'last_error': '',
            'error_code': 'UNINITIALIZED',
            'spreadsheet_id': SPREADSHEET_ID,
            'sheet_name': SHEET_NAME,
            'credential_file': SERVICE_ACCOUNT_FILE,
        }

        self._evaluate_sheets_feature()

    def _set_sheet_status(self, enabled=False, connected=False, error_code='UNINITIALIZED', last_error=''):
        self.sheets_status['enabled'] = enabled
        self.sheets_status['connected'] = connected
        self.sheets_status['error_code'] = error_code
        self.sheets_status['last_error'] = last_error
        self.sheets_status['queue_size'] = len(self._pending_queue)

    def _evaluate_sheets_feature(self):
        if not GOOGLE_SHEETS_AVAILABLE:
            self._set_sheet_status(
                enabled=False,
                connected=False,
                error_code='MISSING_DEPENDENCY',
                last_error='Missing gspread/google-auth dependency.'
            )
            print("[CHECK] Google Sheets disabled: missing gspread/google-auth.")
            return

        if not SHEETS_CONFIGURED:
            self._set_sheet_status(
                enabled=False,
                connected=False,
                error_code='CONFIG_MISSING',
                last_error='Không thể load config.py cho Google Sheets.'
            )
            print("[CHECK] Google Sheets disabled: config.py load failed.")
            return

        if not SPREADSHEET_ID:
            self._set_sheet_status(
                enabled=False,
                connected=False,
                error_code='SPREADSHEET_ID_MISSING',
                last_error='SPREADSHEET_ID chưa được cấu hình trong config.py.'
            )
            print("[CHECK] Google Sheets disabled: missing SPREADSHEET_ID.")
            return

        if not SERVICE_ACCOUNT_FILE:
            self._set_sheet_status(
                enabled=False,
                connected=False,
                error_code='SERVICE_ACCOUNT_FILE_MISSING',
                last_error='SERVICE_ACCOUNT_FILE chưa được cấu hình trong config.py.'
            )
            print("[CHECK] Google Sheets disabled: missing SERVICE_ACCOUNT_FILE.")
            return

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            self._set_sheet_status(
                enabled=False,
                connected=False,
                error_code='SERVICE_ACCOUNT_FILE_NOT_FOUND',
                last_error=f'Không tìm thấy file credential: {SERVICE_ACCOUNT_FILE}'
            )
            print(f"[CHECK] Google Sheets disabled: credential file not found at {SERVICE_ACCOUNT_FILE}.")
            return

        self._set_sheet_status(enabled=True, connected=False, error_code='INITIALIZED', last_error='')
        self._init_gspread()

    def get_sheets_status(self):
        """Trả về trạng thái kết nối Google Sheets hiện tại."""
        status = self.sheets_status.copy()
        status['queue_size'] = len(self._pending_queue)
        return status

    def _update_pending_queue_size(self):
        self.sheets_status['queue_size'] = len(self._pending_queue)

    def retry_sheets_sync(self):
        """Thử kết nối lại Google Sheets và đẩy lại hàng chờ."""
        if not self.sheets_status['enabled']:
            return 0, self.sheets_status['last_error']

        if self._gs_sheet is None:
            self._init_gspread()

        if self._gs_sheet is None:
            return 0, self.sheets_status['last_error'] or 'Không thể kết nối Google Sheets.'

        success_count = self._flush_pending_queue()
        if success_count > 0:
            return success_count, ''

        return 0, self.sheets_status['last_error'] or 'Không có bản ghi nào cần đồng bộ.'

    def force_sync_sheets(self):
        """Ép buộc đồng bộ hàng chờ ngay lập tức."""
        count, error = self.retry_sheets_sync()
        return count

    def sync_history_to_sheets(self, date_str):
        """
        Quét toàn bộ dữ liệu local của một ngày và đẩy lên Google Sheets (Batch).
        Dùng khi dữ liệu đã lưu local nhưng chưa có trên Sheets.
        """
        if not self.sheets_status['enabled'] or date_str not in self.data:
            return 0
            
        records = self.data[date_str]
        if not records:
            return 0
            
        # Chuẩn bị dữ liệu để đẩy hàng loạt
        rows_to_push = []
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            display_date = date_obj.strftime('%d/%m/%Y')
            sheet_name = date_obj.strftime('%d-%m-%Y')
            
            for rec in records:
                row = [
                    display_date,
                    rec['time'],
                    rec['total'],
                    rec['passed'],
                    rec['failed'],
                    rec['result'],
                    rec.get('model_name', 'N/A')
                ]
                rows_to_push.append(row)
                
            if not rows_to_push:
                return 0

            # Khởi tạo sheets nếu chưa có
            if self._gs_spreadsheet is None:
                self._init_gspread()
            
            if self._gs_spreadsheet:
                sheet = self._get_or_create_worksheet(self._gs_spreadsheet, sheet_name)
                sheet.append_rows(rows_to_push)
                return len(rows_to_push)
        except Exception as e:
            print(f"[LỖI SYNC LỊCH SỬ] {e}")
            self._set_sheet_status(enabled=True, connected=False, error_code='SYNC_ERROR', last_error=str(e))
            
        return 0

    def load_data(self):
        """
        Load dữ liệu từ file JSON

        Returns:
            dict: Dictionary với key là ngày (YYYY-MM-DD), value là list các bản ghi
        """
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[LỖI] Không thể đọc file JSON: {e}")
                return {}
        return {}

    def _write_json(self):
        """
        Ghi dữ liệu ra file JSON (internal method)
        Được gọi trong thread riêng để không block UI
        """
        with self._lock:
            try:
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"[LỖI] Không thể ghi file JSON: {e}")

    def save_record(self, total, passed, failed, result, model_name=""):
        """
        Lưu một bản ghi mới (bất đồng bộ)

        Args:
            total: Tổng số viên phát hiện được
            passed: Số viên đạt (Full)
            failed: Số viên lỗi (Partial, Empty)
            result: Kết quả tổng hợp (OK/NG)
            model_name: Tên model AI đang sử dụng

        Returns:
            str: Chuỗi hiển thị cho danh sách UI
        """
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        # Tạo bản ghi mới
        record = {
            'time': time_str,
            'model_name': model_name,
            'total': total,
            'passed': passed,
            'failed': failed,
            'result': result
        }

        # Thêm vào dữ liệu
        if date_str not in self.data:
            self.data[date_str] = []
        self.data[date_str].append(record)

        # Ghi file trong thread riêng (async) để không block UI
        Thread(target=self._write_json, daemon=True).start()

        # Ghi lên Google Sheets (nếu có cấu hình)
        Thread(target=self._write_sheets, args=(record, date_str), daemon=True).start()

        # Trả về chuỗi hiển thị cho UI
        display_str = f"[{time_str}] | Model: {model_name} | Tổng: {total} | Đạt: {passed} | Lỗi: {failed} | Kết quả: {result}"
        return display_str

    def get_today_records(self):
        """
        Lấy danh sách bản ghi của ngày hôm nay

        Returns:
            list: Danh sách các chuỗi hiển thị
        """
        today = datetime.now().strftime('%Y-%m-%d')
        records = self.data.get(today, [])

        display_list = []
        for rec in records:
            model_name = rec.get('model_name', 'N/A')
            display_str = f"[{rec['time']}] | Model: {model_name} | Tổng: {rec['total']} | Đạt: {rec['passed']} | Lỗi: {rec['failed']} | Kết quả: {rec['result']}"
            display_list.append(display_str)

        return display_list

    def cleanup_old_data(self, days=DATA_RETENTION_DAYS):
        """
        Xóa dữ liệu cũ hơn số ngày chỉ định
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')

        keys_to_remove = [date for date in self.data.keys() if date < cutoff_str]

        if keys_to_remove:
            for key in keys_to_remove:
                del self.data[key]
            print(f"[THÔNG BÁO] Đã xóa dữ liệu của {len(keys_to_remove)} ngày cũ")
            Thread(target=self._write_json, daemon=True).start()

    def _get_or_create_worksheet(self, spreadsheet, sheet_name):
        """Lấy worksheet theo tên, nếu chưa có thì tạo mới với header."""
        try:
            return spreadsheet.worksheet(sheet_name)
        except Exception:
            # Tạo mới nếu không tồn tại
            new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
            headers = ["Timestamp", "Ngày", "Thời gian", "Tổng", "Đạt", "Lỗi", "Kết quả", "Model AI"]
            new_sheet.append_row(headers)
            # Định dạng header (bold)
            try:
                new_sheet.format("A1:H1", {"textFormat": {"bold": True}})
            except: pass
            return new_sheet

    def _init_gspread(self):
        """Kết nối Google Sheets bằng Service Account."""
        if not self.sheets_status['enabled']:
            return

        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            self._gs_spreadsheet = client.open_by_key(SPREADSHEET_ID)
            
            # Thay vì mở 1 sheet cố định, chúng ta sẽ mở theo ngày khi cần ghi
            self._set_sheet_status(enabled=True, connected=True, error_code='CONNECTED', last_error='')
            print("[THÔNG BÁO] Đã kết nối Google Sheets thành công.")
            
            # Thử đẩy hàng chờ ngay khi kết nối
            Thread(target=self._flush_pending_queue, daemon=True).start()
            
        except Exception as e:
            message = str(e)
            error_code = 'AUTH_ERROR'
            if '403' in message or 'permission' in message.lower():
                error_code = 'PERMISSION_DENIED'
                message = f'Quyền truy cập bị từ chối. Hãy chia sẻ Sheet cho email Service Account.'
            self._set_sheet_status(enabled=True, connected=False, error_code=error_code, last_error=message)
            self._gs_spreadsheet = None
            print(f"[LỖI SHEETS] Kết nối thất bại: {message}")

    def _flush_pending_queue(self):
        """Đẩy toàn bộ hàng chờ lên Sheets theo nhóm ngày, tránh lỗi Quota"""
        if not hasattr(self, '_gs_spreadsheet') or not self._gs_spreadsheet or not self._pending_queue:
            return 0

        success_count = 0
        try:
            # Phân nhóm hàng chờ theo ngày (giả định cột thứ 2 là ngày dạng DD/MM/YYYY)
            data_by_date = {}
            for row in self._pending_queue:
                date_key = row[1].replace("/", "-") # Chuyển thành tên Tab 15-05-2026
                if date_key not in data_by_date:
                    data_by_date[date_key] = []
                data_by_date[date_key].append(row)

            # Gửi từng nhóm lên các Tab tương ứng
            for date_key, rows in data_by_date.items():
                sheet = self._get_or_create_worksheet(self._gs_spreadsheet, date_key)
                sheet.append_rows(rows) # Gửi hàng loạt (Batch update)
                success_count += len(rows)
            
            # Xóa hàng chờ sau khi thành công
            self._pending_queue.clear()
            self._save_pending_queue()
            self._update_pending_queue_size()
            print(f"[THÔNG BÁO] Đã đồng bộ hàng loạt {success_count} bản ghi lên các Tab ngày.")
            
        except Exception as e:
            msg = str(e)
            self._set_sheet_status(enabled=True, connected=False, error_code='FLUSH_ERROR', last_error=msg)
            print(f"[LỖI SHEETS] Lỗi đồng bộ hàng loạt: {msg}")
        return success_count

    def _write_sheets(self, record, date_str):
        """Ghi dữ liệu lên Tab theo ngày tương ứng"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            display_date = date_obj.strftime('%d/%m/%Y')
            sheet_name = date_obj.strftime('%d-%m-%Y')

            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                display_date,
                record['time'],
                record['total'],
                record['passed'],
                record['failed'],
                record['result'],
                record.get('model_name', 'N/A')
            ]

            if not self.sheets_status['enabled']:
                return

            if not hasattr(self, '_gs_spreadsheet') or self._gs_spreadsheet is None:
                self._init_gspread()

            if hasattr(self, '_gs_spreadsheet') and self._gs_spreadsheet:
                # Nếu có hàng chờ cũ, ưu tiên đẩy hết trước (Batch)
                if self._pending_queue:
                    self._pending_queue.append(row)
                    self._flush_pending_queue()
                else:
                    # Ghi trực tiếp vào Tab ngày
                    sheet = self._get_or_create_worksheet(self._gs_spreadsheet, sheet_name)
                    sheet.append_row(row)
            else:
                raise Exception("Chưa có kết nối Spreadsheet")

        except Exception as e:
            message = str(e)
            print(f"[LỖI SHEETS] Tạm lưu vào hàng chờ: {message}")
            if 'row' in locals():
                self._pending_queue.append(row)
                self._save_pending_queue()
                self._update_pending_queue_size()
            if self.sheets_status['enabled']:
                self._set_sheet_status(enabled=True, connected=False, error_code='WRITE_ERROR', last_error=message)
            else:
                self._set_sheet_status(enabled=False, connected=False, error_code=self.sheets_status.get('error_code', 'DISABLED'), last_error=self.sheets_status.get('last_error', message))

    def get_all_records_as_list(self, days_back=90):
        """Trả về list các bản ghi từ JSON local, lọc theo số ngày"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        all_records = []
        # Sắp xếp ngày mới nhất trước
        sorted_dates = sorted(self.data.keys(), reverse=True)
        
        for d_str in sorted_dates:
            if d_str < cutoff_str:
                continue
                
            date_obj = datetime.strptime(d_str, '%Y-%m-%d')
            display_date = date_obj.strftime('%d/%m/%Y')
            
            # Sắp xếp giờ mới nhất trước trong cùng một ngày
            day_records = sorted(self.data[d_str], key=lambda x: x['time'], reverse=True)
            
            for rec in day_records:
                item = rec.copy()
                item['date'] = display_date
                all_records.append(item)
                
        return all_records

    def get_available_dates(self):
        """Trả về list ngày có dữ liệu (YYYY-MM-DD), mới nhất trước"""
        return sorted(self.data.keys(), reverse=True)

    def get_available_models(self):
        """Trả về danh sách các Model AI duy nhất đã từng xuất hiện trong dữ liệu."""
        models = set()
        for date_records in self.data.values():
            for record in date_records:
                model_name = record.get('model_name')
                if model_name:
                    models.add(model_name)
        return sorted(list(models))

    def get_filtered_data(self, date_filter=None, model_filter=None):
        """Lấy dữ liệu từ local JSON và lọc theo ngày/model."""
        all_records = []
        
        # 1. Xác định tập ngày cần quét
        if date_filter:
            target_dates = [date_filter] if date_filter in self.data else []
        else:
            # Nếu không lọc ngày, mặc định lấy 90 ngày gần nhất
            cutoff_date = datetime.now() - timedelta(days=90)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            target_dates = [d for d in self.data.keys() if d >= cutoff_str]
            
        # Sắp xếp ngày mới nhất trước
        target_dates = sorted(target_dates, reverse=True)
        
        for d_str in target_dates:
            # Sắp xếp giờ mới nhất trước trong cùng một ngày
            day_records = sorted(self.data[d_str], key=lambda x: x['time'], reverse=True)
            
            for rec in day_records:
                # Lọc theo model (nếu có yêu cầu)
                if model_filter and rec.get('model_name') != model_filter:
                    continue
                    
                item = rec.copy()
                item['date'] = d_str
                all_records.append(item)
                
        return all_records

    def get_summary_stats(self, date_filter=None):
        """Thống kê từ dữ liệu local"""
        total = 0
        ok = 0
        ng_l = 0
        ng_h = 0
        missing = 0
        
        # Xác định tập ngày cần quét
        target_dates = [date_filter] if date_filter and date_filter in self.data else self.data.keys()
        
        for d_str in target_dates:
            for rec in self.data.get(d_str, []):
                total += 1
                res = rec.get('result', '')
                if res == 'OK':
                    ok += 1
                elif res == 'NG_L':
                    ng_l += 1
                elif res == 'NG_H':
                    ng_h += 1
                elif res == 'MISSING':
                    missing += 1
        
        ng = ng_l + ng_h + missing
        rate = (ok / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'ok': ok,
            'ng_l': ng_l,
            'ng_h': ng_h,
            'missing': missing,
            'ng': ng,
            'rate': round(rate, 1)
        }

    def _load_pending_queue(self):
        """Load hàng chờ dữ liệu chưa gửi được (nếu có)"""
        if os.path.exists(self.pending_queue_file):
            try:
                with open(self.pending_queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_pending_queue(self):
        """Lưu hàng chờ ra file để tránh mất dữ liệu"""
        try:
            with open(self.pending_queue_file, 'w', encoding='utf-8') as f:
                json.dump(self._pending_queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LỖI] Không thể lưu hàng chờ: {e}")

    def export_to_excel(self, filepath, date_filter=None, model_filter=None):
        """
        Xuất dữ liệu ra file Excel với merge cell cho cột Ngày

        Args:
            filepath: Đường dẫn file Excel để lưu
            date_filter: Nếu là chuỗi 'YYYY-MM-DD', chỉ xuất ngày đó. 
                        Nếu là None, xuất toàn bộ dữ liệu.
            model_filter: Nếu có, chỉ xuất các bản ghi của model này.

        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        if not OPENPYXL_AVAILABLE:
            print("[LỖI] Thư viện openpyxl chưa được cài đặt!")
            return False

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Kết quả phát hiện"

            # Định dạng header
            headers = ['STT', 'Ngày', 'Thời gian', 'Tổng số viên', 'Viên đạt', 'Viên lỗi', 'Kết quả', 'Model AI']
            header_font = Font(bold=True, color='FFFFFF')
            header_fill_color = '006666'  # Màu teal
            header_alignment = Alignment(horizontal='center', vertical='center')
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Ghi header
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = thin_border
                # Đặt màu nền cho header
                from openpyxl.styles import PatternFill
                cell.fill = PatternFill(start_color=header_fill_color, end_color=header_fill_color, fill_type='solid')

            # Ghi dữ liệu
            row_num = 2
            stt = 1

            # Biến đếm số lần từng trạng thái kết quả (5 trạng thái)
            count_ok = 0
            count_ng_l = 0
            count_ng_h = 0
            count_missing = 0
            count_wait = 0

            # Lọc các ngày cần xuất
            if date_filter:
                if date_filter in self.data:
                    sorted_dates = [date_filter]
                else:
                    sorted_dates = []
            else:
                # Sắp xếp các ngày theo thứ tự
                sorted_dates = sorted(self.data.keys())

            for date_str in sorted_dates:
                records = self.data[date_str]
                if not records:
                    continue

                # Chuyển đổi định dạng ngày từ YYYY-MM-DD sang DD/MM/YYYY
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                display_date = date_obj.strftime('%d/%m/%Y')

                # Lọc records theo model_filter
                filtered_records = []
                for r in records:
                    if model_filter and r.get('model_name') != model_filter:
                        continue
                    filtered_records.append(r)
                
                if not filtered_records:
                    continue

                start_row = row_num
                for i, rec in enumerate(filtered_records):
                    current_row = row_num
                    ws.cell(row=current_row, column=1, value=stt).alignment = header_alignment
                    ws.cell(row=current_row, column=1).border = thin_border

                    # Chỉ ghi ngày vào hàng đầu tiên của ngày đó (trong tập đã lọc)
                    if i == 0:
                        ws.cell(row=current_row, column=2, value=display_date).alignment = header_alignment
                        ws.cell(row=current_row, column=2).border = thin_border
                    else:
                        ws.cell(row=current_row, column=2).border = thin_border

                    ws.cell(row=current_row, column=3, value=rec['time']).alignment = header_alignment
                    ws.cell(row=current_row, column=3).border = thin_border

                    ws.cell(row=current_row, column=4, value=rec['total']).alignment = header_alignment
                    ws.cell(row=current_row, column=4).border = thin_border

                    ws.cell(row=current_row, column=5, value=rec['passed']).alignment = header_alignment
                    ws.cell(row=current_row, column=5).border = thin_border

                    ws.cell(row=current_row, column=6, value=rec['failed']).alignment = header_alignment
                    ws.cell(row=current_row, column=6).border = thin_border

                    ws.cell(row=current_row, column=7, value=rec['result']).alignment = header_alignment
                    ws.cell(row=current_row, column=7).border = thin_border

                    ws.cell(row=current_row, column=8, value=rec.get('model_name', 'N/A')).alignment = header_alignment
                    ws.cell(row=current_row, column=8).border = thin_border

                    # Đếm số lần từng trạng thái kết quả
                    result_val = rec.get('result', '')
                    if result_val == 'OK':
                        count_ok += 1
                    elif result_val == 'NG_L':
                        count_ng_l += 1
                    elif result_val == 'NG_H':
                        count_ng_h += 1
                    elif result_val == 'MISSING':
                        count_missing += 1
                    elif result_val == 'WAIT':
                        count_wait += 1

                    stt += 1
                    row_num += 1

                end_row = row_num - 1

                # Merge cell cột Ngày nếu có nhiều hơn 1 bản ghi trong ngày
                if end_row > start_row:
                    ws.merge_cells(start_row=start_row, start_column=2, end_row=end_row, end_column=2)
                    # Căn trung tâm cho ô đã gộp
                    ws.cell(row=start_row, column=2).alignment = Alignment(horizontal='center', vertical='center')

            # === PHẦN TỔNG HỢP KẾT QUẢ Ở CUỐI ===
            if row_num > 2:  # Chỉ thêm nếu có dữ liệu
                from openpyxl.styles import PatternFill
                
                summary_font = Font(bold=True, size=11)
                summary_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')  # Vàng nhạt
                
                # --- HÀNG 1: Tiêu đề "TỔNG HỢP KẾT QUẢ" + OK + NG_L ---
                row1 = row_num
                ws.merge_cells(start_row=row1, start_column=1, end_row=row1, end_column=3)
                cell_title = ws.cell(row=row1, column=1, value="TỔNG HỢP KẾT QUẢ")
                cell_title.font = Font(bold=True, size=12)
                cell_title.alignment = Alignment(horizontal='center', vertical='center')
                cell_title.border = thin_border
                cell_title.fill = summary_fill

                # OK
                cell_ok = ws.cell(row=row1, column=4, value=f"OK: {count_ok}")
                cell_ok.font = summary_font
                cell_ok.alignment = Alignment(horizontal='center', vertical='center')
                cell_ok.border = thin_border
                cell_ok.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')  # Xanh nhạt

                # NG_L (lỗi nhẹ)
                cell_ng_l = ws.cell(row=row1, column=5, value=f"NG_L: {count_ng_l}")
                cell_ng_l.font = summary_font
                cell_ng_l.alignment = Alignment(horizontal='center', vertical='center')
                cell_ng_l.border = thin_border
                cell_ng_l.fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')  # Vàng nhạt

                # NG_H (lỗi nặng)
                cell_ng_h = ws.cell(row=row1, column=6, value=f"NG_H: {count_ng_h}")
                cell_ng_h.font = summary_font
                cell_ng_h.alignment = Alignment(horizontal='center', vertical='center')
                cell_ng_h.border = thin_border
                cell_ng_h.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')  # Đỏ nhạt

                # MISSING
                cell_miss = ws.cell(row=row1, column=7, value=f"MISSING: {count_missing}")
                cell_miss.font = summary_font
                cell_miss.alignment = Alignment(horizontal='center', vertical='center')
                cell_miss.border = thin_border
                cell_miss.fill = PatternFill(start_color='FFD699', end_color='FFD699', fill_type='solid')  # Cam nhạt

                # --- HÀNG 2: Tổng số lượt kiểm tra ---
                row2 = row_num + 1
                total_count = count_ok + count_ng_l + count_ng_h + count_missing + count_wait
                total_ng = count_ng_l + count_ng_h

                ws.merge_cells(start_row=row2, start_column=1, end_row=row2, end_column=3)
                cell_total_label = ws.cell(row=row2, column=1, value=f"TỔNG LƯỢT: {total_count}")
                cell_total_label.font = Font(bold=True, size=12)
                cell_total_label.alignment = Alignment(horizontal='center', vertical='center')
                cell_total_label.border = thin_border
                cell_total_label.fill = summary_fill

                # Tổng đạt
                cell_dat = ws.cell(row=row2, column=4, value=f"Đạt: {count_ok}")
                cell_dat.font = summary_font
                cell_dat.alignment = Alignment(horizontal='center', vertical='center')
                cell_dat.border = thin_border
                cell_dat.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')

                # Tổng lỗi (NG_L + NG_H)
                cell_loi = ws.cell(row=row2, column=5, value=f"Lỗi: {total_ng}")
                cell_loi.font = summary_font
                cell_loi.alignment = Alignment(horizontal='center', vertical='center')
                cell_loi.border = thin_border
                cell_loi.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')

                # Tỷ lệ đạt
                if total_count > 0:
                    ty_le = (count_ok / total_count) * 100
                    ty_le_str = f"Tỷ lệ đạt: {ty_le:.1f}%"
                else:
                    ty_le_str = "Tỷ lệ đạt: --"
                ws.merge_cells(start_row=row2, start_column=6, end_row=row2, end_column=7)
                cell_tyle = ws.cell(row=row2, column=6, value=ty_le_str)
                cell_tyle.font = Font(bold=True, size=11, color='006666')
                cell_tyle.alignment = Alignment(horizontal='center', vertical='center')
                cell_tyle.border = thin_border
                cell_tyle.fill = summary_fill

            # Điều chỉnh độ rộng cột
            column_widths = [6, 15, 12, 15, 12, 12, 15, 25]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[chr(64 + i)].width = width

            # Lưu file
            wb.save(filepath)
            print(f"[THÔNG BÁO] Đã xuất file Excel: {filepath}")
            return True

        except Exception as e:
            print(f"[LỖI] Không thể xuất Excel: {e}")
            return False


# Singleton instance để sử dụng trong toàn ứng dụng
_data_manager_instance = None


def get_data_manager():
    """
    Lấy instance của DataManager (Singleton pattern)

    Returns:
        DataManager: Instance duy nhất của DataManager
    """
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = DataManager()
    return _data_manager_instance
