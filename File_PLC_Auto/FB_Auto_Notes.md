# FB_Auto Integration Notes

## 1) Required mapping
- `DB_GET` (PC -> PLC):
  - `PC_KetQua` (INT)
  - `PC_DataReady` (BOOL)
- `DB_PUT` (PLC -> PC):
  - `PLC_Auto` (BOOL)
  - `PLC_Manual` (BOOL)
  - `PLC_Running` (BOOL)
  - `PLC_TriggerReq` (BOOL)

## 2) I/O used by the FB
- Inputs:
  - `btAuto`, `btManual`, `StartStop`
  - `SS0`, `SS1`, `SS2`
  - `LS1`, `LS2`
- Outputs:
  - `Conveyor` (`%Q0.0`)
  - `Cylinder1` (`%Q0.1`)
  - `Cylinder2` (`%Q0.2`)

## 3) AI handshake implemented
- `SS0` rising edge -> `PLC_TriggerReq := TRUE`
- `PC_DataReady = TRUE` is consumed exactly once per SS0 cycle
- `PLC_TriggerReq` is reset only when `SS0` falls

## 4) Result mapping
- `0 = WAIT`
- `1 = OK`
- `2 = NG_L`
- `3 = NG_H`
- `4 = MISSING`

## 5) Error codes
- `101`: AI timeout while waiting result
- `102`: SS0 stuck high timeout
- `201`: LS1 timeout during cylinder1 sequence
- `202`: LS2 timeout during cylinder2 sequence
- `301`: FIFO overflow
- `302..306`: FIFO underflow/state mismatch
- `401`: Invalid `PC_KetQua` value

## 6) Behavior summary
- Conveyor runs in Auto, but is temporarily stopped during active cylinder classification states.
- `NG_L` is handled at `SS1` with `Cylinder1`.
- `NG_H` and `MISSING` are handled at `SS2` with `Cylinder2`.
- Any critical fault -> `SAFE_STOP`:
  - `Conveyor OFF`
  - `Cylinder1 OFF`
  - `Cylinder2 OFF`
  - `PLC_TriggerReq OFF`
- Manual fault reset input: `ResetFault` (rising edge).
