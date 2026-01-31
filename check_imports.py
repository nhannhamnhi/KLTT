import sys
print("Checking imports...")
try:
    import cv2
    print("cv2 imported successfully. Version:", cv2.__version__)
except ImportError as e:
    print("cv2 ImportError:", e)
except Exception as e:
    print("cv2 Exception:", e)

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    print("PyQt5 imported successfully.")
except ImportError as e:
    print("PyQt5 ImportError:", e)

try:
    import torch
    print("torch imported successfully. Version:", torch.__version__)
except ImportError as e:
    print("torch ImportError:", e)
except Exception as e:
    print("torch Exception:", e)

try:
    from ultralytics import YOLO
    print("ultralytics imported successfully.")
except ImportError as e:
    print("ultralytics ImportError:", e)
