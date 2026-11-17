# Lab 03 — เพิ่มโหมด Fixed Bias และ Emitter Bias ในเว็บ BJT DC Bias

- วันที่: 2026-11-17
- สถานะ: รออนุมัติจากเจ้าของงาน
- อ้างอิงใบงาน: `ENG29_2121_Lab03_BJT_Bias_Web_App.html`
- โค้ดฐาน: `main` ที่ `cbf5fbe` (งาน Lab 2 ที่ merge/push แล้ว)
- ขอบเขต: ต่อยอดเว็บ Flask เดิม ไม่ทำเว็บใหม่

## 1. เจตนา

Lab 2 คำนวณ Voltage Divider Bias วงจรเดียว Lab 03 ต้องการให้เว็บเดิมเลือกวงจรได้สามแบบ
— Voltage Divider Bias (ของเดิม), Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียว —
โดยผลของ Divider ต้องเหมือนเดิมทุกตัวเมื่อกรอกค่าเดิม และต้องมีหลักฐานการตรวจผลจริง
ผ่านเบราว์เซอร์ตามตาราง A1–A5 ของใบงาน

เป้าหมายไม่ใช่การสร้างเครื่องคิดเลขใหม่ แต่คือการแสดงว่าเราแยกสมการแต่ละวงจรได้
เลือกฟังก์ชันตามโหมดได้ ตรวจเฉพาะช่องที่โหมดนั้นใช้ และรักษาผลเดิมไว้ได้

## 2. เป้าหมาย / ไม่ใช่เป้าหมาย / anti-goals

### เป้าหมาย

1. เพิ่ม Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียว โดยใช้ `VCC`, `RC`, `β`, `VBE` ร่วมกัน
2. ให้ Divider Bias ให้ผลคำนวณ ฟิลด์ และแผนภาพเหมือน Lab 2 ทุกประการเมื่อกรอกค่าเดิม
   (หัวข้อผลลัพธ์และข้อความผิดพลาดเพิ่มป้ายชื่อโหมดได้ เพื่อให้ตรงข้อกำหนด "ระบุโหมด")
3. เลือกโหมดจากฟอร์ม แล้วเห็นเฉพาะช่องที่โหมดนั้นใช้ โดยไม่ต้องใช้ JavaScript
4. ผลลัพธ์และข้อผิดพลาดระบุโหมดที่เลือก และผลรอบก่อนต้องไม่ถูกแสดงเป็นผลรอบใหม่
5. ตรวจเฉพาะฟิลด์ของโหมดที่เลือก: ค่าไม่ครบ / ไม่ใช่ตัวเลข / ไม่ finite / ค่าที่ต้องเป็นบวก ≤ 0
   ต้องแจ้งข้อผิดพลาดภาษาไทย
6. ถ้าอินพุตถูกต้องแต่ `IB ≤ 0` หรือ `VCE ≤ 0.2 V` ให้เตือนว่าแบบจำลอง Forward Active
   อาจใช้ไม่ได้ โดยไม่ต้องคำนวณค่า Cutoff/Saturation ใหม่
7. มีแผนภาพ SVG แยกตามโหมด ป้ายผูกกับค่าที่ใช้คำนวณจริง
8. เก็บเทสเดิม 52 ตัวไว้ ปรับได้เพียงเพิ่ม `mode=divider` ในข้อมูล POST
9. ส่งงานพร้อม README, `docs/validation.md`, GitHub URL และ Commit SHA

### ไม่ใช่เป้าหมาย

- ไม่เขียน `unittest` ใหม่ (ใบงานกำหนดให้ตรวจพฤติกรรมใหม่ผ่าน Browser)
- ไม่ทำ SPICE, DC Load Line, AC/Transient, ตัวเก็บประจุ Bypass
- ไม่แยก route ต่อโหมด และไม่สร้างเว็บใหม่
- ไม่ย้ายสมการไปไว้ใน HTML หรือ JavaScript
- ไม่คำนวณจุดทำงานจริงใน Cutoff/Saturation สำหรับโหมดใหม่
- ไม่เพิ่ม dependency ใหม่

### Anti-goals (ทำแล้วถือว่าล้มเหลว)

- ผลของ Divider เปลี่ยนแม้กรอกค่าเดิม
- โหมดที่ไม่รู้จักถูกตีความเป็น Divider เงียบ ๆ
- ผลของรอบก่อนยังค้างอยู่ทั้งที่รอบใหม่ผิดพลาด
- ตรวจฟิลด์ที่ไม่ใช้ของโหมดนั้นแล้วปฏิเสธอินพุตที่ควรใช้ได้
- ใช้ค่าที่โปรแกรมคำนวณเองเป็น "ค่าอ้างอิง" ในเอกสารตรวจรับ

## 3. ข้อกำหนดจากใบงาน (constraints)

