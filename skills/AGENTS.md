# Project Conventions

## Folder Structure (Root)

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
skills/                 ← skills, rules, agents, custom tools
```

## Skills Folder Structure

```
skills/
├── AGENTS.md                  ← tài liệu này (project conventions)
├── .clinerules/               ← VS Code .clinerules (high-priority rules)
│   └── caveman.md             ← caveman mode rule
├── rules/                      ← custom agent rules & skills
│   └── caveman_1.md           ← caveman skill v1
└── agents/                     ← custom agents definitions (tạm)
    └── [agent-name].md
```

## Rules

- **Không để file mới ở root** — luôn đặt đúng thư mục trên
- **File MD tạm khi plan** → `scratch/plans/` hoặc `scratch/specs/`
- **File MD hoàn chỉnh** → `docs/`
- **Skills & Rules** → `skills/` (`.clinerules/` cho high-priority, `rules/` cho regular)
- **Custom Agents** → `skills/agents/` (tài liệu định nghĩa agent)
- `scratch/` bị gitignore, không commit
