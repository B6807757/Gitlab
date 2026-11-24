# Lab 04 — CE Amplifier Simulator v1 · Design

วันที่: 24 พฤศจิกายน 2026
สถานะ: ฉบับปรับหลัง builder check — รออนุมัติ (ยังไม่เริ่มเขียนโค้ด)

## 1. เจตนาและเหตุผล

ต่อยอด Flask web app ของ Lab 3 (`B6807757/Gitlab`) ให้เป็น Common-Emitter Amplifier
Simulator รุ่นแรกตามใบงาน ENG29 2121 Lab 04 โดย **คง DC Bias 3 โหมดและเทสต์เดิมไว้ทั้งหมด**
แล้วเพิ่มการจำลอง ngspice จริง 3 แบบสำหรับวงจร CE Voltage Divider อ้างอิงหนึ่งวงจร

เหตุผล: ใบงานต้องการให้นักศึกษาเห็นความต่างระหว่าง "สมการประมาณ" (analytical) กับ
"ผลจาก simulator จริง" (SPICE) และพิสูจน์ที่มาของตัวเลข/กราฟได้ ไม่ใช่ภาพประกอบ

## 2. เป้าหมาย / ไม่ใช่เป้าหมาย

### เป้าหมาย
1. DC Bias 3 โหมด (divider / fixed / emitter) ยังทำงานและผลไม่เปลี่ยน (regression)
2. วงจร CE Voltage Divider อ้างอิงหนึ่งวงจร รัน ngspice จริงได้ 3 analysis:
   - `.op` → VB, VE, VC, VCE, IC จาก output จริง
   - `.ac` → ขนาดอัตราขยาย (V/V และ dB) และเฟส (องศา) เทียบความถี่
   - `.tran` → Vin/Vout เทียบเวลา พร้อมแอมพลิจูด/ความถี่ที่ผู้ใช้ตั้ง
3. แสดงหน่วย SI, ชื่อ analysis, engine + version, ชื่อ BJT model และ netlist ที่รันจริง
4. แยกผล SPICE ออกจากผล analytical อย่างชัดเจน (คนละหัวข้อ คนละป้าย)
5. Error path ครบ: ไม่พบ ngspice / timeout / exit ไม่เป็น 0 / parse ไม่ได้ / input ผิด
   → ต้องไม่มีกราฟหรือค่าค้างจากรอบก่อนหน้า และต้องไม่ขึ้นสถานะสำเร็จ
6. README อัปเดตวิธีติดตั้ง ngspice + วิธีรัน + สภาพแวดล้อมที่ทดสอบ
7. `docs/validation.md` เพิ่มตาราง B1–B8 ตามใบงาน พร้อมหลักฐานจริง

### ไม่ใช่เป้าหมาย (ตามใบงาน)
- Drag-and-drop editor หรือต่อวงจรอิสระ
- AC simulation ของ Fixed/Emitter bias
- FET, การเขียน SPICE solver เอง, animated overlay บนวงจร
- คำนวณ Saturation/Cutoff ด้วยสมการประมาณแทน SPICE
- Deploy ให้ผู้ใช้ภายนอก
- Emitter bypass capacitor (CE) — ใบงานบอกเป็นงานต่อยอด

### Anti-goals (ถือว่าล้มเหลวแม้หน้าจอสวย)
- กราฟที่ hard-code หรือ mock data ที่อ้างว่าเป็นผล ngspice
- แสดงผลรอบเก่าพร้อมสถานะ Success เมื่อรอบใหม่ล้มเหลว
- ทำให้ DC Bias 3 โหมดหรือเทสต์เดิมเสีย
- ซ่อน error ของ ngspice

## 3. ข้อจำกัดของสภาพแวดล้อม (ตรวจแล้ว)

| รายการ | สถานะจริง |
|---|---|
| Repo | `C:\Users\B6807757\Gitlab`, `main` @ `cffa15f`, clean |
| โมดูล analytical | `bjt.py` (ไม่ใช่ `dc_bias.py` ตามใบงาน — ใช้ของเดิมตามหลัก reuse) |
| Python | 3.12.7 |
| Flask | **ยังไม่ติดตั้ง** — จะติดตั้งตอนเริ่มสร้าง (เป็น dependency เดิมใน `requirements.txt`) |
| ngspice | **ngspice-33 (64-bit)** ที่ `%LOCALAPPDATA%\Programs\ngspice\ngspice-33-w7\ngspice.exe`; ยังไม่อยู่ใน PATH ของ service ที่รัน OpenCode |
| Node / npx | v24.14.0 / 11.9.0 (ใช้ติดตั้ง Impeccable ได้) |
| Starter Kit | **ไม่มี** — ผู้ใช้สั่งข้าม; ใช้การ์ด 2N3904 ที่เผยแพร่และอ้างอิงได้ (ผู้ใช้อนุมัติแล้ว) |
| Playwright MCP | **ไม่ติดตั้ง** — ผู้ใช้เลือกใช้ OpenCode Browser และบันทึก NOT RUN ตามใบงาน |
| Impeccable | ยังไม่ติดตั้ง — จะติดตั้งตอนขั้น UI (ดู §5.9) |

