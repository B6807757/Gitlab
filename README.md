# DC Circuit Calculator

ใช้สำหรับเรียนแลป Compro ไฟฟ้า

โปรแกรมคำนวณกระแสและกำลังไฟฟ้าของวงจรตัวต้านทาน DC อุดมคติ ด้วยสมการ `I = V/R` และ `P = VI`

## วิธีใช้งาน

ต้องติดตั้ง Python 3 แล้วรัน:

```bash
python electrical.py
```

ตัวอย่างในโปรแกรมใช้แรงดัน `12 V` และความต้านทาน `6 Ω` ผลลัพธ์คือกระแส `2 A` และกำลัง `24 W`

ฟังก์ชัน `analyze_dc(voltage_v, resistance_ohm)` คืนค่าเป็นพจนานุกรมที่มี `current_a` และ `power_w` หากความต้านทานเป็นศูนย์ ฟังก์ชันจะแจ้ง `ValueError` แทนการหารด้วยศูนย์

## ทดสอบ

รันทดสอบด้วย `unittest` ซึ่งมาพร้อม Python:

```bash
python -m unittest -v
```

## บันทึกงานด้วย Git

ใช้ `git status` ตรวจสถานะ, `git add` เลือกไฟล์เข้า Staging Area, `git diff --staged` ตรวจสิ่งที่จะบันทึก และ `git commit` บันทึกลง Local Repository ส่วน `git push` ใช้ส่ง Commit ไปยัง Remote Repository เมื่อกำหนดไว้แล้ว

---

# ENG29 2121 — BJT Common-Emitter DC Bias Web App

เว็บแอป Flask ขนาดเล็กสำหรับหาจุดทำงาน DC (Q-point) ของวงจรไบแอสแบบแบ่งแรงดัน (voltage-divider bias) ต่อแบบ common-emitter พร้อมตรวจโซนทำงานและเทียบผลกับการคำนวณอีกวิธีหนึ่งที่เป็นอิสระต่อกัน

## ติดตั้งและรัน

```bash
python -m pip install -r requirements.txt
python app.py
```

เปิด <http://127.0.0.1:5000>

## อินพุต

`VCC` (V), `R1`, `R2`, `RC`, `RE` (Ω), `β`, `VBE` (V)

ช่องความต้านทานรับส่วนขยายได้ เช่น `47k`, `4.7k`, `1M`, `47kΩ` ส่วนช่องอื่นรับเลขทศนิยมธรรมดา (ไม่รับ `47,000` หรือ `4.7*1000`)

## เอาต์พุต

`IB, IC, IE, VB, VE, VC, VCE` พร้อมหน่วยแบบ SI (nA/µA/mA/A, µV/mV/V/kV, Ω/kΩ/MΩ) ตัวเลข 3 หลักสำคัญ ค่า intermediate `VBB` และ `RB` และโซนทำงาน

| เงื่อนไข | โซน |
|---|---|
| `VBB ≤ VBE` | Cutoff (ทรานซิสเตอร์ตัดการทำงาน, `IC = 0`, `VCE = VCC`) |
| `VCE < 0.2 V` | Saturation (Q-point ใช้ไม่ได้ พร้อมแสดง `IC(sat)`) |
| `0.2 V ≤ VCE < 1.0 V` | Active แต่ headroom เหลือน้อย (มีคำเตือน) |
| `VCE ≥ 1.0 V` | Active ปกติ |

ค่าในโซนอิ่มตัวจะไม่ถูก clamp ให้ดูเหมือนปกติ — โปรแกรมรายงานค่าตามที่คำนวณได้พร้อมคำเตือน

## การตรวจสอบการคำนวณ

โปรแกรมคำนวณสองครั้งด้วยวิธีที่ derive ต่างกันโดยไม่ใช้พีชคณิตร่วมกัน:

1. **Thévenin closed form** — แทนวงจรด้วย `VBB`, `RB` แล้วหา `IB`
2. **Nodal analysis** — แก้ระบบสมการ 3 โหนด (`VB`, `VC`, `IC`) ด้วย Gaussian elimination

ทั้งสองวิธีต้องตรงกัน (ผลต่างสัมพัทธ์สูงสุดที่แสดงบนหน้าจอ) พร้อมเทียบกับสูตรประมาณแบบ stiff divider (`IC ≈ (VBB − VBE)/RE`) และบอกว่าการประมาณนี้ใช้ได้หรือไม่ (`β·RE ≥ 10·RB`)

## แผนภาพวงจร

หน้าเว็บวาดวงจร common-emitter เป็น SVG ในตัว (ไม่ใช้ JavaScript และไม่ใช้ไฟล์รูป) ป้าย `VCC`, `R1`, `R2`, `RC`, `RE` และ `β` สร้างจากค่าเดียวกับที่ใช้คำนวณจริง ผ่านตัวจัดรูปแบบหน่วยชุดเดียวกับผลลัพธ์ ป้ายในภาพจึงตรงกับตัวเลขที่แสดงเสมอ