- ใช้โค้ดและฟอร์ม Lab 2 เป็นจุดเริ่มต้น
- สมการอยู่ในโมดูล Python (`bjt.py` ทำหน้าที่แทน `dc_bias.py`)
- `app.py` เลือกฟังก์ชันด้วย `if` / `elif` ตามค่าที่ส่งจากฟอร์ม
- แปลงหน่วยเป็น Ω ครั้งเดียวที่จุดรับข้อมูล แล้วคำนวณด้วย Ω และ A
- แสดง `VB`, `VE`, `VC`, `VCE` เป็น V และ `IC` เป็น mA
- โหมดที่ไม่รู้จักต้องแจ้งข้อผิดพลาด ไม่เดาเป็น Divider
- ฟอร์มเลือกโหมดแล้วโหลดใหม่ได้ ไม่จำเป็นต้องมี JavaScript
- ผลลัพธ์และข้อผิดพลาดระบุโหมด
- เก็บเทสเดิม ไม่สร้าง unittest ใหม่
- ค่าอ้างอิงต้องเป็นอิสระจากโปรแกรม และต้องมีอย่างน้อยหนึ่งกรณีของโหมดใหม่
  พร้อมสมการและหน่วย
- ตรวจ A1–A5 ผ่าน Browser จริง บันทึกวิธีจริงว่า Playwright MCP, OpenCode Browser
  หรือ Manual (เครื่องนี้ไม่มี Node/npx จึงใช้ OpenCode Browser)

## 4. สภาพปัจจุบัน (Lab 2)

- `bjt.py` มี `BiasInputs`, `validate`, `thevenin_equivalent`, `solve_thevenin`,
  `solve_nodal`, `analyze`, `BiasResult`, `classify_region` และ formatter
- `app.py` มี route เดียว `/` (GET/POST), `DEFAULTS`, `parse_number`,
  `parse_resistance`, `build_inputs`, `DEFAULT_INPUTS`
- `templates/index.html` มีฟอร์ม Divider, ผลลัพธ์, ตาราง cross-check และ SVG Divider
- `test_bjt.py` 32 ตัว, `test_app.py` 13 ตัว, `test_electrical.py` 7 ตัว — รวม 52 ตัว
- ค่าตั้งต้น Divider: `12`, `47k`, `10k`, `2.2k`, `1k`, `150`, `0.7`
- `parse_resistance` รับ `k/K/M/Ω/ohm` และคืนค่าเป็น Ω

## 5. ทางเลือกที่พิจารณา

### A. ต่อยอดโครงเดิม (เลือก)

`bjt.py` เพิ่ม `FixedInputs`, `EmitterInputs`, `analyze_fixed()`, `analyze_emitter()`
โดยไม่แตะ Divider · `app.py` มี `MODE_DEFS` (โหมด → ฟิลด์, ป้าย, ค่าตั้งต้น) และ dispatch
ด้วย `if/elif` · template มีตัวเลือกโหมด (GET) + ฟิลด์/SVG ตามโหมด

- ข้อดี: Divider ไม่เสี่ยง regress, เทสเดิมใช้ต่อได้, ตรงข้อ "ไม่ต้องทำเว็บใหม่"
- ข้อเสีย: template มีเงื่อนไขตามโหมดเพิ่มขึ้น

### B. รื้อเป็น dict กลาง

ให้ทุกโหมดรับ dict เดียวและคืน dict รูปแบบเดียวกันทั้งหมด

- ข้อดี: ชื่อคีย์ตรงใบงานเป๊ะ
- ข้อเสีย: ต้องรื้อ `BiasResult`, หน้าผลลัพธ์ และเทสของ Lab 2 → เสี่ยงทำให้ Divider เพี้ยน
  ซึ่งขัดเกณฑ์ "Divider ต้องคงเดิม" (3 คะแนน)

### C. แยก route ต่อโหมด (`/divider`, `/fixed`, `/emitter`)

- ข้อเสีย: ฟอร์ม/ผลลัพธ์ซ้ำ 3 ชุด, ผิดเจตนา "หนึ่งเว็บเลือกวงจรได้", flow ตรวจ browser ยุ่งขึ้น

**Decision:** ใช้ A ตามที่เจ้าของงานเลือก

## 6. การออกแบบ

### 6.1 โหมด ฟิลด์ และค่าตั้งต้น

| mode (ค่าที่ส่ง) | ป้ายที่แสดง | ฟิลด์ที่ใช้ | ค่าตั้งต้น |
|---|---|---|---|
| `divider` | Voltage Divider Bias | `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE` | `12`, `47k`, `10k`, `2.2k`, `1k`, `150`, `0.7` |
| `fixed` | Fixed Bias | `VCC`, `RB`, `RC`, `β`, `VBE` | `12`, `1M`, `2.2k`, `100`, `0.70` |
| `emitter` | Emitter Bias | `VCC`, `RB`, `RC`, `RE`, `β`, `VBE` | `12`, `1M`, `2.2k`, `1k`, `100`, `0.70` |

