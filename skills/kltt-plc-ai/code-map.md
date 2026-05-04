# Code Map - KLTT Project

## Key Python files
- `File_MainProgram/finish.py`
  - Main UI controller
  - Camera thread
  - PLC polling integration
  - Auto/Manual UI behavior
- `File_MainProgram/Class_dataplc.py`
  - Snap7 connector
  - DB read/write functions
  - Polling thread with debounce behavior
- `File_MainProgram/data_manager.py`
  - Runtime record save/load
  - Excel export

## PLC data exchange model
- `DB_GET` (PC -> PLC)
  - `PC_KetQua` (INT): 0/1/2/3
  - `PC_DataReady` (BOOL)
  - Manual commands: conveyor/cylinder controls
- `DB_PUT` (PLC -> PC)
  - `PLC_Auto` (BOOL)
  - `PLC_Manual` (BOOL)
  - `PLC_Running` (BOOL)
  - `PLC_TriggerReq` (BOOL)
  - `PLC_Sensor1` / `PLC_Sensor2` (BOOL)

## I/O summary (from project screenshots)
- Outputs:
  - `Conveyor` `%Q0.0`
  - `Cylinder1` `%Q0.1`
  - `Cylinder2` `%Q0.2`
- Inputs:
  - `btAuto` `%I0.1`
  - `btManual` `%I0.2`
  - `SS0` `%I0.3`
  - `SS1` `%I0.4`
  - `SS2` `%I0.5`
  - `LS_1` `%I0.6`
  - `LS_2` `%I0.7`
  - `Start-Stop` `%I0.0`

## Auto-mode assumptions
1. Product path: `SS0 -> SS1 -> SS2`
2. `NG_H` still passes `SS1` before `SS2`
3. No encoder feedback for conveyor speed
4. PWM speed control is external, independent from PLC
5. LS signals are used to complete cylinder extend/retract cycle

## Preferred technical defaults
- Use state machine for Auto logic
- Use FIFO when conveyor carries multiple products
- Use safe stop on queue mismatch / timeout
- Keep runtime data out of git-tracked files