ถ้าอินพุตไม่ถูกต้อง หน้าจะยังแสดงแผนภาพด้วยค่าตั้งต้นพร้อมคำอธิบายใต้ภาพ เพื่อให้แก้ไขแล้วกดคำนวณใหม่ได้ทันที ในโหมดแอกทีฟจะมีบรรทัดสรุปโซนทำงานใต้ badge (เช่น `โซนแอกทีฟปกติ · VCE = 7.76 V > 0.2 V`) และหน้าจอ ≥900 px จะแสดงฟอร์มกับแผนภาพเป็นสองคอลัมน์

## ไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `bjt.py` | ตรรกะวิศวกรรมล้วน ๆ (ไม่ import Flask) |
| `app.py` | Flask routes และการแปลงค่าจากฟอร์ม |
| `templates/index.html`, `static/style.css` | หน้าเว็บหนึ่งหน้า ไม่ใช้ JavaScript |
| `test_bjt.py`, `test_app.py` | ชุดทดสอบ |

## ทดสอบ

```bash
python -m unittest -v
```

รันทั้งชุดของทั้งสองแลป (`electrical.py` และ `bjt.py`)

---

# ENG29 2121 — Lab 03: Three BJT Bias Modes

ต่อยอดจาก Lab 2 โดยเพิ่มโหมดไบแอสให้เลือก 3 แบบในหน้าเดียว เลือกโหมดด้วยฟอร์ม GET
(โหลดหน้าใหม่ ไม่ใช้ JavaScript) แล้วกรอกค่าของโหมดนั้น กด `คำนวณ`
สมการทั้งหมดอยู่ใน `bjt.py` ทั้งหมด HTML ทำหน้าที่แสดงผลเท่านั้น

## โหมดที่รองรับ

| โหมด | ฟิลด์ | สมการกระแสฐาน |
|---|---|---|
| Voltage Divider Bias (`divider`) | `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE` | `IB = (VTH − VBE) / (RTH + (β + 1)RE)` |
| Fixed Bias (`fixed`) | `VCC`, `RB`, `RC`, `β`, `VBE` | `IB = (VCC − VBE) / RB` |
| Emitter Bias (`emitter`) | `VCC`, `RB`, `RC`, `RE`, `β`, `VBE` | `IB = (VCC − VBE) / (RB + (β + 1)RE)` |

ทุกโหมดใช้ `IC = β·IB`, `IE = (β + 1)·IB`, `VB = VE + VBE`, `VC = VCC − IC·RC`,
`VCE = VC − VE` และโหมด Fixed ใช้ `VE = 0` (อิมิตเตอร์ต่อลงกราวด์)

หน้าเว็บแสดงเฉพาะช่องของโหมดที่เลือก ตรวจเฉพาะช่องเหล่านั้น แปลง `k`/`M`
เป็น Ω ครั้งเดียวก่อนเข้าสมการ และแสดงแรงดันเป็น V กับกระแสเป็น mA (พร้อมหน่วย SI)

## คำเตือนเมื่อแบบจำลอง Forward Active อาจใช้ไม่ได้

ถ้าอินพุตถูกต้องแต่ผลคำนวณได้ `IB ≤ 0` หรือ `VCE ≤ 0.2 V` โปรแกรมจะไม่คำนวณโซน
Cutoff/Saturation ใหม่ แต่จะติด badge `Model warning` พร้อมข้อความ
`แบบจำลอง Forward Active อาจใช้ไม่ได้` และบอกเงื่อนไขที่ทำให้เตือน
(ค่าที่คำนวณได้ยังแสดงตามจริง ไม่ clamp)

## วิธีรัน

```bash
python -m pip install -r requirements.txt
python app.py
```

เปิด <http://127.0.0.1:5000> แล้วเลือกโหมดที่ต้องการ

## การตรวจสอบ

ตารางผล A1–A5, ค่าอ้างอิงที่คำนวณมือ, A1 baseline ก่อนแก้โค้ด และหลักฐานจาก
OpenCode Browser อยู่ใน [`docs/validation.md`](docs/validation.md)
(ไฟล์ภาพอยู่ใน [`docs/evidence/`](docs/evidence/))

## แหล่งเก็บโค้ด

- GitHub: <https://github.com/B6807757/Gitlab>
- Commit ที่มีโค้ด Lab 03: `a698156` (`76314be` = mode dispatch/UI, `a698156` = CSS)

## ส่วนที่ AI ช่วย

AI เขียนฟังก์ชัน `analyze_fixed`/`analyze_emitter` และ validator, mode dispatch ใน
`app.py`, template/SVG ของโหมดใหม่, CSS และร่างเอกสาร `docs/validation.md`
นักศึกษาเป็นผู้ตรวจสมการและหน่วยเทียบใบงาน ตรวจค่าอ้างอิง A1–A5 (รวม A4 = 8.03 V)
และทวนผลบนเบราว์เซอร์จริงอย่างน้อยหนึ่งกรณี

