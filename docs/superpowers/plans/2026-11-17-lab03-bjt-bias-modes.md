# Lab 03 — Three BJT Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มโหมด Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียวให้เว็บ Flask เดิม โดยคงผลของ Voltage Divider Bias เดิมไว้ และตรวจ A1–A5 ผ่าน OpenCode Browser

**Architecture:** ใช้ Approach A — เพิ่มฟังก์ชันและ input dataclass ใหม่ใน `bjt.py` โดยไม่แตะ Divider; `app.py` ใช้ `MODE_DEFS` + `if/elif` เลือกโหมดและตรวจเฉพาะฟิลด์ของโหมด; template ใช้ GET form เลือกโหมดและแสดง SVG แยก 3 แบบ ไม่ใช้ JavaScript

**Tech Stack:** Python 3.12, Flask 3.1, Jinja2, unittest (เฉพาะของเดิม), OpenCode Browser

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-bjt-bias-modes-design.md`

## Global Constraints

- ห้ามทำเว็บใหม่ และห้ามย้ายสมการไปไว้ใน HTML/JavaScript
- `bjt.py` ต้องไม่ import Flask
- Divider ต้องให้ผลคำนวณ ฟิลด์ และแผนภาพเหมือน Lab 2 เมื่อกรอกค่าเดิม
- โหมดที่รู้จัก: `divider`, `fixed`, `emitter` (ตัวพิมพ์เล็ก; normalize ด้วย `.strip().lower()`)
- POST ที่ไม่มี `mode` หรือมี `mode` ที่ไม่รู้จัก → error, ห้าม fallback เป็น Divider
- GET ที่ไม่มี `mode` หรือ `mode` ว่าง → `divider`; GET ที่ไม่รู้จัก → error
- ตรวจเฉพาะฟิลด์ของโหมด: Fixed ไม่มี `RE`; Emitter ไม่มี `R1`, `R2`; Divider ไม่มี `RB`
- แปลง kΩ/MΩ เป็น Ω ครั้งเดียวใน `parse_resistance`; `bjt.py` รับ Ω และ V, คืน A และ V
- แสดง V ด้วย `format_voltage`, กระแสด้วย `format_current`, ความต้านทานด้วย `format_resistance`
- `IB ≤ 0` หรือ `VCE ≤ 0.2 V` ในโหมดใหม่ → `region="model_warning"` + คำเตือน; ไม่คำนวณ Cutoff/Saturation ใหม่
- ห้ามเขียน unittest ใหม่; แก้ `test_app.py` ได้เพียงเพิ่ม `"mode": "divider"` ใน `FORM`
- ต้องคงเทสเดิม 52 ตัวให้ผ่าน
- ตรวจ A1–A5 ผ่าน OpenCode Browser; ห้ามใช้ curl/อ่านโค้ดแทนหลักฐาน browser
- ค่าอ้างอิง A1–A5 ตาม spec §7 (A4 VCE = 8.03278 V)

## Review Focus

- POST/GET โหมดไม่รู้จักหรือไม่มี mode ต้องไม่คำนวณ Divider แทน
- ฟิลด์ที่ไม่ใช้ของโหมด (เช่น `RE` ใน Fixed, `R1` ใน Emitter) ต้องไม่ถูกตรวจและไม่ทำให้ error
- `VCE ≤ 0.2 V` ต้องไม่ถูกเรียกเป็น Active ปกติ และต้องมีคำเตือนว่าแบบจำลองอาจใช้ไม่ได้
- Divider ต้องไม่เปลี่ยนผลหลัง refactor `app.py`/template
- หลังสลับโหมดหรือ POST ที่ผิด ต้องไม่มีผลของรอบก่อนค้างอยู่
- ค่า kΩ/MΩ ต้องถูกแปลงเป็น Ω ก่อนเข้าสมการเพียงครั้งเดียว
- ข้อความที่ผู้ใช้กรอกต้องถูก escape ใน HTML (ค่าใน `value` attribute)

---

### Task 0: บันทึก A1 baseline ก่อนแก้โค้ด

**Files:**
- ไม่แก้ไฟล์โค้ด
- บันทึกผลชั่วคราวใน `.superpowers/sdd/2026-11-17-lab03-bjt-bias-modes/progress.md`

**Interfaces:**
- Consumes: แอป Lab 2 ที่ `main` (`cbf5fbe`)
- Produces: ค่า `IC`, `VCE` ของ A1 ก่อนแก้ ใช้เปรียบเทียบใน Task 6

- [ ] **Step 1: เริ่ม Flask**

Run: `python app.py`
Expected: `Running on http://127.0.0.1:5000`

