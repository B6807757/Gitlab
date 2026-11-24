# Lab 03 — ผลการตรวจสอบบนเบราว์เซอร์ (A1–A5)

วันที่ตรวจ: 17 พฤศจิกายน 2026

## สภาพแวดล้อมและวิธีตรวจ

| รายการ | ค่า |
|---|---|
| ระบบปฏิบัติการ | Windows (เครื่องผู้พัฒนา) |
| Python | 3.12.7 |
| Flask | 3.1.3 |
| เว็บแอป | `python app.py` → <http://127.0.0.1:5000> |
| เครื่องมือตรวจ | **OpenCode Browser** (เปิดแท็บจริง กรอกฟอร์ม กดปุ่ม อ่านข้อความบนหน้า และ screenshot) |
| ชุดทดสอบเดิม | `python -m unittest -v` → 52 tests OK (31 ใน `test_bjt.py`, 21 ใน `test_app.py`) |

ไม่ได้ใช้ Playwright MCP เพราะเครื่องนี้ไม่มี `node`/`npx` ให้รัน MCP server
การตรวจ A1–A5 ทั้งหมดทำผ่านหน้าเว็บจริง ไม่ได้ใช้ `curl` และไม่ได้อ่านค่าจากโค้ดแทน

## ตาราง A1–A5

ค่าอ้างอิงคำนวณมือจากสมการในใบงาน/design doc §7 ก่อนรัน (ยังไม่ปัดเศษ)
ผลที่เห็นอ่านจากหน้าเว็บหลังกด `คำนวณ` (หน้าจอแสดง 3 หลักสำคัญ)
เกณฑ์ผ่าน: `IC` คลาดเคลื่อน ≤ 0.01 mA และ `VCE` ≤ 0.02 V จากค่าอ้างอิงที่ยังไม่ปัด

| กรณี | โหมด / อินพุต | ค่าอ้างอิง (ยังไม่ปัด) | ผลที่เห็นบนหน้าเว็บ | ผลต่าง | สถานะ |
|---|---|---|---|---|---|
| A1 | Divider · `VCC=12`, `R1=100k`, `R2=22k`, `RC=2.2k`, `RE=1k`, `β=100`, `VBE=0.70` | `IC = 1.22983 mA`, `VCE = 8.05225 V` | `IC = 1.23 mA`, `VCE = 8.05 V` | `0.00017 mA`, `0.00225 V` | ผ่าน |
| A2 | Fixed · `VCC=12`, `RB=1M`, `RC=2.2k`, `β=100`, `VBE=0.70` (ไม่มีช่อง `RE`) | `IC = 1.13000 mA`, `VCE = 9.51400 V` | `IC = 1.13 mA`, `VCE = 9.51 V` | `0`, `0.004 V` | ผ่าน |
| A3 | Emitter · `VCC=12`, `RB=1M`, `RC=2.2k`, `RE=1k`, `β=100`, `VBE=0.70` | `IC = 1.02634 mA`, `VCE = 8.70545 V` | `IC = 1.03 mA`, `VCE = 8.71 V` | `0.00366 mA`, `0.00455 V` | ผ่าน |
| A4 | Emitter · คงค่า A3 เปลี่ยนเฉพาะ `RE=2k` | `IC = 0.94010 mA`, `VCE = 8.03278 V` | `IC = 940 µA`, `VCE = 8.03 V` | `0.00010 mA`, `0.00022 V` | ผ่าน |
| A5 | Fixed · `RB=0` | ต้องได้ข้อผิดพลาด ไม่มีผลลัพธ์ | `Fixed Bias: RB ต้องมากกว่า 0` ไม่มีส่วนผลลัพธ์ หน้าเว็บยังใช้งานได้ | — | ผ่าน |

ค่าที่เห็นครบทุกตัว (อ่านจากหน้าเว็บ):

| กรณี | IB | IC | IE | VB | VE | VC | VCE |
|---|---|---|---|---|---|---|---|
| A1 | 12.3 µA | 1.23 mA | 1.24 mA | 1.94 V | 1.24 V | 9.29 V | 8.05 V |
| A2 | 11.3 µA | 1.13 mA | 1.14 mA | 700 mV | 0 V | 9.51 V | 9.51 V |
| A3 | 10.3 µA | 1.03 mA | 1.04 mA | 1.74 V | 1.04 V | 9.74 V | 8.71 V |
| A4 | 9.40 µA | 940 µA | 950 µA | 2.60 V | 1.90 V | 9.93 V | 8.03 V |