---

# ENG29 2121 — Lab 04: CE Amplifier Simulator

ต่อยอดจาก Lab 03 ด้วยหน้า `/simulator` ที่รัน **ngspice จริง** บนวงจรอ้างอิง
Common-Emitter voltage-divider (2N3904) แล้วอ่านผลจาก log ที่เกิดจากรอบนั้น ๆ
ไม่มีข้อมูล/graf สำเร็จรูปและไม่ได้ปิดบังข้อผิดพลาดของ engine

## ติดตั้ง (เครื่องใหม่ / หลังโคลน)

```bash
python -m pip install -r requirements.txt
python app.py
# เปิด http://127.0.0.1:5000/simulator
```

Lab 04 ต้องการ ngspice เพิ่มจาก Lab 03:

1. ติดตั้ง ngspice (Windows ที่ใช้พัฒนา: ngspice-33 64-bit) แล้วเพิ่ม `ngspice.exe`
   ลง `PATH` **หรือ** ตั้งตัวแปร `NGSPICE_EXE` ให้ชี้ถึง file นั้น เช่น
   `set NGSPICE_EXE=C:\path\to\ngspice.exe`
2. หน้า `/simulator` จะแสดง path + version ของ engine ที่ตรวจพบทันที
   ถ้าไม่พบจะแสดงข้อความ `ยังไม่พบ ngspice` และไม่มีผลลัพธ์/กราฟปลอม

โคลนไปทำต่อเครื่องอื่นได้ปกติ (`git clone https://github.com/B6807757/Gitlab`)
เฉพาะ ngspice + Flask ต้องมีบนเครื่องนั้นด้วย เพราะผลทั้งหมดรันจากเครื่องที่ใช้เปิดเว็บ

## สิ่งที่หน้า `/simulator` ทำ

| ปุ่ม | สิ่งที่รัน | ผลที่แสดง |
|---|---|---|
| `Run DC (.op)` | ngspice `.op` | ตาราง VB/VE/VC/VCE/IC จาก SPICE เทียบกับสมการประมาณ (β/VBE ที่กรอก) พร้อมผลต่าง — ไม่บังคับให้ตัวเลขเท่ากัน |
| `Run AC (.ac)` | `.ac dec 20 1 100meg` | Bode (dB + เฟสองศา) จาก `vm/vp(5), vm/vp(6)`, gain ที่ 1 kHz และ fL/fH แบบ −3 dB (ถ้าไม่ตัดในช่วงสแกนจะขึ้น `not determined in sweep range`) |
| `Run Transient (.tran)` | `.tran` ตามความถี่ source | waveform Vin/Vout, Vpp, ตรวจการกลับเฟส, หน้าต่างเวลา 5 ms หรือ 3 คาบ (แล้วแต่ค่าที่มากกว่า) และ step ≥ 50 จุด/คาบ |

ค่าเริ่มต้นตามใบงาน: `VCC=12 V`, `R1=100k`, `R2=22k`, `RC=2.2k`, `RE=1k`,
`RL=10k`, `CIN=COUT=10u`, source `10 mV peak, 1 kHz`, analytical `β=150`, `VBE=0.70 V`

โมเดล BJT คือ `Q2N3904` (LTspice Standard.bjt, mfg=Philips, `BF=300`, มี Early effect)
ที่มาและ netlist ที่รันจริง + ngspice log ดิบของรอบนั้นเปิดได้จาก `<details>` ใต้ผลลัพธ์

## ไฟล์ที่เพิ่มจาก Lab 03

| ไฟล์ | หน้าที่ |
|---|---|
| `spice_engine.py` | validate ค่า, สร้าง netlist, หา/รัน ngspice, parse `.op`/`.ac`/`.tran` จาก log |
| `plots.py` | วาด Bode และ waveform เป็น inline SVG จากข้อมูลที่ parse ได้เท่านั้น |
| `templates/simulator.html`, `static/style.css` | หน้า `/simulator` (server-rendered ไม่ใช้ JavaScript) |
| `test_spice_engine.py`, `test_plots.py`, `test_simulator_app.py` | ชุดทดสอบของ Lab 04 |

การแปลงหน่วย: resistances รับ `k`/`M`, capacitances รับ `p`/`n`/`u`/`µ`/`m` (ตามด้วย `F` ได้)
`RE = 0` ถูกปฏิเสธก่อนสร้าง netlist และแสดง error โดยไม่มีกราฟ/ป้าย Success ปลอม

รายละเอียดออกแบบ: [`docs/superpowers/specs/2026-11-24-lab04-ce-amplifier-simulator-design.md`](docs/superpowers/specs/2026-11-24-lab04-ce-amplifier-simulator-design.md)
แผนทำงาน: [`docs/superpowers/plans/2026-11-24-lab04-ce-amplifier-simulator.md`](docs/superpowers/plans/2026-11-24-lab04-ce-amplifier-simulator.md)
หลักฐานตรวจรับ: [`docs/validation.md`](docs/validation.md)