- [ ] **Step 2: เปิดด้วย OpenCode Browser และกรอก A1**

เปิด `http://127.0.0.1:5000/` แล้วกรอก
`VCC=12`, `R1=100k`, `R2=22k`, `RC=2.2k`, `RE=1k`, `β=100`, `VBE=0.70`
กด `คำนวณ`

- [ ] **Step 3: อ่านผลและบันทึก**

อ่าน `IC`, `VCE` จากหน้าเว็บ และ screenshot อย่างน้อยหนึ่งภาพ
Expected ตามสมการมือ: `IC = 1.23 mA`, `VCE = 8.05 V`
ถ้าได้ค่าไม่ตรง ให้บันทึกค่าจริงและความต่างไว้ ไม่แก้โค้ด

- [ ] **Step 4: หยุด Flask**

หยุด process ที่พอร์ต 5000

---

### Task 1: เพิ่มฟังก์ชัน Fixed/Emitter ใน `bjt.py`

**Files:**
- Modify: `bjt.py`
- Test: ไม่เพิ่มเทส; ใช้ `python -c` และ `test_bjt.py` เดิม

**Interfaces:**
- Produces:
  - `FixedInputs(vcc: float, rb: float, rc: float, beta: float, vbe: float)`
  - `EmitterInputs(vcc: float, rb: float, rc: float, re: float, beta: float, vbe: float)`
  - `ModeResult(inputs, ib, ic, ie, vb, ve, vc, vce, region, warnings)`
  - `validate_fixed(inputs: FixedInputs) -> None`
  - `validate_emitter(inputs: EmitterInputs) -> None`
  - `analyze_fixed(inputs: FixedInputs) -> dict[str, object]`
  - `analyze_emitter(inputs: EmitterInputs) -> dict[str, object]`
  - คีย์ของ dict: `ib, ic, ie, vb, ve, vc, vce, region, warnings` (A, V, `str`, `tuple[str, ...]`)

- [ ] **Step 1: เพิ่ม dataclass และ label**

เพิ่ม `FixedInputs`, `EmitterInputs`, `ModeResult` ใน `bjt.py` และเพิ่ม `"rb": "RB"` ใน `_FIELD_LABELS`
ห้ามแก้ `BiasInputs`, `validate`, `analyze`, `BiasResult` หรือ solver เดิม

- [ ] **Step 2: เพิ่ม validator**

`validate_fixed` ตรวจ:
- ทุกฟิลด์ finite → `<FIELD> ต้องเป็นจำนวนจริง`
- `vcc > 0`, `rc > 0`, `rb > 0` → `<FIELD> ต้องมากกว่า 0`
- `beta >= 1` → `β ต้องไม่น้อยกว่า 1`
- `0 <= vbe < vcc` → `VBE ต้องอยู่ระหว่าง 0 ถึง VCC`

`validate_emitter` เหมือนกันและเพิ่ม `re > 0`

- [ ] **Step 3: เพิ่ม `analyze_fixed` / `analyze_emitter`**