### ข้อจำกัดของ ngspice-33 ที่ทดสอบแล้ว
- `.print ac vm(5) vm(6) vp(6)` บนบรรทัดเดียว: **vp ถูกตัดทิ้ง** ต้องแยก `.print ac vp(5) vp(6)` อีกบรรทัด
- `vp()` คืนค่าเป็น **radian** ต้องแปลงเป็นองศาใน Python
- `.op` พิมพ์โหนดเป็น `V(n)` และกระแส `ic` ในบล็อก `device q1`
- ไม่มี `init file` (warning ตอนเริ่ม) — ไม่กระทบผลรัน
- batch mode ทำงานเสร็จใน ~0.05 s ต่อรอบ

## 4. แนวทางที่พิจารณา

**A. Server-rendered ไม่ใช้ JavaScript (เลือกแล้ว)**
- Jinja + inline SVG ที่สร้างจาก Python, form POST, โหลดหน้าใหม่ต่อการรัน
- ข้อดี: เข้ากับ Lab 3, เทสต์ด้วย Flask test client ได้, ไม่มี dependency ใหม่, ตรวจย้อนกลับได้ง่าย
- ข้อเสีย: ต้องเขียนโค้ดวาดกราฟเอง, ไม่ interactive

**B. JSON + Chart.js (ไม่เลือก)**
- กราฟสวยและซูมได้ แต่เพิ่ม JS/library, เทสต์ฝั่ง server ยากขึ้น และเสี่ยงกราฟไม่มาจากผลรันจริง

**C. matplotlib (ไม่เลือก)**
- เขียนกราฟง่าย แต่เพิ่ม dependency หนักและเกินความจำเป็น

## 5. การออกแบบ

### 5.1 โครงสร้างไฟล์

```
app.py                      # คงของเดิม + route /simulator (GET/POST)
bjt.py                      # ไม่แก้ (analytical reference ของ Lab 3)
spice_engine.py             # ใหม่: netlist, subprocess, parser, error
plots.py                    # ใหม่: สร้าง SVG (Bode, transient)
templates/simulator.html    # ใหม่: หน้าจำลอง (ไม่แตะ index.html)
static/style.css            # เพิ่ม style ของหน้าจำลอง (ไม่แก้ของเดิม)
test_spice_engine.py        # ใหม่
test_plots.py               # ใหม่
test_simulator_app.py       # ใหม่
README.md                   # เพิ่มหัวข้อ Lab 04
docs/validation.md          # เพิ่ม B1–B8
```

เทสต์เดิมอยู่ที่ root (`test_*.py`) และรันด้วย `python -m unittest -v`
จึงวางเทสต์ใหม่ที่ root ชื่อเดียวกันเพื่อให้ discovery เดิมยังทำงาน (ไม่ย้ายเทสต์เดิม)

### 5.2 วงจรอ้างอิง (ค่าตั้งต้นตามใบงาน §06)

| รายการ | ค่า |
|---|---|
| VCC / R1 / R2 | 12 V / 100 kΩ / 22 kΩ |
| RC / RE / RL | 2.2 kΩ / 1 kΩ / 10 kΩ |
| Cin / Cout | 10 µF / 10 µF |
| Source | 10 mV **peak** / 1 kHz (SIN) |
| β, VBE (analytical only) | 150, 0.70 V (ค่า default เดิมของโหมด Divider ใน Lab 3) |

โหนด: `1`=VCC, `2`=base, `3`=collector, `4`=emitter, `5`=source (ก่อน Cin), `6`=output (หลัง Cout)

```spice
* ENG29 2121 Lab 04 - CE voltage-divider reference
VCC 1 0 DC 12
R1  1 2 100k
R2  2 0 22k
RC  1 3 2.2k
RE  4 0 1k
Q1  3 2 4 Q2N3904
CIN 5 2 10u
COUT 3 6 10u
RL  6 0 10k
VIN 5 0 DC 0 AC 1 SIN(0 10m 1k)
.model Q2N3904 NPN(IS=1E-14 VAF=100 BF=300 IKF=0.4 XTB=1.5 BR=4
+ CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12
+ ITF=1 VTF=2 XTF=3)
```