A4 แสดงทิศทางตามที่ทำนาย: `RE` เพิ่มจาก 1 kΩ เป็น 2 kΩ ทำให้ `IB`/`IC` ลดลง
`VE` เพิ่มขึ้นมาก และ `VCE` ลดลงจาก 8.71 V เป็น 8.03 V

หลักฐาน (screenshot จาก OpenCode Browser):

- A1 Divider: [`docs/evidence/lab03-a1-divider.jpeg`](evidence/lab03-a1-divider.jpeg)
- A3 Emitter: [`docs/evidence/lab03-a3-emitter.jpeg`](evidence/lab03-a3-emitter.jpeg)
- A5 Fixed error: [`docs/evidence/lab03-a5-fixed-error.jpeg`](evidence/lab03-a5-fixed-error.jpeg)

## A1 baseline ก่อนแก้โค้ด (Lab 2)

บันทึกก่อนเพิ่มโหมดใหม่ โดยใช้แอป Lab 2 ที่ `main` (`cbf5fbe`):

| ค่า | ก่อนแก้ (Lab 2) | หลังแก้ (Lab 03) |
|---|---|---|
| IB | 12.3 µA | 12.3 µA |
| IC | 1.23 mA | 1.23 mA |
| IE | 1.24 mA | 1.24 mA |
| VB | 1.94 V | 1.94 V |
| VE | 1.24 V | 1.24 V |
| VC | 9.29 V | 9.29 V |
| VCE | 8.05 V | 8.05 V |
| VBB / RB | 2.16 V / 18.0 kΩ | 2.16 V / 18.0 kΩ |
| Thévenin vs Nodal | 1.23 mA / 1.23 mA (ผลต่าง 3.6e-16) | เหมือนเดิม |

ผล Divider ไม่เปลี่ยนหลังเพิ่มโหมด และตรงกับค่าอ้างอิงมือ
`IC = 1.22983 mA`, `VCE = 8.05225 V`

## ค่าอ้างอิงอิสระของโหมดใหม่ — A3 (Emitter Bias)

คำนวณมือด้วยเครื่องคิดเลขจากสมการใบงาน ก่อนรันโปรแกรม (ไม่ได้อ่านค่าจากโปรแกรม):

```
VCC = 12 V, RB = 1,000,000 Ω, RC = 2,200 Ω, RE = 1,000 Ω, β = 100, VBE = 0.70 V

IB  = (VCC − VBE) / (RB + (β + 1)·RE)
    = (12 − 0.70) / (1,000,000 + 101 × 1,000)
    = 11.30 / 1,101,000
    = 1.02634 × 10⁻⁵ A = 10.2634 µA

IC  = β·IB = 100 × 1.02634 × 10⁻⁵ = 1.02634 × 10⁻³ A = 1.02634 mA
IE  = (β + 1)·IB = 101 × 1.02634 × 10⁻⁵ = 1.03660 × 10⁻³ A = 1.03660 mA
VE  = IE·RE = 1.03660 × 10⁻³ × 1,000 = 1.03660 V
VB  = VE + VBE = 1.03660 + 0.70 = 1.73660 V
VC  = VCC − IC·RC = 12 − 1.02634 × 10⁻³ × 2,200 = 9.74205 V
VCE = VC − VE = 9.74205 − 1.03660 = 8.70545 V
```

หน้าเว็บแสดง `IB = 10.3 µA`, `IC = 1.03 mA`, `IE = 1.04 mA`, `VB = 1.74 V`,
`VE = 1.04 V`, `VC = 9.74 V`, `VCE = 8.71 V` ซึ่งตรงกับค่าข้างต้นเมื่อปัดเป็น 3 หลักสำคัญ

## เส้นทางข้อมูลของ A4