ใช้สูตร:
```
Fixed:   ib=(vcc-vbe)/rb;                 ve=0
Emitter: ib=(vcc-vbe)/(rb+(beta+1)*re);   ve=ie*re
ทั้งคู่:  ic=beta*ib; ie=(beta+1)*ib; vb=ve+vbe; vc=vcc-ic*rc; vce=vc-ve
```
`region = "active"` เมื่อ `ib > 0 and vce > VCE_SAT_V`; ไม่เช่นนั้น `"model_warning"`
`warnings`:
- `ib <= 0`: `"IB ≤ 0: แบบจำลอง Forward Active อาจใช้ไม่ได้"`
- `vce <= VCE_SAT_V`: `"VCE ≤ 0.2 V: แบบจำลอง Forward Active อาจใช้ไม่ได้"`

- [ ] **Step 4: ตรวจผลด้วย `python -c`**

Run:
```
python -c "from bjt import *; print(analyze_fixed(FixedInputs(12,1e6,2200,100,0.7))); print(analyze_emitter(EmitterInputs(12,1e6,2200,1000,100,0.7))); print(analyze_emitter(EmitterInputs(12,1e6,2200,2000,100,0.7))); print(analyze_fixed(FixedInputs(12,1e6,11000,100,0.7)))"
```
Expected:
- Fixed: `ic=1.13e-3`, `vce=9.514`, `region='active'`
- Emitter 1k: `ic=1.02634e-3`, `vce=8.70545`
- Emitter 2k: `ic=0.94010e-3`, `vce=8.03278`
- Fixed RC=11k: `vce≈-0.43`, `region='model_warning'`, warnings ไม่ว่าง

- [ ] **Step 5: ตรวจว่า validation ทำงาน**

Run:
```
python -c "from bjt import *; import traceback
for f in (lambda: analyze_fixed(FixedInputs(12,0,2200,100,0.7)), lambda: analyze_emitter(EmitterInputs(12,1e6,2200,0,100,0.7)), lambda: analyze_fixed(FixedInputs(12,1e6,2200,0,0.7))):
    try: f()
    except ValueError as e: print(e)"
```
Expected: ข้อความระบุ `RB`, `RE`, `β` ตามลำดับ

- [ ] **Step 6: รันเทสวิศวกรรมเดิม**

Run: `python -m unittest test_bjt -v`
Expected: 32 tests OK (Divider ไม่เปลี่ยน)

- [ ] **Step 7: Commit**

```bash
git add bjt.py
git commit -m "feat: add fixed and emitter bias solvers"
```

---

### Task 2: เพิ่ม mode dispatch, ฟอร์ม และผลลัพธ์ตามโหมด

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `test_app.py` (เพิ่ม `"mode": "divider"` ใน `FORM` เท่านั้น)

**Interfaces:**
- Consumes: `FixedInputs`, `EmitterInputs`, `ModeResult`, `analyze_fixed`, `analyze_emitter` จาก Task 1
- Produces:
  - `FIXED_DEFAULTS`, `EMITTER_DEFAULTS`
  - `MODE_DEFS: dict[str, dict]` โดยมีคีย์ `label`, `resistance_fields`, `number_fields`, `defaults`, `hint`
  - `DEFAULT_MODE_INPUTS: dict[str, BiasInputs | FixedInputs | EmitterInputs]`
  - `build_mode_inputs(mode: str, form) -> BiasInputs | FixedInputs | EmitterInputs`
  - route `/` รับ `mode` และส่ง `mode`, `mode_label`, `raw`, `result`, `error`, `diagram` ให้ template
  - template แสดงเฉพาะฟิลด์/ผลของโหมด; แผนภาพ Divider ยังใช้ของเดิม (SVG โหมดใหม่ตามใน Task 3)

- [ ] **Step 1: เพิ่มค่าตั้งต้นและ `MODE_DEFS`**

