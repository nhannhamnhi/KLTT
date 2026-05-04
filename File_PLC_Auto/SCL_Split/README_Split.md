# SCL Split Blocks (for TIA copy limit)

## 1) Block list
- `FB_Auto_Main.scl` : main state machine
- `FC_EdgesAndMode.scl` : edge detection + mode/run latch
- `FC_AI_Handshake.scl` : SS0 trigger + DataReady consume
- `FB_FIFO10.scl` : queue memory (10 items)
- `FC_Cylinder1_Seq.scl` : XL1 sequence by LS1
- `FC_Cylinder2_Seq.scl` : XL2 sequence by LS2
- `FC_FaultManager.scl` : central fault decision
- `FC_ClassifyRule.scl` : optional classifier rule helper
- `OB1_Call_Split_Example.scl` : OB1 call template

## 2) Input conditions per block

### FC_EdgesAndMode
- Requires raw hardware inputs: `btAuto`, `btManual`, `StartStop`, `SS0`, `SS1`, `SS2`
- Requires memory vars (`prev*`, `runLatch`) passed by `VAR_IN_OUT`

### FC_AI_Handshake
- Requires edge signals from FC_EdgesAndMode: `ss0Rise`, `ss0Fall`
- Requires PLC<->PC values: `PC_DataReady`, `PC_KetQua`
- Requires current queue count to protect overflow

### FB_FIFO10
- `Push` and `PushValue` from handshake logic
- `Pop` from downstream classification completion

### FC_Cylinder1_Seq / FC_Cylinder2_Seq
- `StartAction` pulse from main state machine
- `LS1` / `LS2` real feedback inputs

### FC_FaultManager
- Receives all error flags and outputs one `ErrorActive`, `ErrorCode`

### FB_Auto_Main
- Integrates all blocks and drives final outputs

## 3) Integration order in OB1
1. Call `FB_Auto_Main` only (recommended)
2. Keep all split internals inside the FB
3. Map only physical tags + DB_GET/DB_PUT at OB1 level