```
ฟอร์ม Emitter: RE = "2k"
  → parse_resistance("2k")            = 2,000.0 Ω   (แปลงหน่วยครั้งเดียว)
  → build_mode_inputs("emitter", ...) → EmitterInputs(re=2000.0, rb=1e6, rc=2200.0,
                                                      beta=100.0, vbe=0.70)
  → analyze_emitter(inputs)           → ib = 9.40100e-6 A
                                        ic = 9.400998e-4 A
                                        vce = 8.032779 V
  → format_current / format_voltage   → "940 µA" / "8.03 V"
  → หน้าเว็บ (badge Active, verdict "โซนแอกทีฟตามแบบจำลอง")
```

## การตรวจเพิ่มเติม (ไม่ใช่หลักฐาน A1–A5)

| กรณี | วิธีตรวจ | ผลที่เห็น |
|---|---|---|
| สลับโหมดหลังมีผลลัพธ์ | กด `เปลี่ยนโหมด` จากหน้า Fixed ที่มีผลแล้วไป Emitter | หน้าใหม่ไม่มีส่วนผลลัพธ์ของรอบก่อน |
| โหมดไม่รู้จัก (GET) | เปิด `/?mode=bogus` ในเบราว์เซอร์ | HTTP 400, ข้อความ `ไม่รู้จักโหมดที่เลือก: bogus` + ลิงก์กลับหน้าเริ่มต้น ไม่มีฟอร์ม/แผนภาพ |
| โหมดไม่รู้จัก (POST) | HTTP POST `mode=bogus` ตรงไปยัง `/` | HTTP 400, ไม่มีผลลัพธ์ Divider ถูกคำนวณแทน |
| POST ไม่มี `mode` | HTTP POST ด้วยฟิลด์ Divider แต่ไม่มี `mode` | HTTP 400, ข้อความ `ไม่ได้ระบุโหมด (mode)` ไม่มีผลลัพธ์ |
| ฟิลด์ที่ไม่ใช้ของโหมด | POST Emitter พร้อม `r1=abc` (โหมด Emitter ไม่ใช้ `r1`) | HTTP 200 และคำนวณสำเร็จ — ฟิลด์ที่ไม่ใช้ไม่ถูกตรวจ |
| `VCE ≤ 0.2 V` | Fixed · `RB=1M`, `RC=11k` | badge `Model warning`, verdict `แบบจำลอง Forward Active อาจใช้ไม่ได้ · VCE = -430 mV`, คำเตือน `VCE ≤ 0.2 V: ...` ไม่ถูกเรียกว่า Active ปกติ |
| ข้อความผู้ใช้ใน HTML | POST Fixed ด้วย `RB = 1M" onload="alert(1)` | ถูก escape (`&quot;`) ไม่หลุดเป็น attribute; แสดง error `กรุณากรอกเป็นตัวเลข` |

หลักฐานเพิ่มเติม: [`docs/evidence/lab03-fixed-model-warning.jpeg`](evidence/lab03-fixed-model-warning.jpeg)

## ส่วนที่ AI ทำ และส่วนที่นักศึกษาตรวจ

AI ช่วย:

- เขียนฟังก์ชัน `analyze_fixed` / `analyze_emitter` และ validator ใน `bjt.py`
- เขียน mode dispatch, การแปลงหน่วย และการจัดการ error ใน `app.py`
- ปรับ template (mode switcher, ฟิลด์/ผลตามโหมด, SVG 3 แบบ) และ CSS
- ร่างเอกสารนี้และ README

นักศึกษาเป็นผู้ตรวจ:

- ตรวจสมการและหน่วยของทั้งสามโหมดเทียบกับใบงาน
- ตรวจค่าอ้างอิง A1–A5 ที่คำนวณมือในหัวข้อก่อนหน้า (โดยเฉพาะ A4 = 8.03 V)
- ทวนผลบนเบราว์เซอร์อย่างน้อยหนึ่งกรณี (A1, A3, A5) และดู screenshot ด้วยตนเอง

---

# Lab 04 — CE Amplifier Simulator: ผลตรวจรับ B1–B8

วันที่ตรวจ: 24 พฤศจิกายน 2026

## สภาพแวดล้อม