```
divider: label="Voltage Divider Bias", fields r1,r2,rc,re + vcc,beta,vbe, defaults=DEFAULTS
fixed:   label="Fixed Bias", fields rb,rc + vcc,beta,vbe,
         defaults={"vcc":"12","rb":"1M","rc":"2.2k","beta":"100","vbe":"0.70"}
emitter: label="Emitter Bias", fields rb,rc,re + vcc,beta,vbe,
         defaults={"vcc":"12","rb":"1M","rc":"2.2k","re":"1k","beta":"100","vbe":"0.70"}
```

สร้าง `DEFAULT_MODE_INPUTS` หลังนิยาม `build_mode_inputs` โดยใช้ค่า defaults ของแต่ละโหมด

- [ ] **Step 2: เพิ่ม `build_mode_inputs`**

แปลง resistance fields ด้วย `parse_resistance` และ number fields ด้วย `parse_number`
แล้วเลือก dataclass ด้วย `if/elif` ตาม `mode`
`build_inputs` เดิมใช้ต่อได้ในฐานะ wrapper ของ divider

- [ ] **Step 3: แก้ route `/`**

GET:
- `mode = (request.args.get("mode") or "divider").strip().lower()`
- ถ้า `mode not in MODE_DEFS` → render error page (`mode=None`) + HTTP 400
- ถ้าปกติ → `raw = MODE_DEFS[mode]["defaults"]`, `diagram = DEFAULT_MODE_INPUTS[mode]`, `result=None`

POST:
- `mode = (request.form.get("mode") or "").strip().lower()`
- `if mode == "divider": result = analyze(...)`
- `elif mode == "fixed": result = ModeResult(inputs=..., **analyze_fixed(...))`
- `elif mode == "emitter": result = ModeResult(inputs=..., **analyze_emitter(...))`
- `else`: `error = "ไม่ได้ระบุโหมด (mode)"` หรือ `f"ไม่รู้จักโหมดที่เลือก: {mode}"`
- known mode ที่ error: `error = f"{label}: {exc}"`
- `raw` เก็บเฉพาะฟิลด์ของโหมด; `diagram = result.inputs` ถ้าสำเร็จ ไม่เช่นนั้นใช้ defaults ของโหมด
- ใส่ header `Cache-Control: no-store` ทุก response ของ `/`

- [ ] **Step 4: ปรับ template — mode switcher และฟิลด์**

เพิ่ม GET form เหนือฟอร์มคำนวณ:
```html
<form method="get" class="mode-form">
  <label for="mode-select">วงจรไบอัส</label>
  <select id="mode-select" name="mode">
    <option value="divider" ...>Voltage Divider Bias</option>
    <option value="fixed" ...>Fixed Bias</option>
    <option value="emitter" ...>Emitter Bias</option>
  </select>
  <button type="submit">เปลี่ยนโหมด</button>
</form>
```
ใน POST form ใส่ `<input type="hidden" name="mode" value="{{ mode }}">`
แสดงฟิลด์:
- divider: `vcc, r1, r2, rc, re, beta, vbe`
- fixed: `vcc, rb, rc, beta, vbe`
- emitter: `vcc, rb, rc, re, beta, vbe`

- [ ] **Step 5: ปรับ template — หัวข้อ/error/ผลลัพธ์ตามโหมด**

- `<h2>จุดทำงาน DC · {{ mode_label }} ...`
- error แสดง `{{ error }}` (app เติมชื่อโหมดแล้ว)
- ถ้า `mode is none` แสดงเฉพาะ error + ลิงก์ `กลับไปหน้าเริ่มต้น (Voltage Divider Bias)` และไม่แสดงฟอร์ม/แผนภาพ
- ทุกโหมด: `IB, IC, IE, VB, VE, VC, VCE, VBE`
- divider เท่านั้น: `VBB`, `RB`, ตาราง Thévenin/nodal, `IC(sat)`, สูตรประมาณ, `stiff divider`
- โหมดใหม่: verdict active/model_warning และ `warnings`:
  - active: `โซนแอกทีฟตามแบบจำลอง · VCE = …`
  - model_warning: `แบบจำลอง Forward Active อาจใช้ไม่ได้ · VCE = …`