ทุกค่าตัวเลขถูก format ด้วย Python (ไม่ต่อ string จาก input ดิบ) และตรวจช่วงก่อนสร้าง netlist
ไม่ใช้ `shell=True`; เรียกด้วย list ของ argument; ทำงานใน `tempfile.TemporaryDirectory()`;
`timeout` 20 วินาที; เก็บ log ไว้แสดงเป็นหลักฐาน

### 5.3 BJT model (ผู้ใช้อนุมัติแล้ว)

ใช้การ์ด **2N3904 (mfg=Philips)** จาก Standard.bjt ที่เผยแพร่ใน LTspice
(<https://ltwiki.org/index.php?title=Standard.bjt>) ระบุแหล่งที่มาใน README,
`docs/validation.md` และในหน้า `/simulator`

```
.model Q2N3904 NPN(IS=1E-14 VAF=100 BF=300 IKF=0.4 XTB=1.5 BR=4
+ CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12
+ ITF=1 VTF=2 XTF=3)
```

**ผลกระทบที่ต้องแสดงบนหน้าจอ:** β ในฟอร์มใช้กับ analytical เท่านั้น
ผล SPICE ใช้ β จากโมเดล (BF=300) — ต้องมีข้อความอธิบาย ไม่ให้ผู้ใช้เข้าใจผิดว่าปรับ β แล้ว SPICE เปลี่ยน

### 5.4 คำสั่งวิเคราะห์และพารามิเตอร์

| Analysis | Directive | หมายเหตุ |
|---|---|---|
| DC | `.op` | capacitor เปิดวงจรโดยธรรมชาติ |
| AC | `.ac dec 20 1 100meg` | ครอบคลุม fL และช่วง midband |
| AC print | `.print ac vm(5) vm(6)` + `.print ac vp(5) vp(6)` | ต้องแยกบรรทัด (ข้อจำกัด ngspice-33) |
| Transient | `.tran {step} {stop}` | คำนวณจากความถี่ต้นทาง (ด้านล่าง) |
| Transient print | `.print tran v(5) v(6)` | |

**Transient window (เป็น call ของผู้สร้าง):**
- `stop = min(max(5 ms, 3/f), 200 ms)`
- `step = min(stop/2000, 1/(50·f))` เพื่อให้ ≥ 50 จุดต่อคาบ (จำนวนจุดสูงสุด ~25,000 ที่ 100 kHz)
- หน้าจอระบุ "หน้าต่างเวลา = 5 ms หรือ 3 คาบ (แล้วแต่ค่าที่มากกว่า)"
- ที่ 1 kHz (B5): 5 ms = 5 คาบ, step 2.5 µs

### 5.5 การอ่านผล (parser)

ใช้ text output จาก `ngspice -b -o run.log circuit.cir` (ไม่ parse raw ไบนารี)

- **DC:** อ่าน `V(1..4)` จากส่วน node voltage และ `ic` ของ `q1` จากบล็อก device
  → VB=V(2), VE=V(4), VC=V(3), VCE=VC−VE
- **AC:** อ่านตาราง 3 คอลัมน์ (index, frequency, value) จากสองตาราง
  → gain = vm(6)/vm(5), gain_dB = 20·log10(gain), phase = wrap_deg(deg(vp(6)) − deg(vp(5)))
  → normalize ไป (−180, 180]
- **Transient:** อ่านคู่ (time, v(5), v(6))
- **Cutoff:** หา −3 dB จาก gain สูงสุดใน sweep; ถ้าไม่มีจุดตัด → "not determined in sweep range"
  (ห้ามสร้างตัวเลขขึ้นเอง)
- **Phase inversion:** ตรวจสหสัมพันธ์ของ (Vin−mean) กับ (Vout−mean) ในช่วงท้าย 50% ของ window
  → ค่าลบ = กลับเฟส; รายงาน peak-to-peak ของทั้งสองสัญญาณตลอด window
- ทุก parser ต้อง fail ชัดเจนถ้าจำนวนแถว/คอลัมน์ไม่ครบ หรือค่าที่จำเป็นหายไป
  (`SpiceParseError`) — ห้ามคืน list ว่างแล้วถือว่าสำเร็จ
- แถวข้อมูลต้องเป็นตัวเลขจริงทุกค่า; ถ้าเจอ `NaN`/`Inf` → error

### 5.6 การเปรียบเทียบ SPICE กับ Analytical

- แสดงสองคอลัมน์แยก: "ngspice (SPICE)" และ "สมการประมาณ (Analytical)"
- Analytical ใช้ `bjt.analyze()` (Thevenin) ด้วย β/VBE จากฟอร์ม
- แสดงผลต่าง (absolute + %) และคำอธิบายว่าต่างเพราะ β/VBE/Early effect/โมเดลไม่เหมือนกัน
- **ไม่มี tolerance แบบ pass/fail** — สถานะ B2 อิงจาก "ngspice รันสำเร็จและอ่านค่าครบ" ไม่ใช่ตัวเลขเท่ากัน
- ถ้า analytical อยู่ใน cutoff/saturation ให้แสดง region และหมายเหตุ ไม่ซ่อน

### 5.7 UI (`/simulator`)

1. ฟอร์มวงจร: VCC, R1, R2, RC, RE, RL, Cin, Cout (รับ suffix k/M/µ) + Source amplitude (mV peak) / frequency (Hz)
2. ฟิลด์ β และ VBE สำหรับ analytical เท่านั้น (มีป้ายกำกับชัด)
3. ปุ่ม Run 3 ปุ่ม: `DC (.op)`, `AC (.ac)`, `Transient (.tran)`
4. กล่องสถานะ: engine + version, model, analysis, เวลารัน, สถานะ Success/Error
5. ผล DC: ตาราง VB/VE/VC/VCE/IC + คอลัมน์ analytical + ผลต่าง
6. ผล AC: Bode 2 ชั้น (ขนาด dB, เฟส องศา) แกน log frequency + ตารางค่าที่ 1 kHz และ fL/fH
7. ผล Transient: กราฟ Vin/Vout (ms, V) + peak-to-peak และสรุปการกลับเฟส
8. `<details>` แสดง netlist และ ngspice log ของรอบนั้น
9. Error: ข้อความ + hint (เช่น ตั้ง `NGSPICE_EXE`) ไม่มีกราฟ/ค่าเก่าค้าง
10. ลิงก์ไป–กลับระหว่าง `/` (Lab 3) และ `/simulator` โดยไม่แก้พฤติกรรมเดิม

กราฟเป็น SVG ที่สร้างจากข้อมูลจริงของรอบนั้น: แกนมี tick/หน่วย, เส้น polyline จากข้อมูล,
legend, และ caption บอก analysis/engine/model — ไม่ใช้ภาพนิ่งหรือค่าคงที่
(ยอมรับเฉพาะกรณีข้อมูลสั้น/แบนที่ยังวาดจากข้อมูลจริง)

### 5.8 การตั้งค่า ngspice

ลำดับค้นหา executable:
1. environment variable `NGSPICE_EXE`
2. `shutil.which("ngspice")`
3. path ที่รู้จักในเครื่องนี้ (`%LOCALAPPDATA%\Programs\ngspice\ngspice-33-w7\ngspice.exe`)

ถ้าไม่พบ → `SpiceEngineNotFound` พร้อมข้อความวิธีตั้งค่า (ไม่ crash หน้า)
แสดง version จาก `ngspice -v` แบบ batch (ทดสอบแล้วว่า ngspice-33 ไม่พิมพ์ version
ด้วย `-v` แบบ batch; จะอ่านจากชื่อไฟล์/โฟลเดอร์หรือ `version` command ใน netlist แทน
และถ้าอ่านไม่ได้ให้แสดง "ngspice (version unknown)")

### 5.9 Impeccable (call ของผู้สร้าง)

ติดตั้งด้วย `npx impeccable install` ใน project scope ตามใบงาน แล้วใช้ `critique`/`polish`
กับหน้า `/simulator` ที่รันจริง โดยแก้เฉพาะ UI (`templates/simulator.html`, `static/style.css`)
และห้ามแตะสูตรคำนวณ/ข้อมูลกราฟ
ถ้าติด interactive prompt หรือติดตั้งไม่สำเร็จ → บันทึก NOT RUN พร้อมเหตุผล แล้วทำ UI polish มือเปล่า
โดยไม่ลดทอนข้อกำหนด SPICE

### 5.10 เทสต์

- `test_spice_engine.py`: netlist ที่สร้าง (ค่าถูกตำแหน่ง/หน่วย/analysis), parser ด้วย log ตัวอย่าง,
  error: ไม่พบ exe, timeout, exit≠0, log ว่าง, parse ไม่ครบ, input นอกช่วง, vp radian→degree
- `test_plots.py`: SVG มี viewBox/แกน/legend/จำนวนจุดตรงกับข้อมูล, จัดการข้อมูล 1 จุด/ว่าง,
  ข้อมูลแบน, ไม่มี hard-code ค่าผลลัพธ์
- `test_simulator_app.py`: GET หน้า, POST ด้วย runner ปลอม (ไม่ต้องมี ngspice), error state,
  ตรวจว่าไม่มีผลเก่าค้างเมื่อล้มเหลว, ตรวจว่าหน้า `/` ยังเหมือนเดิม
- เทสต์เดิมทั้งหมดต้องผ่านเหมือนเดิม
- integration test จริง (เรียก ngspice) แยกและ skip ถ้าไม่พบ engine — รันมือตอน validation

### 5.11 Validation (B1–B8) — เคสที่จะใช้จริง

| Case | Action | เกณฑ์ |
|---|---|---|
| B1 | `/` Fixed 12V/1M/2.2k/β100/0.70; Emitter 12V/1M/2.2k/1k/β100/0.70; Divider 12V/100k/22k/2.2k/1k/β100/0.70 | ตรงค่าอ้างอิง Lab 3 (A1–A5) และสลับโหมดได้ |
| B2 | `/simulator` ค่า default → Run DC | VB/VE/VC/VCE/IC จาก ngspice + model + status |
| B3 | เปลี่ยน RE 1k → 2k → Run DC ซ้ำ | ค่า operating point เปลี่ยนตามผลรัน ไม่ค้างค่าเดิม |
| B4 | Run AC | Bode มีแกน Hz/dB/องศา, ค่าจาก run จริง, fL/fH หรือ "not determined" |
| B5 | Run tran 10 mV peak, 1 kHz | เห็น Vin/Vout ตามเวลา, ป้าย ms/V, กลับเฟส ~180° |
| B6 | เปลี่ยน amplitude 10 → 20 mV (และ/หรือ 1k → 2k) → Run tran ซ้ำ | waveform เปลี่ยนตามค่าที่ตั้ง |
| B7 | ใส่ RE = 0 | error ชัดเจน ไม่มีผล/กราฟเก่า ไม่มี Success ปลอม |
| B8 | Desktop ~1280 px และ mobile ~390 px | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ถูกตัด |

บันทึก ngspice version, model, วิธีตรวจ, ค่าที่เห็น, หลักฐาน, PASS/FAIL/NOT RUN ตามจริง
(Playwright MCP = NOT RUN เพราะผู้ใช้เลือก OpenCode Browser)

### 5.12 การส่งมอบ

- ติดตั้ง Flask (`pip install -r requirements.txt`) เพื่อรันและตรวจ
- commit บน `main` ตามประวัติเดิม แยก commit ตามขั้นงาน แล้ว push
- README: วิธีติดตั้ง ngspice, ตั้ง `NGSPICE_EXE`, รันแอป, โครงสร้าง, โมเดลและแหล่งที่มา, ข้อจำกัด

## 6. สิ่งที่ผู้ใช้ตัดสินแล้ว

1. **BJT model:** ใช้การ์ด 2N3904 (mfg=Philips) จาก Standard.bjt — อนุมัติแล้ว
2. **Browser acceptance:** ใช้ OpenCode Browser และบันทึก Playwright MCP เป็น NOT RUN — เลือกแล้ว
3. **แนวทาง:** server-rendered + SVG (A) — เลือกแล้ว

## 7. Calls ของผู้สร้าง (ตรวจทับได้)

- Analytical reference ใช้ `bjt.analyze()` (Thevenin) และเพิ่มฟิลด์ β/VBE เฉพาะหน้านี้
- ไม่มี tolerance เปรียบเทียบ SPICE/Analytical — แสดงผลต่างและคำอธิบาย
- Transient window/step ตาม §5.4
- AC sweep 1 Hz–100 MHz, dec 20; fL/fH ที่หาไม่ได้ → "not determined in sweep range"
- ติดตั้ง Impeccable ตอนขั้น UI; ถ้าติดปัญหา → NOT RUN + polish มือ
- commit บน `main`, push ทีละขั้นที่มีความหมาย
- ข้อความ error ภาษาไทยให้สอดคล้อง Lab 3; สี/ระยะห่างกราฟให้เข้ากับ `style.css` เดิม

## 8. สิ่งที่เหลือให้ผู้สร้างตัดสินเอง

- จำนวน tick และการจัดวางกราฟ
- โครงสร้าง helper ภายใน `plots.py` / `spice_engine.py`
- รายละเอียดข้อความอธิบายบนหน้าจอ (ต้องมี provenance ครบตาม §5.7)