- Divider คงค่าตั้งต้นเดิมทั้งหมดเพื่อไม่ให้เทสและพฤติกรรม Lab 2 เปลี่ยน
- Fixed/Emitter ใช้ `β = 100`, `VBE = 0.70` และ `RB = 1 MΩ` ให้ตรงกับ A1–A5
- Fixed ไม่มีช่อง `RE` และไม่ตรวจ `RE`
- Emitter ไม่มีช่อง `R1`, `R2` และไม่ตรวจ `R1`, `R2`
- Divider ไม่มีช่อง `RB` และไม่ตรวจ `RB`

### 6.2 สมการ

ทุกโหมดใช้ `VCC`, `RC`, `β`, `VBE` ร่วมกัน และคำนวณด้วย Ω กับ A

```
Fixed:    IB = (VCC − VBE) / RB
Emitter:  IB = (VCC − VBE) / (RB + (β + 1)·RE)
Divider:  IB = (VTH − VBE) / (RTH + (β + 1)·RE)
          VTH = VCC·R2 / (R1 + R2)
          RTH = R1·R2 / (R1 + R2)

IC = β·IB
IE = (β + 1)·IB
VE = IE·RE          (Fixed: VE = 0 V)
VB = VE + VBE
VC = VCC − IC·RC
VCE = VC − VE
```

- Fixed และ Emitter ไม่มีเส้นทาง Cutoff/Saturation ในแบบจำลองนี้
- Divider ใช้ `analyze()` เดิมทั้งหมด รวมถึง Thévenin/nodal cross-check และสูตรประมาณ

### 6.3 สัญญาผลลัพธ์ (result contract)

ฟังก์ชันใหม่คืน `dict` ที่มีคีย์และหน่วยตรงกัน:

```
{
  "ib": A, "ic": A, "ie": A,
  "vb": V, "ve": V, "vc": V, "vce": V,
  "region": "active" | "model_warning",
  "warnings": tuple[str, ...],
}
```

- ชื่อคีย์เป็นชื่อเดียวกับ attribute ของ `BiasResult` เดิม (`ib`, `ic`, ...)
  ตามที่ใบงานอนุญาตให้ใช้ชื่อคีย์เดิมของ Lab 2 ต่อ
- หน่วยภายในเป็น SI (A และ V) แล้วให้ template แปลงเป็นหน่วยแสดงผลด้วย
  `format_current` / `format_voltage` ชุดเดิม
- `app.py` ห่อ dict ด้วย `ModeResult` (dataclass ใน `bjt.py`) เพื่อให้ template
  เข้าถึงด้วย attribute ได้เหมือน `BiasResult`

```
ModeResult(
  inputs: FixedInputs | EmitterInputs,
  ib, ic, ie, vb, ve, vc, vce,
  region, warnings
)
```

- Divider ยังคืน `BiasResult` เดิม ไม่เปลี่ยนรูป
- `region` ของโหมดใหม่:
  - `"active"` เมื่อ `IB > 0` และ `VCE > 0.2 V`
  - `"model_warning"` เมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V`
- ไม่มี `vbb`, `rb`, `ic_sat`, `ic_approx`, `stiff_divider` ในโหมดใหม่
  (template แสดงส่วนเหล่านี้เฉพาะ `mode == "divider"`)

### 6.4 การตรวจอินพุต

ตรวจเฉพาะฟิลด์ของโหมด และใช้ข้อความภาษาไทยที่ระบุชื่อฟิลด์:

| เงื่อนไข | ข้อความ |
|---|---|
| ไม่เป็นจำนวนจริง (`NaN`, `inf`) | `<FIELD> ต้องเป็นจำนวนจริง` |
| `VCC`, `RC`, `RB`, `RE` ≤ 0 | `<FIELD> ต้องมากกว่า 0` |
| `β < 1` | `β ต้องไม่น้อยกว่า 1` |
| `VBE` ไม่อยู่ในช่วง `0 ≤ VBE < VCC` | `VBE ต้องอยู่ระหว่าง 0 ถึง VCC` |
| ค่าไม่ครบ / ไม่ใช่ตัวเลข | `กรุณากรอกเป็นตัวเลข` (จาก parser เดิม) |

- `<FIELD>` เป็น `VCC`, `RB`, `RC`, `RE`, `β`, `VBE`
- Fixed ตรวจ `VCC`, `RB`, `RC`, `β`, `VBE` — ไม่ตรวจ `RE`
- Emitter ตรวจ `VCC`, `RB`, `RC`, `RE`, `β`, `VBE` — ไม่ตรวจ `R1`, `R2`
- Divider ใช้ `validate()` เดิมทั้งหมด
- `VBE = VCC` ถูกปฏิเสธเหมือน Lab 2 (ดังนั้น `IB ≤ 0` ในทางปฏิบัติจะไม่เกิด
  แต่ยังคง guard ไว้ตามข้อกำหนดใบงาน)
- ข้อผิดพลาดในโหมดที่รู้จักจะถูกเติมชื่อโหมด เช่น
  `Fixed Bias: RB ต้องมากกว่า 0`

### 6.5 การเลือกโหมดใน `app.py`

ใช้ `if/elif` ตามข้อกำหนด:

```python
mode = (request.form.get("mode") or "").strip().lower()