- ใน Task นี้ให้แสดง SVG เฉพาะ `mode == "divider"`; โหมดใหม่จะได้ SVG ใน Task 3

- [ ] **Step 6: เพิ่ม `"mode": "divider"` ใน `FORM` ของ `test_app.py`**

แก้เฉพาะ dict `FORM` (ทุก POST ใช้ `{**FORM, ...}`)

- [ ] **Step 7: รันเทสเดิมทั้งชุด**

Run: `python -m unittest -v`
Expected: 52 tests OK

- [ ] **Step 8: ตรวจ dispatch และการไม่ตรวจฟิลด์ที่ไม่ใช้**

Run:
```
python -c "from app import app; c=app.test_client()
print(c.get('/').status_code)
print(c.get('/?mode=bogus').status_code)
print(c.post('/', data={'mode':'fixed','vcc':'12','rb':'1M','rc':'2.2k','beta':'100','vbe':'0.70'}).status_code)
print(c.post('/', data={'mode':'emitter','vcc':'12','rb':'1M','rc':'2.2k','re':'1k','beta':'100','vbe':'0.70','r1':'abc'}).status_code)
print(c.post('/', data={'vcc':'12','r1':'47k','r2':'10k','rc':'2.2k','re':'1k','beta':'150','vbe':'0.7'}).status_code)"
```
Expected: `200`, `400`, `200`, `200`, `400`
และ POST fixed/emitter ต้องมีข้อความ `1.13 mA` / `1.03 mA` ตามลำดับ

- [ ] **Step 9: Commit**

```bash
git add app.py templates/index.html test_app.py
git commit -m "feat: dispatch bias modes from the form"
```

---

### Task 3: เพิ่ม SVG ของ Fixed และ Emitter

**Files:**
- Modify: `templates/index.html`

**Interfaces:**
- Consumes: `diagram` (หนึ่งใน `BiasInputs`, `FixedInputs`, `EmitterInputs`) และ `mode`
- Produces: SVG 3 แบบ; ป้ายทุกป้ายมาจาก `diagram`

- [ ] **Step 1: คง SVG ของ Divider ไว้ทั้งหมด**

ห้ามเปลี่ยน markup/ป้ายของ Divider (เทสเดิมตรวจ `47.0 kΩ`, `10.0 kΩ`, `2.20 kΩ`, `1.00 kΩ`)

- [ ] **Step 2: เพิ่ม SVG ของ Fixed**

`viewBox="0 0 340 340"`, `role="img"`, `<title>` ระบุ Fixed Bias
ป้าย: `VCC = {{ format_voltage(diagram.vcc) }}`, `RB`, `RC`, `Q1`, `NPN β = {{ "%g"|format(diagram.beta) }}`
ไม่มีป้าย `RE`

- [ ] **Step 3: เพิ่ม SVG ของ Emitter**

เหมือน Fixed แต่มี `RE` ระหว่าง emitter กับ ground และป้าย `RE`

- [ ] **Step 4: แสดงแผนภาพตามโหมด**

`{% if mode == "divider" %} ... {% elif mode == "fixed" %} ... {% elif mode == "emitter" %} ... {% endif %}`
ถ้า error ให้แสดง caption ค่าตั้งต้น

- [ ] **Step 5: ตรวจด้วย Browser**

เปิดทั้ง 3 โหมดและ screenshot
Expected: ป้ายในภาพตรงกับค่าที่กรอก/ค่าตั้งต้น และไม่มีป้ายชนกัน

- [ ] **Step 6: Commit**

```bash
git add templates/index.html
git commit -m "feat: draw fixed and emitter schematics"
```

---

### Task 4: ปรับ CSS ของ mode switcher และสถานะ model_warning

**Files:**
- Modify: `static/style.css`

