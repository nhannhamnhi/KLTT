@echo off
set CUDA_VISIBLE_DEVICES=-1
set YOLO_OFFLINE=True
set OPENVINO_DEVICE=CPU
set KMP_DUPLICATE_LIB_OK=TRUE
echo [LAUNCHER] Starting PharmaScan...
.venv\Scripts\python.exe -u src\ui\finish.py