if mode == "divider":
    result = analyze(build_divider_inputs(raw))
elif mode == "fixed":
    result = ModeResult(inputs=..., **analyze_fixed(...))
elif mode == "emitter":
    result = ModeResult(inputs=..., **analyze_emitter(...))
else:
    error = "ไม่ได้ระบุโหมด (mode)" if not mode else f"ไม่รู้จักโหมดที่เลือก: {mode}"
```

- `MODE_DEFS` เก็บป้าย, ฟิลด์, ค่าตั้งต้น และ hint ต่อโหมด
- GET: ไม่มี `mode` หรือ `mode` ว่าง → `divider` (หน้าแรก) · `mode` ที่ไม่รู้จัก → ข้อผิดพลาด
- POST: ไม่มี `mode` หรือ `mode` ว่าง → ข้อผิดพลาด · `mode` ที่ไม่รู้จัก → ข้อผิดพลาด
  ไม่คำนวณ Divider แทน
- ทั้ง GET และ POST ทำ `.strip().lower()` กับ `mode` ก่อนตรวจ ( `/?mode=Fixed` → `fixed` )
- ไม่รับ alias เช่น `voltage-divider`; ค่าที่ถูกต้องคือ `divider`, `fixed`, `emitter`
- ใช้ `Cache-Control: no-store` กับหน้า `/` เพื่อลดโอกาสที่ browser cache
  แสดงผลรอบก่อนเป็นผลรอบใหม่

**หน้า unknown/missing mode:** แสดงเฉพาะข้อความผิดพลาดภาษาไทยกับลิงก์
`กลับไปหน้าเริ่มต้น (Voltage Divider Bias)` — **ไม่แสดง** mode selector,
ฟอร์มคำนวณ หรือ SVG เพราะไม่มีโหมดให้อ้างอิง (ไม่ใช้ค่าตั้งต้น Divider แทน)
โดยส่ง `mode=None`, `raw={}`, `diagram=None`, `result=None` และตอบ HTTP 400
ทั้ง GET และ POST ส่วน known mode ที่อินพุตผิดยังตอบ 200 พร้อมฟอร์มและแผนภาพค่าตั้งต้น

### 6.6 ฟอร์มและผลลัพธ์

- ตัวเลือกโหมดเป็น GET form แยกจากฟอร์มคำนวณ:
  `<select name="mode">` + ปุ่ม `เปลี่ยนโหมด`
  → เลือกแล้วโหลดหน้าใหม่ เห็นเฉพาะช่องของโหมด ไม่ต้องใช้ JavaScript
- ฟอร์มคำนวณเป็น POST และมี `<input type="hidden" name="mode" value="{{ mode }}">`
- ช่องที่แสดงตามโหมดตามตาราง 6.1
- `raw` เก็บเฉพาะค่าที่ผู้ใช้กรอกของฟิลด์ในโหมดนั้น เพื่อให้แก้ไขต่อได้
- หัวข้อผลลัพธ์: `จุดทำงาน DC · <mode label>` (ใช้กับทุกโหมด รวม Divider)
- ข้อผิดพลาด: `<mode label>: <ข้อความ>` (ใช้กับทุกโหมดที่รู้จัก รวม Divider;
  โหมดที่ไม่รู้จักไม่มีป้ายโหมด)
- การเติมป้ายโหมดในหัวข้อ/ข้อผิดพลาดของ Divider เป็นเพียงข้อความ ไม่เปลี่ยน
  ฟิลด์ ค่าคำนวณ แผนภาพ หรือตาราง cross-check ของ Divider
- ผลลัพธ์หลักแสดง `IB, IC, IE, VB, VE, VC, VCE, VBE` เหมือนเดิม
- `VBB`, `RB`, ตาราง Thévenin/nodal, `IC(sat)`, สูตรประมาณ และ `stiff divider`
  แสดงเฉพาะ `mode == "divider"`
- โหมดใหม่แสดงคำเตือนจาก `warnings` และ verdict:
  - active: `โซนแอกทีฟตามแบบจำลอง · VCE = …`
  - model_warning: `แบบจำลอง Forward Active อาจใช้ไม่ได้ · VCE = …`
- verdict ไม่ restate ค่าเกณฑ์ด้วยเลขที่ปัดแล้ว (บทเรียนจาก Lab 2)
- เมื่อเกิดข้อผิดพลาด จะไม่แสดง section ผลลัพธ์เลย และแผนภาพใช้ค่าตั้งต้น
  ของโหมดนั้นพร้อม caption `แผนภาพแสดงค่าตั้งต้น — แก้ไขค่าที่ไม่ถูกต้องก่อน`
- เมื่อสลับโหมดด้วย GET จะไม่มีผลลัพธ์ค้าง (GET ตั้ง `result=None` เสมอ)

### 6.7 แผนภาพ SVG

- Divider: ใช้ markup เดิมทั้งหมด (ป้าย `R1`, `R2`, `RC`, `RE`, `β`, `VCC`)
- Fixed: `VCC` → `RB` → base, `VCC` → `RC` → collector, emitter → ground
  (ไม่มี `RE`) · ป้าย `RB`, `RC`, `β`, `VCC`
- Emitter: เหมือน Fixed แต่มี `RE` ระหว่าง emitter กับ ground · ป้าย `RB`, `RC`, `RE`, `β`, `VCC`
- ทุกป้ายใช้ `format_voltage` / `format_resistance` / `%g` จากค่าของโหมดนั้น
- `diagram` ที่ส่งเข้า template:
  - GET → ค่าตั้งต้นของโหมด
  - POST สำเร็จ → `result.inputs`
  - POST ผิดพลาด → ค่าตั้งต้นของโหมด
- `<title>` ของ SVG ระบุชื่อโหมด และใช้ `role="img"` + `aria-labelledby` เหมือนเดิม

### 6.8 ไฟล์ที่เปลี่ยน

| ไฟล์ | การเปลี่ยนแปลง |
|---|---|
| `bjt.py` | เพิ่ม `FixedInputs`, `EmitterInputs`, `ModeResult`, `validate_fixed`, `validate_emitter`, `analyze_fixed`, `analyze_emitter`; ไม่แตะ Divider |
| `app.py` | เพิ่ม `MODE_DEFS`, `FIXED_DEFAULTS`, `EMITTER_DEFAULTS`, `build_mode_inputs`, dispatch `if/elif`, unknown-mode error, `Cache-Control` |
| `templates/index.html` | mode switcher (GET), ฟิลด์ตามโหมด, ผลลัพธ์ตามโหมด, SVG 3 แบบ |
| `static/style.css` | สไตล์ mode switcher, badge/verdict ของ `model_warning` |
| `test_app.py` | เพิ่ม `"mode": "divider"` ใน `FORM` เท่านั้น |
| `README.md` | ส่วน Lab 03, วิธีรัน, GitHub URL, Commit SHA, ส่วนที่ AI ทำ |
| `docs/validation.md` | ตาราง A1–A5 + ค่าอ้างอิงอิสระ + หลักฐาน Browser |
| `docs/superpowers/specs/2026-11-17-lab03-bjt-bias-modes-design.md` | เอกสารนี้ |

## 7. ค่าอ้างอิง A1–A5 (คำนวณมือจากสมการใบงาน)

ค่าที่ใช้ร่วม: `VCC = 12 V`, `RC = 2.2 kΩ = 2200 Ω`, `β = 100`, `VBE = 0.70 V`
ค่าอ้างอิงเหล่านี้คำนวณด้วยเครื่องคิดเลข/มือจากสมการในหัวข้อ 6.2 ไม่ได้อ่านจากโปรแกรม

| กรณี | โหมดและอินพุต | ค่าอ้างอิง (ยังไม่ปัด) | แสดงผล 3 หลักสำคัญ |
|---|---|---|---|
| A1 | Divider · `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RE = 1 kΩ` | `IC = 1.22983 mA`, `VCE = 8.05225 V` | `1.23 mA`, `8.05 V` |
| A2 | Fixed · `RB = 1 MΩ` | `IC = 1.13000 mA`, `VCE = 9.51400 V` | `1.13 mA`, `9.51 V` |
| A3 | Emitter · `RB = 1 MΩ`, `RE = 1 kΩ` | `IC = 1.02634 mA`, `VCE = 8.70545 V` | `1.03 mA`, `8.71 V` |
| A4 | Emitter · `RB = 1 MΩ`, `RE = 2 kΩ` | `IC = 0.94010 mA`, `VCE = 8.03278 V` | `0.940 mA`, `8.03 V` |
| A5 | Fixed · `RB = 0` | ต้องได้ข้อผิดพลาด ไม่มีผลลัพธ์ | — |

### 7.1 ตัวอย่างการคำนวณ A3 (Emitter Bias)

```
VCC = 12 V, RB = 1,000,000 Ω, RE = 1,000 Ω, β = 100, VBE = 0.70 V