**Interfaces:**
- Consumes: คลาส `mode-form`, `badge-model`, `verdict-model`
- Produces: หน้าจอที่อ่านได้ทั้งเดสก์ท็อปและมือถือ

- [ ] **Step 1: เพิ่มสไตล์ mode switcher**

จัดเป็นแถวเดียวบนจอกว้างและ wrap บนจอแคบ; ปุ่มใช้สไตล์เดียวกับปุ่มคำนวณ

- [ ] **Step 2: เพิ่มสไตล์ badge/verdict ของ model_warning**

`badge-model` ใช้สี `var(--saturation)`; `verdict-model` ใช้พื้น `var(--warn-bg)` และเส้น `var(--warn-line)`

- [ ] **Step 3: ตรวจด้วย Browser**

เปิด 3 โหมดที่ความกว้างปกติและแคบ
Expected: ไม่มีป้าย/ฟอร์มล้น, verdict อ่านชัด

- [ ] **Step 4: Commit**

```bash
git add static/style.css
git commit -m "style: add mode switcher and model-warning states"
```

---

### Task 5: ตรวจ A1–A5 ผ่าน OpenCode Browser

**Files:**
- ไม่แก้โค้ดใน task นี้ ยกเว้นพบข้อผิดพลาด

**Interfaces:**
- Consumes: แอปที่รันจาก Task 2–4
- Produces: ผลจริงสำหรับ `docs/validation.md`

- [ ] **Step 1: เริ่ม Flask**

Run: `python app.py`

- [ ] **Step 2: A1**

เลือก Divider, กรอก `12 / 100k / 22k / 2.2k / 1k / 100 / 0.70`, กดคำนวณ
Expected: `IC ≈ 1.23 mA`, `VCE ≈ 8.05 V` และตรงกับ baseline Task 0

- [ ] **Step 3: A2**

เลือก Fixed, กรอก `12 / 1M / 2.2k / 100 / 0.70`, กดคำนวณ
Expected: ไม่มีช่อง `RE`, `IC ≈ 1.13 mA`, `VCE ≈ 9.51 V`

- [ ] **Step 4: A3**

เลือก Emitter, กรอก `12 / 1M / 2.2k / 1k / 100 / 0.70`, กดคำนวณ
Expected: มีช่อง `RE`, `IC ≈ 1.03 mA`, `VCE ≈ 8.71 V`

- [ ] **Step 5: A4**

คงโหมด Emitter เปลี่ยนเฉพาะ `RE=2k`, กดคำนวณ
Expected: `IC ≈ 0.940 mA`, `VCE ≈ 8.03 V`; ทั้งคู่ลดจาก A3

- [ ] **Step 6: A5**

เลือก Fixed, กรอก `RB=0`, กดคำนวณ
Expected: ข้อความ `Fixed Bias: RB ต้องมากกว่า 0`, ไม่มีผลลัพธ์, หน้าไม่ล่ม

- [ ] **Step 7: ตรวจ edge cases เพิ่มเติม**

- หลัง A3 สลับโหมดด้วย GET → ไม่มีผลลัพธ์เก่าค้าง
- Fixed `RB=1M`, `RC=11k` → `model_warning` + คำเตือน `VCE ≤ 0.2 V`
- POST `mode=bogus` → error ไม่มีผล Divider (ใช้ HTTP request ตรง; ระบุว่าไม่ใช่หลักฐาน A1–A5)
- POST ไม่มี `mode` → error ไม่มีผล Divider
- Fixed `RB=1M" onload="alert(1)` → error และข้อความถูก escape ไม่หลุดเป็น attribute

- [ ] **Step 8: เก็บหลักฐาน**

Screenshot อย่างน้อย A3 หรือ A5 และบันทึกข้อความผลที่เห็นจริง
ถ้าผลไม่ตรง ให้แก้แล้วรันกรณีที่เกี่ยวข้องซ้ำ

---

