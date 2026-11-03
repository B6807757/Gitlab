# DC Circuit Calculator

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
