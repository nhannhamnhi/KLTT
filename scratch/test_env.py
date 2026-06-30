import sys
import os

print("Setting environment variables...")
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OPENVINO_DEVICE"] = "CPU"

print("Importing torch...")
try:
    import torch
    print("Torch imported successfully")
    print("Torch version:", torch.__version__)
except Exception as e:
    print("Torch error:", e)

print("Done")