### Task 6: เขียน `docs/validation.md`

**Files:**
- Create: `docs/validation.md`

**Interfaces:**
- Consumes: ผลจาก Task 0 และ Task 5
- Produces: เอกสารส่งงานตามใบงาน

- [ ] **Step 1: เขียนส่วนหัวและ environment**

ระบุวันที่, Windows, Python 3.12.7, Flask 3.1.3, วิธีตรวจ **OpenCode Browser**
และเหตุผลที่ไม่ได้ใช้ Playwright MCP (ไม่มี `node`/`npx`)

- [ ] **Step 2: ใส่ตาราง A1–A5**

คอลัมน์: กรณี, โหมด/อินพุต, ค่าคาดหมาย (ยังไม่ปัด), ผลที่เห็นพร้อมหน่วย,
วิธีตรวจ, สถานะ, หลักฐาน
ใช้ค่าจาก spec §7 และผลจริงจาก Task 5

- [ ] **Step 3: ใส่ A1 baseline**

ระบุผล Lab 2 ก่อนแก้และผลหลังแก้ เทียบกัน

- [ ] **Step 4: ใส่ค่าอ้างอิงอิสระ A3**

คัดลอกสมการ/ตัวเลขจาก spec §7.1 พร้อมหน่วย และระบุว่าคำนวณมือก่อนรัน

- [ ] **Step 5: อธิบายเส้นทางข้อมูล A4**

`form RE=2k` → `parse_resistance` → `2000 Ω` → `EmitterInputs.re` →
`analyze_emitter` → `IC/VCE` → `format_current/format_voltage` → หน้าเว็บ

- [ ] **Step 6: ระบุส่วนที่ AI ทำและส่วนที่นักศึกษาตรวจ**

AI: เขียนฟังก์ชัน, dispatch, template, CSS, docs
นักศึกษา: ตรวจสมการ/หน่วย, ตรวจค่าอ้างอิง, ทวนผลบน Browser อย่างน้อยหนึ่งกรณี

- [ ] **Step 7: Commit**

```bash
git add docs/validation.md
git commit -m "docs: record Lab 03 browser validation"
```

---

### Task 7: อัปเดต README และส่งงาน

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: ข้อมูลจาก Task 1–6
- Produces: README ที่มีวิธีรัน, GitHub URL, Commit SHA, ส่วนที่ AI ช่วย

- [ ] **Step 1: เพิ่มส่วน Lab 03**

อธิบาย 3 โหมด, ฟิลด์, สมการย่อ, วิธีเลือกโหมด, คำเตือน Forward Active,
ลิงก์ `docs/validation.md`

- [ ] **Step 2: ใส่ GitHub URL และ Commit SHA**

`https://github.com/B6807757/Gitlab`
ใช้ SHA ของ commit ที่มีโค้ด Lab 03 (ไม่ใช่ commit ที่แก้ README เอง)
และรายงาน HEAD ล่าสุดในข้อความส่งงาน

- [ ] **Step 3: ระบุส่วนที่ AI ช่วย**

เขียนสั้น ๆ ว่า AI เขียนโค้ดส่วนใด และนักศึกษาตรวจสมการ/หน่วย/ผลใด

- [ ] **Step 4: รันเทสทั้งหมดอีกครั้ง**

Run: `python -m unittest -v`
Expected: 52 tests OK

- [ ] **Step 5: ตรวจ diff ก่อน commit**

Run: `git diff` และ `git diff --staged`
Expected: ไม่มี `.venv`, `.env`, credentials หรือไฟล์ขยะ

- [ ] **Step 6: Commit และ push**

```bash
git add README.md
git commit -m "docs: document the three bias modes"
git push origin main
```

- [ ] **Step 7: รายงานผล**

รายงาน GitHub URL, HEAD SHA, ผลเทส 52/52, ตาราง A1–A5,
และหลักฐาน Browser อย่างน้อยหนึ่งกรณี