IB  = (12 − 0.70) / (1,000,000 + (100 + 1)(1,000))
    = 11.30 / 1,101,000
    = 1.02634 × 10⁻⁵ A
    = 10.2634 µA

IC  = 100 × 1.02634 × 10⁻⁵ = 1.02634 × 10⁻³ A = 1.02634 mA
IE  = 101 × 1.02634 × 10⁻⁵ = 1.03660 × 10⁻³ A = 1.03660 mA
VE  = 1.03660 × 10⁻³ × 1,000 = 1.03660 V
VB  = 1.03660 + 0.70 = 1.73660 V
VC  = 12 − 1.02634 × 10⁻³ × 2,200 = 9.74205 V
VCE = 9.74205 − 1.03660 = 8.70545 V
```

### 7.2 A1 (Divider) ตรวจสอบไขว้

```
VTH = 12 × 22,000 / (100,000 + 22,000) = 2.16393 V
RTH = (100,000 × 22,000) / 122,000 = 18,032.79 Ω
IB  = (2.16393 − 0.70) / (18,032.79 + 101 × 1,000)
    = 1.46393 / 119,032.79 = 1.22983 × 10⁻⁵ A
IC  = 1.22983 mA
VE  = 101 × 1.22983 × 10⁻⁵ × 1,000 = 1.24213 V
VC  = 12 − 1.22983 × 10⁻³ × 2,200 = 9.29437 V
VCE = 9.29437 − 1.24213 = 8.05225 V
```

A1 ต้องตรงกับผลที่บันทึกจาก Lab 2 **ก่อนแก้โค้ด** (บันทึกผ่าน Browser ตามแผนข้อ 8)
ถ้า Lab 2 เดิมไม่ตรงกับค่าอ้างอิง ให้บันทึกความต่างและปรึกษา TA ก่อนแก้

### 7.3 A4 — ทิศทางที่ต้องทำนาย

เมื่อ `RE` เพิ่มจาก `1 kΩ` เป็น `2 kΩ`:

- ตัวส่วน `RB + (β + 1)RE` เพิ่มจาก `1,101,000 Ω` เป็น `1,202,000 Ω`
  → `IB` และ `IC` **ลดลง** (1.02634 → 0.94010 mA)
- `VE = IE·RE` เพิ่มขึ้นมาก (1.0366 → 1.8990 V)
- `VC = VCC − IC·RC` เพิ่มขึ้นเล็กน้อย (9.7421 → 9.9318 V)
- ดังนั้น `VCE = VC − VE` **ลดลง** (8.7054 → 8.0328 V)

**หมายเหตุสำคัญ:** ค่า A4 ที่เคยประมาณไว้ในบทสนทนาก่อนหน้า (`VCE ≈ 8.98 V`)
ไม่ตรงกับการคำนวณจากสมการ; ค่าที่ถูกต้องตามสมการคือ **8.03 V** เพราะ `VE` เพิ่มขึ้น
มากกว่าที่ `VC` เพิ่มขึ้น เอกสารนี้ใช้ 8.03 V เป็นค่าอ้างอิง และจะให้เจ้าของงานตรวจก่อนรัน

## 8. แผนตรวจรับ

### 8.1 ก่อนแก้โค้ด (A1 baseline)

1. รัน Flask ด้วย `python app.py`
2. เปิด `http://127.0.0.1:5000/` ด้วย OpenCode Browser
3. กรอก Divider: `VCC=12`, `R1=100k`, `R2=22k`, `RC=2.2k`, `RE=1k`, `β=100`, `VBE=0.70`
4. อ่าน `IC` และ `VCE` ที่แสดงจริง บันทึกพร้อม screenshot/ข้อความ
5. เก็บผลนี้ไว้เป็น baseline ของ A1 ใน `docs/validation.md`