| รายการ | ค่า |
|---|---|
| OS / Python / Flask | Windows · Python 3.12.7 · Flask 3.1.3 |
| Engine | ngspice-33 (64-bit) path แสดงบนหน้า `/simulator` |
| โมเดล BJT | `Q2N3904` — LTspice Standard.bjt (mfg=Philips), `BF=300` |
| ชุดทดสอบ | `python -m unittest -v` → **85 tests OK** |
| เครื่องมือ | OpenCode Browser (แท็บจริง `/simulator`, ส่งฟอร์มจริงแล้วอ่านข้อความ/DOM ที่ render) |
| Playwright MCP | **NOT RUN** (ผู้ใช้เลือกใช้ OpenCode Browser) |

หมายเหตุวิธีกดปุ่ม: ตัวชี้ของ Browser tool ไม่สามารถคลิกปุ่มได้
(`DOM.getNodeForLocation failed`) จึงใช้ `evaluate` เรียก `.click()` บน `<button>`
จริงของหน้าเว็บ — คำสั่งยังส่ง POST ผ่านฟอร์มเดิมและอ่านผลที่ render จาก ngspice จริง
ไม่ได้เรียก `run_simulation` จาก Python แทน

## ตาราง B1–B8

| Case | Method | Input | Expected / Reference | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 | Lab 03 browser A1–A5 + `test_app.py`/`test_bjt.py` | Divider `12/100k/22k/2.2k/1k/β100/0.70`; Fixed `12/1M/2.2k/β100/0.70`; Emitter `12/1M/2.2k/1k/β100/0.70` | ทั้ง 3 โหมดคำนวณและสลับได้ ผลตรง A1–A5 | Divider/Fixed/Emitter ผ่าน A1–A5, มีลิงก์ไป-กลับ `/simulator` | Lab 03 A1–A5 ข้างบน + screenshot ใน `docs/evidence/lab03-*.jpeg` | ผ่าน |
| B2 | `/simulator` → `Run DC (.op)` | default `12 V, 100k, 22k, 2.2k, 1k, 10k, 10u, 10u, 10 mV, 1 kHz` | ngspice รันสำเร็จและแสดง VB/VE/VC/VCE/IC แยกจาก Analytical | `Success`, `ngspice-33`, `Q2N3904`; SPICE `VB 2.084 V`, `VE 1.421 V`, `VC 8.883 V`, `VCE 7.462 V`, `IC 1.417 mA`; Analytical `IC 1.299 mA`, `VCE 7.834 V`; delta `+9.1%` / `−4.8%` | ข้อความบนหน้า + `<details>` netlist/log ของรันนี้ | ผ่าน |
| B3 | เปลี่ยน RE แล้ว `Run DC` ซ้ำ | `RE 1k → 2k` (อย่างอื่นคงเดิม) | operating point เปลี่ยนตามผลรัน new | `IC 1.417 → 0.737 mA`, `VCE 7.462 → 8.902 V`, `VE 1.421 → 1.478 V` | ตาราง DC ของรันที่ 2 ใน browser | ผ่าน |
| B4 | `Run AC (.ac)` | ค่า default, `.ac dec 20 1 100meg` | Bode มีแกน Hz/dB/องศา; fL/fH หรือข้อความ `not determined` | gain 1 kHz `1.764 V/V = 4.93 dB`, phase `−179.9°`, `fL 1.75 Hz`, `fH not determined in sweep range`; SVG 161 จุด มี `ความถี่ (Hz)`, `ขนาด (dB)`, `เฟส (องศา)` | SVG บนหน้า + log ดิบ | ผ่าน |
| B5 | `Run tran (.tran)` | `10 mV peak, 1 kHz` | waveform Vin/Vout, แกน ms/V, กลับเฟส ~180° | `Vin 20.00 mVpp`, `Vout 35.27 mVpp`, `กลับเฟส (~180°)`, `5.00 ms`, step `2.50 µs`, 2008 จุด; แกน `เวลา (ms)`, `แรงดัน (V)`, legend `Vin`/`Vout` | SVG บนหน้า + log ดิบ | ผ่าน |
| B6 | เปลี่ยน amplitude แล้ว `Run tran` ซ้ำ | `10 → 20 mV peak` | waveform/ค่าขยับตาม amplitude ใหม่ | `Vin 40.00 mVpp`, `Vout 70.55 mVpp` (เดิม 35.27) | ตาราง + SVG ของรันที่ 2 | ผ่าน |
| B7 | ใส่ RE ผิดแล้ว `Run DC` | `RE = 0` | error ชัดเจน ไม่มีผล/กราฟเก่า ไม่มี Success ปลอม | `Error: ข้อมูลไม่ถูกต้อง: RE ต้องมากกว่า 0`, ไม่มี `<svg>`, ไม่มี `Success` | หน้า error ใน browser | ผ่าน |
| B8 | Screenshot หน้า `/simulator` ที่ผล DC | desktop viewport จริงของ browser tool `1000×700`; mobile จำลองโดยจำกัดความกว้างเอกสารเป็น 390 px | อ่านปุ่ม/หน่วย/กราฟง่าย ไม่ถูกตัด | เก็บภาพแล้ว: desktop full-page `985×1571`, mobile-width `390×1035`; ข้อความปุ่ม แกน และตารางยังอ่านได้ | [`lab04-desktop-dc.png`](evidence/lab04-desktop-dc.png), [`lab04-mobile-dc.png`](evidence/lab04-mobile-dc.png) | ผ่าน (มีข้อจำกัดดูหมายเหตุ) |

