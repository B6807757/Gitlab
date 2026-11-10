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