### 8.2 หลังแก้โค้ด (A1–A5 ผ่าน OpenCode Browser)

| กรณี | การกระทำใน Browser | เกณฑ์ผ่าน |
|---|---|---|
| A1 | เลือก Divider กรอกค่าเดิม กดคำนวณ | ผลตรงกับ baseline และค่าอ้างอิง ±0.01 mA / ±0.02 V |
| A2 | เลือก Fixed กรอก `RB=1M` (ไม่ต้องมี `RE`) กดคำนวณ | `IC ≈ 1.13 mA`, `VCE ≈ 9.51 V`, ไม่มีช่อง `RE` |
| A3 | เลือก Emitter กรอก `RB=1M`, `RE=1k` กดคำนวณ | มีช่อง `RE`, `IC ≈ 1.03 mA`, `VCE ≈ 8.71 V` |
| A4 | คงโหมด Emitter เปลี่ยนเฉพาะ `RE=2k` กดคำนวณ | `IC` ลดจาก A3 (`≈0.940 mA`), `VCE ≈ 8.03 V` |
| A5 | เลือก Fixed กรอก `RB=0` กดคำนวณ | ข้อความไทยระบุ `RB`, ระบุโหมด Fixed, ไม่มีผลลัพธ์เดิม, หน้าไม่ล่ม |

