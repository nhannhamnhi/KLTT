# Project Conventions

## Folder Structure

```
src/{ai,plc,data,ui}/   ← source code Python
ui/forms/               ← file .ui Qt Designer
assets/                 ← ảnh tĩnh, icon
models/                 ← model AI (YOLOv8, OpenVINO)
data/                   ← dữ liệu runtime (JSON, Excel)
docs/                   ← tài liệu MD hoàn chỉnh
plc/SCL/                ← code PLC Siemens
scripts/                ← script tiện ích
scratch/plans/          ← kế hoạch, todo (tạm)
scratch/specs/          ← draft spec (tạm)
scratch/debug/          ← ghi chú debug (tạm)
```

## Rules

- **Không để file mới ở root** — luôn đặt đúng thư mục trên
- **File MD tạm khi plan** → `scratch/plans/` hoặc `scratch/specs/`
- **File MD hoàn chỉnh** → `docs/`
- `scratch/` bị gitignore, không commit