ข้อจำกัด B8: Browser tool ของ OpenCode ไม่มีคำสั่งเปลี่ยน viewport จริง จึงใช้ viewport
desktop `1000×700` (ใกล้เคียง ~1280 px) และจำลองมือถือด้วยการจำกัดความกว้างเอกสาร
เป็น 390 px — `@media (max-width:640px)` ไม่ได้ถูกทริกเกอร์จริง จึงยังไม่สามารถ
อ้างว่าได้ทดสอบ media query บนอุปกรณ์ 390 px แท้ได้ ภาพที่เก็บเป็นหลักฐานความกว้าง/
การอ่านได้ของเนื้อหา ไม่ใช่การจำลองอุปกรณ์เต็มรูปแบบ

## หมายเหตุผลที่ต้องแยก SPICE กับ Analytical

ค่าที่ต่างกัน (~9% ที่ IC) ไม่ใช่ความผิดพลาด: Analytical ใช้ β=150, VBE=0.70 V คงที่
และ Thevenin closed form ขณะที่ SPICE ใช้โมเดลจริง `BF=300`, Early effect (`VAF=100`)
และ VBE ที่คำนวณจาก `IS` ของโมเดล (~0.663 V) ตามที่ design doc §5 กำหนด
จึงไม่มีการตั้ง tolerance pass/fail ระหว่างสองคอลัมน์ — สถานะ "ผ่าน" หมายถึง
ngspice รันสำเร็จ อ่านตารางครบ และแสดงผลจาก log รอบนั้นจริง

## หลักฐานที่เปิดได้จากหน้าเว็บ

ปุ่ม `<details>` ใต้ผลลัพธ์แสดง **netlist ที่รันจริง** และ **ngspice log ดิบของรอบนั้น**
ทุกครั้ง ไม่ใช่ข้อความตัวอย่าง — ตารางและกราฟด้านบนparse จาก log ชุดเดียวกัน

## Screenshot กราฟจาก Browser จริง (ตามเกณฑ์ใบงาน)

ถ่ายจากแท็บ OpenCode Browser หลังกดปุ่ม `Run AC` / `Run Transient` จริง:

- Bode (dB + เฟส, 161 จุดจาก ngspice): [`lab04-ac-bode.png`](evidence/lab04-ac-bode.png)
- Waveform (Vin/Vout, 2008 จุดจาก ngspice): [`lab04-tran-waveform.png`](evidence/lab04-tran-waveform.png)

ภาพเหล่านี้เป็นผลที่ render จาก log ของรอบนั้น ไม่ใช่ภาพตัวอย่างหรือ mock data

## ส่วนที่ AI ทำ / นักศึกษาตรวจ (Lab 04)

- AI: เขียน `spice_engine.py` (netlist, batch run, parser), `plots.py` (SVG), `/simulator` route + template/CSS และชุดทดสอบ 3 ไฟล์
- AI: ติดตั้ง Impeccable, รัน detector, ปรับ UI เฉพาะหน้า `/simulator` และร่างเอกสารนี้
- นักศึกษาตรวจ: ค่าอ้างอิงใบงาน (12 V, 100k/22k/2.2k/1k/10k, 10u, 10 mV@1 kHz), แหล่งโมเดล Q2N3904 และความต่าง BF=300 กับ analytical β=150
- นักศึกษาตรวจ: ผล B1–B8 บน browser จริงโดยเฉพาะ fH `not determined`, การกลับเฟส ~180° และ error `RE = 0`; ทวนว่า netlist/log ที่แสดงตรงกับรันที่กด