การอ่านผล: ใช้ `browser_navigate` เปิดหน้า, `browser_snapshot` อ่านชื่อช่อง/ปุ่ม/ผล,
`browser_click` เลือกโหมด/กดคำนวณ, `browser_fill` หรือเครื่องมือกรอกฟอร์มที่ใช้จริง,
และ `browser_screenshot` เก็บหลักฐานอย่างน้อยหนึ่งกรณี

### 8.3 การตรวจเพิ่มเติม (ไม่ใช่ A1–A5)

- GET `/?mode=fixed` → เห็นเฉพาะฟิลด์ Fixed, ไม่มี `RE`, ไม่มีผลลัพธ์ค้าง
- GET `/?mode=emitter` → มี `RE`
- GET `/?mode=bogus` → ข้อผิดพลาด ไม่คำนวณ Divider
- POST `mode=bogus` → ข้อผิดพลาด ไม่คำนวณ Divider
  (ตรวจด้วย HTTP request ตรง เพราะฟอร์มไม่มีตัวเลือกนี้; ระบุว่าไม่ใช่หลักฐาน A1–A5)
- หลัง POST สำเร็จแล้วสลับโหมดด้วย GET → ผลลัพธ์เก่าต้องหายไป
- `python -m unittest` → 52 tests OK

### 8.4 Tolerance

- `IC`: ±0.01 mA เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ
- `VCE`: ±0.02 V เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ
- หน้าจอแสดง 3 หลักสำคัญ จึงต้องเทียบกับค่าอ้างอิงก่อนปัด

## 9. README และ `docs/validation.md`

### README

เพิ่มส่วน Lab 03 ต่อจากส่วน Lab 2:

- สามโหมดและฟิลด์ที่ใช้
- วิธีรัน (`python -m pip install -r requirements.txt`, `python app.py`) และ URL
- วิธีเลือกโหมด (GET form) และการตรวจเฉพาะฟิลด์ของโหมด
- สรุปสมการสั้น ๆ และหน่วย
- ตารางโซน/คำเตือนของโหมดใหม่ (Forward Active อาจใช้ไม่ได้)
- ลิงก์ไป `docs/validation.md`
- GitHub URL และ Commit SHA ของงาน Lab 03
- ส่วน "AI ช่วยอะไร / นักศึกษาตรวจอะไร"

Commit SHA: ใส่ SHA ของ commit ที่มีโค้ด Lab 03 (ไม่ใช่ commit ที่แก้ README เอง
เพราะ SHA ของ commit ใหม่จะเปลี่ยนเมื่อแก้ README) และรายงาน HEAD ล่าสุดในข้อความส่งงาน

### `docs/validation.md`

- ข้อมูลวันเวลา, environment (Windows, Python 3.12.7, Flask 3.1.3), วิธีตรวจ:
  **OpenCode Browser** พร้อมชื่อเครื่องมือที่ใช้จริง
- เหตุผลที่ไม่ได้ใช้ Playwright MCP: เครื่องไม่มี `node`/`npx`
- ตาราง A1–A5: ID, โหมด/อินพุต, ค่าคาดหมาย (ยังไม่ปัด), ผลที่เห็นพร้อมหน่วย,
  วิธีตรวจ, สถานะ (PASS/FAIL/NOT RUN), หลักฐาน
- A1 baseline จาก Lab 2 ก่อนแก้
- ค่าอ้างอิงอิสระของโหมดใหม่ (A3) พร้อมสมการและหน่วยตามหัวข้อ 7.1
- เส้นทางข้อมูลของ A4: `form RE=2k` → `parse_resistance` → `2000 Ω` →
  `EmitterInputs.re` → `analyze_emitter` → `IC`/`VCE` → `format_*` → หน้าเว็บ
- ระบุว่า AI เขียนโค้ดส่วนไหน และนักศึกษาตรวจสมการ/หน่วย/ผลอะไร
- หมายเหตุข้อจำกัดและสิ่งที่ไม่ได้ทำ (เช่น ไม่ได้ใช้ Playwright MCP)

## 10. เทส

- `test_app.py`: เพิ่ม `"mode": "divider"` ใน `FORM` เท่านั้น
  (ทุก POST ใช้ `{**FORM, ...}` จึงได้ mode ครบโดยไม่ต้องแก้ทีละเทส)
- ไม่แก้ `test_bjt.py` และ `test_electrical.py`
- ไม่เพิ่ม unittest ใหม่
- ตรวจพฤติกรรมใหม่ผ่าน OpenCode Browser ตามข้อ 8
- ระหว่างพัฒนาใช้ `python -c` หรือ REPL ตรวจเลขได้ แต่ไม่ commit เป็นเทส

## 11. ความเสี่ยงและการป้องกัน

| ความเสี่ยง | การป้องกัน |
|---|---|
| Divider regress | ไม่แตะฟังก์ชัน Divider; รัน 52 เทส + A1 เทียบ baseline |
| โหมดใหม่รับฟิลด์ผิด | `MODE_DEFS` ระบุฟิลด์ต่อโหมด; ตรวจเฉพาะฟิลด์นั้น |
| ผลรอบก่อนค้าง | GET ตั้ง `result=None`; POST คำนวณใหม่หรือ error; `Cache-Control: no-store` |
| โหมดไม่รู้จักกลายเป็น Divider | `if/elif` + else error; ไม่มี default fallback ใน POST |
| หน่วยผิด | parse เป็น Ω ครั้งเดียว; เก็บ SI ใน `bjt.py`; แปลงที่ display |
| ค่า VCE ≤ 0.2 V ถูกเรียกเป็น Active ปกติ | `region="model_warning"` + verdict/caution + warning |
| ค่าอ้างอิงมาจากโปรแกรม | ใช้สมการมือในหัวข้อ 7; บันทึกที่มาใน validation.md |
| SVG ป้ายไม่ตรงผล | ใช้ `result.inputs` / mode defaults ตัวเดียวกับที่คำนวณ |

## 12. สิ่งที่ตัดสินใจแล้ว / สิ่งที่เหลือให้ builder

### ตัดสินใจแล้ว (จากบทสนทนาและเอกสารนี้)

- ใช้ Approach A
- ขอบเขตครบตามใบงาน
- ค่าอ้างอิงคำนวณมือและให้เจ้าของงานตรวจ
- ตรวจด้วย OpenCode Browser
- ปรับเทสเดิมเพียงเพิ่ม `mode=divider`
- วาด SVG แยก 3 โหมด
- โหมดใหม่คืน dict; app ห่อเป็น `ModeResult` เพื่อให้ template ใช้ attribute
- ใช้ `region="model_warning"` สำหรับ `IB ≤ 0` หรือ `VCE ≤ 0.2 V`
- ไม่คำนวณ `IC(sat)` หรือค่า Cutoff/Saturation ของโหมดใหม่
- ใช้ `Cache-Control: no-store`
- unknown/missing mode: แสดงเฉพาะ error + ลิงก์กลับหน้าเริ่มต้น, ไม่มีฟอร์ม/แผนภาพ, HTTP 400
- เติมป้ายชื่อโหมดในหัวข้อผลลัพธ์และข้อผิดพลาดของทุกโหมด รวม Divider
  (ไม่เปลี่ยนค่าคำนวณ/ฟิลด์/แผนภาพของ Divider)

### เหลือให้ builder

- พิกัด/รูปทรง SVG ของ Fixed และ Emitter
- CSS ของ mode switcher, badge และ verdict
- ถ้อยคำภาษาไทยนอกข้อความที่กำหนดไว้
- ลำดับการ commit และข้อความ commit
- รูปแบบตารางใน `docs/validation.md` (ให้ครบคอลัมน์ตามใบงาน)

## 13. เกณฑ์ยอมรับ

1. `python -m unittest` ผ่าน 52/52 โดยไม่ได้แก้เทสใดนอกจากเพิ่ม `mode=divider` ใน `FORM`
2. GET `/` แสดง Divider ค่าตั้งต้นเหมือน Lab 2 (ฟิลด์, ค่า, แผนภาพ);
   หัวข้อผลลัพธ์มีป้าย `Voltage Divider Bias` ได้
3. GET `/?mode=fixed` และ `/?mode=emitter` แสดงเฉพาะฟิลด์ของโหมดนั้น พร้อมแผนภาพที่ถูกต้อง
4. POST A1 ให้ผลตรง baseline Lab 2 และค่าอ้างอิงมือ (1.23 mA / 8.05 V)
5. POST A2 ให้ 1.13 mA / 9.51 V โดยไม่ต้องกรอก `RE`
6. POST A3 ให้ 1.03 mA / 8.71 V และมีช่อง `RE`
7. POST A4 ให้ 0.940 mA / 8.03 V; `IC` และ `VCE` ลดจาก A3 ตามที่ทำนาย
8. POST A5 (`Fixed`, `RB=0`) แสดงข้อความไทยระบุ `RB` และโหมด Fixed,
   ไม่มีผลลัพธ์, หน้าไม่ล่ม
9. โหมดที่ไม่รู้จัก (GET/POST) แจ้งข้อผิดพลาด ไม่คำนวณ Divider แทน
10. ผลลัพธ์/ข้อผิดพลาดระบุโหมด; ผลรอบก่อนไม่ปรากฏเป็นผลรอบใหม่
11. `docs/validation.md` มีตาราง A1–A5, ค่าอ้างอิงอิสระของโหมดใหม่พร้อมสมการ/หน่วย,
    วิธีตรวจ OpenCode Browser และหลักฐานอย่างน้อยหนึ่งกรณี
12. README มีวิธีรัน, GitHub URL, Commit SHA และระบุส่วนที่ AI ช่วย
13. Push ขึ้น `origin/main` และรายงาน Commit SHA สุดท้าย