## Impeccable (UI critique / polish)

- ติดตั้งด้วย `npx --yes impeccable install` สำเร็จ (project scope, OpenCode, engine v0.1.27)
- Critique: **DEGRADED: single-context** — Assessment A แบบ sub-agent ติด free usage limit
  ของ provider จึงทำ design review แบบอินไลน์แทน; Assessment B (detector) รันครบ
- Detector รอบแรกบน `/simulator` @390×844 พบ 3 รายการ: `kicker-above-heading`,
  `body-text-viewport-edge`, `flat-type-hierarchy`
- Polish ที่ทำเฉพาะหน้า `/simulator`: ลบ kicker เหนือ h1 (ย้าย "ENG29 2121 · LAB 04"
  เข้า course badge), เพิ่มขนาด h1/h2 และ `text-wrap: balance`, เพิ่ม padding ของ footer,
  เปลี่ยน error bar เป็น full border และเพิ่ม `:focus-visible` — ไม่แตะผลคำนวณ ข้อมูลกราฟ
  หน่วย หรือข้อความ error
- Detector รอบสุดท้ายบน URL @390×844: **0 findings**
- `detect --json --changed` (สแกนไฟล์ที่เปลี่ยน) ยังเหลือ 4 findings: `side-tab` 3 จุดใน
  Lab 03 CSS เดิม (นอกขอบเขต Lab 04 และ simulator override แล้ว) และ
  `flat-type-hierarchy` เป็น false positive เพราะ detector อ่าน
  `{{ url_for('static', filename='style.css') }}` ใน template ไม่ออก — หน้า render จริง
  ผ่าน detector แล้ว

## ผลต่างจากที่วางแผนไว้

- `find_cutoffs` ใช้จุดตัดที่ `gain_max/√2` บนสเกล log ของความถี่ ทำให้ fL ≈ 1.75 Hz
  และไม่พบ fH ในช่วง 1 Hz–100 MHz (gain แบนจนเกินช่วงสแกน)
  จึงแสดงข้อความ `not determined in sweep range` ตามที่ออกแบบ ไม่ได้สร้างเลขขึ้นมาเอง
- ngspice-33 ตัดตารางเป็นหน้า ๆ ละ 55 แถว พร้อม form feed + ซ้ำ header
  parser รองรับกรณีนี้และทดสอบ regression ไว้ (`test_paginated_table_keeps_rows_after_form_feed`)
- `vp()` ต้องอยู่คนละบรรทัดกับ `.print ac` และคืนค่าเป็น radian → แปลงเป็นองศาใน `parse_ac`

## ตรวจเทียบ Rubric 10 คะแนนในใบงาน

| หัวข้อ | คะแนน | หลักฐานใน repo นี้ |
|---|---|---|
| ความต่อเนื่องจาก Lab 3 | 1 | Lab 03 A1–A5 ข้างบน + 85 tests รวม Lab 3/4 |
| การเชื่อม ngspice | 3 | `spice_engine.py`, netlist/log ดิบใน `<details>`, engine path + model source บนหน้า |
| AC + Transient | 2 | กราฟ/ตาราง B4–B6 + screenshot `lab04-ac-bode.png`, `lab04-tran-waveform.png` |
| UI และ Impeccable | 2 | หัวข้อ Impeccable ข้างบน + CSS ที่เปลี่ยนเฉพาะ `/simulator` |
| Browser Acceptance | 1 | ตาราง B1–B8 (NOT RUN ถูกระบุตรงไปตรงมา) |
| GitHub + Reproducibility | 1 | commit บน `main`, README (ติดตั้ง/รัน), เอกสารนี้ + ภาพใน `docs/evidence/` |

## แหล่งเก็บโค้ด

GitHub: <https://github.com/B6807757/Gitlab> · โค้ด Lab 04 อยู่บน `main`
(`a60894d` = โค้ด + เทสต์, `b92c67a` = เอกสาร README)
