# Requirements vs Implementation — itx_procure_vehicle_parts

> Date: 2026-04-16
> Version: 1.0
> สถานะ: Phase 1 Complete (Manual sync กับ ePart)

---

## สรุปภาพรวม

| สถานะ | ความหมาย |
|--------|----------|
| DONE | ทำเสร็จแล้ว ทดสอบผ่าน |
| PARTIAL | ทำได้บางส่วน มี gap ที่ระบุ |
| MANUAL | ต้องทำด้วยมือผ่าน ePart / LINE (Phase 1) |
| TODO | ยังไม่ได้ทำ รอ Phase ถัดไป |

---

## ข้อ 1: รับออเดอร์ — รับรายการสั่งอะไหล่จากบริษัทประกัน ผ่านระบบ ePart

### สถานะ: DONE (Manual Sync)

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| รับรายการอะไหล่จาก ePart | สร้าง Procure Order ใน Odoo กรอกข้อมูล e-Claim, ePart number, ข้อมูลรถ, รายการอะไหล่ | ยังต้องกรอกด้วยมือ (Phase 1) |
| เลือกบริษัทประกัน | field `partner_id` filter เฉพาะ contact tag "บริษัทประกันภัย" | DONE |
| เลือกอู่ปลายทาง | field `garage_id` filter เฉพาะ contact tag "อู่ซ่อมรถประกัน" | DONE |
| ข้อมูลรถ | free text: Brand, Model, Year, Submodel, Chassis, Plate, Color | DONE |
| Auto-สร้าง Vehicle Spec | ปุ่ม "Create Spec" สร้าง brand → model → generation → spec อัตโนมัติ | DONE |
| รายการอะไหล่ | Part Lines: ชื่ออะไหล่ (free text), Origin (แท้/เทียม/Recon), Condition (default New), จำนวน | DONE |
| Auto-สร้าง Product | เมื่อ save หรือ Send RFQ จะสร้าง product.template + product.product (variant) อัตโนมัติ | DONE |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- API integration กับ ePart/BlueVenture/EMCS เพื่อดึงรายการอัตโนมัติ

---

## ข้อ 2: หาสินค้า — ติดต่อร้านอะไหล่เพื่อขอราคา

### สถานะ: DONE

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| ส่งรายการอะไหล่ไปร้าน | ปุ่ม "Send RFQ" → สร้าง Vendor Quote + Portal Link สำหรับร้านกรอกราคา | DONE |
| ร้านเสนอราคากลับมา | ร้านกรอกผ่าน Portal: ราคา, Part Code, Origin, Condition, Available, Notes | DONE |
| ขอราคาได้กี่ร้าน? | **ไม่จำกัด** — เลือกได้หลายร้านพร้อมกัน filter เฉพาะ contact tag "ร้านขายอะไหล่รถ" | DONE |
| กำหนดเวลาขอใบเสนอราคา | มี Deadline (นาที) — Countdown Timer บน Portal + auto-expire | DONE |
| เอกสารแนบ | tab "Attachments" ใน Vendor Quote สำหรับ upload เอกสาร | DONE |
| ส่งทางไลน์ | Portal Link สามารถ copy ไปส่งทาง LINE ได้ (ด้วยมือ Phase 1) | MANUAL |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- LINE Messaging API — ส่ง Portal Link อัตโนมัติทาง LINE
- LINE Notify — แจ้งเตือนเมื่อร้านตอบราคากลับ

---

## ข้อ 3: เสนอราคา — เลือกร้านอะไหล่

### สถานะ: DONE

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| เงื่อนไข: เสนอราคารวดเร็ว | เห็น `date_quoted` (เวลาที่ร้านตอบ) เทียบกันได้ | DONE |
| เงื่อนไข: ราคาถูกกว่า | เห็น `amount_total` เทียบกันได้ในหน้า Vendor Quotes | DONE |
| กดเลือก vendor | ปุ่ม "Select This Vendor" บน Vendor Quote → state เป็น selected | DONE |
| ร้านเปลี่ยน Origin/Condition | ร้านสามารถเปลี่ยน Origin/Condition ได้ตอนกรอกราคา (เช่น New ไม่มี → Like New) | DONE |
| 1 บิลสั่งได้มากกว่า 1 ร้าน? | **ปัจจุบัน**: 1 Procure Order = 1 Vendor ที่ถูกเลือก → 1 PO | ดูหมายเหตุด้านล่าง |

### หมายเหตุ: 1 บิลหลายร้าน
ปัจจุบันออกแบบให้ 1 Procure Order เลือกได้ 1 ร้าน หากต้องการสั่งจากหลายร้าน มี 2 วิธี:
1. **แยก Procure Order** — สร้างหลายใบ แต่ละใบสั่งคนละร้าน (แนะนำ เพราะ track แยกได้ชัด)
2. **Phase 2**: ปรับให้เลือกได้หลาย vendor ต่อ 1 order → สร้างหลาย PO (ต้อง redesign)

---

## ข้อ 4: อนุมัติ — DP กรอก ePart + ประกันอนุมัติ + confirm ร้านอะไหล่

### สถานะ: DONE (Manual Sync กับ ePart)

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| DP กรอกราคาใน ePart | ต้องทำด้วยมือใน ePart (Phase 1) | MANUAL |
| ประกันอนุมัติ | Insurance Approval Portal — ประกันเห็นรายละเอียดราคา, Origin, Condition, Notes แล้วกด Approve/Reject | DONE |
| Approve → Auto สร้าง SO + PO | กด Approve → สร้าง SO (ขายประกัน) + PO (ซื้อจากร้าน) อัตโนมัติ พร้อม Dropship transfer | DONE |
| Product variant ตาม vendor quote | SO/PO ใช้ variant ตาม origin+condition ที่ร้านเสนอมา (ไม่ใช่ตัวที่สั่งตอนแรก) | DONE |
| Confirm ออเดอร์กับร้านอะไหล่ | PO confirm อัตโนมัติ (status: Purchase Order) — แจ้งร้านด้วย LINE ด้วยมือ Phase 1 | DONE + MANUAL |
| Reject | ประกัน Reject → กลับไป Quoted ให้ DP เลือก vendor ใหม่ | DONE |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- API sync กรอกราคาใน ePart อัตโนมัติ
- LINE แจ้ง confirm ร้านอะไหล่อัตโนมัติ

---

## ข้อ 5: ร้านอะไหล่จัดส่ง — Dropship ไปอู่ + Partial Delivery

### สถานะ: DONE

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| ร้านจัดส่งไปอู่ทั่วประเทศ | Dropship transfer (DS/) — ร้านส่งตรงไปอู่ ไม่ผ่านคลัง DP | DONE |
| SLA ไม่เกิน 3 วันทำการ | field `delivery_deadline` บน Procure Order | DONE (track ได้ แต่ยังไม่มี alert อัตโนมัติ) |
| ค่าขนส่งต่างจังหวัด | สามารถเพิ่มเป็น line item ใน PO ได้ | MANUAL |
| อะไหล่ทยอยส่ง (Partial Delivery) | Odoo standard: ใส่ Done qty < Demand → Validate → Create Backorder → DS ใบที่ 2, 3... | DONE |
| ร้านแจ้งอัปเดตการส่ง ครั้งที่ 1, 2... | แต่ละ DS/ transfer มีสถานะแยก — track ได้ว่าส่งครั้งไหนแล้ว | DONE |
| Auto-update Procure Order → Shipped | เมื่อ DS/ ทุกใบ done → Procure Order เปลี่ยนเป็น "Shipped" อัตโนมัติ | DONE |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- SLA alert/notification เมื่อใกล้ครบกำหนด
- LINE แจ้งสถานะจัดส่งอัตโนมัติ
- ค่าขนส่งแยก field (ไม่ต้องเพิ่มเป็น line item ด้วยมือ)

---

## ข้อ 6: เซ็นรับและอัปโหลดเอกสาร — อู่เซ็นรับ + ร้านนำใบส่งเข้า ePart

### สถานะ: PARTIAL

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| อู่เซ็นรับสินค้า | Validate DS/ transfer ใน Odoo = ยืนยันรับของ | DONE (แต่ไม่มีลายเซ็นดิจิทัล) |
| ร้านนำใบส่งอะไหล่เข้า ePart | ต้องทำด้วยมือใน ePart (Phase 1) | MANUAL |
| เอกสารแนบ (ใบส่งของ) | Vendor Quote มี tab Attachments สำหรับ upload | DONE |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- อู่เซ็นรับผ่าน Portal (ลายเซ็นดิจิทัล)
- Auto upload ใบส่งเข้า ePart ผ่าน API

---

## ข้อ 7: บันทึกข้อความและตรวจสอบ — ตรวจใบส่งสินค้า + กดขอวางบิลใน ePart

### สถานะ: PARTIAL

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| ตรวจใบส่งสินค้าครบถ้วน | DS/ transfer แต่ละใบมีรายการ + จำนวน ตรวจสอบได้ | DONE |
| ตรวจสอบจำนวนเงินถูกต้อง | SO + PO มียอดรวม เทียบกับ Vendor Quote ได้ | DONE |
| กดสถานะขอวางบิลใน ePart | ต้องทำด้วยมือใน ePart (Phase 1) | MANUAL |

---

## ข้อ 8: วางบิลได้ — เจ้าหน้าที่อนุมัติให้ร้านวางบิล

### สถานะ: MANUAL

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| อนุมัติให้ร้านวางบิลได้ | ใน Odoo: ปุ่ม "Create Invoices" ที่ Procure Order (state: shipped) สร้าง Customer Invoice + Vendor Bill อัตโนมัติ | DONE |
| กดอนุมัติใน ePart | ต้องทำด้วยมือใน ePart (Phase 1) | MANUAL |

---

## ข้อ 9: วางบิลและตรวจสอบ — ตรวจ 3 ส่วน + แยก 2 ขาจ่ายเงิน

### สถานะ: DONE

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| ตรวจสอบ 3 ส่วน: ใบแจ้งหนี้, ใบส่งของ, ใบอนุมัติสั่งอะไหล่ | Odoo มีครบ: Customer Invoice (ใบแจ้งหนี้), DS/ transfer (ใบส่งของ), Procure Order (ใบอนุมัติ) — Smart buttons link ถึงกันหมด | DONE |
| ตรวจจำนวนเงิน + ค่าขนส่ง | Invoice/Bill มียอดรวม ตรวจสอบได้ | DONE |
| **ขาที่ 1**: จ่ายเงินร้านอะไหล่ | Vendor Bill → Register Payment (โอนผ่านธนาคาร) | DONE |
| ขาที่ 1: เอกสาร DP ใบส่งของ + ใบแจ้งหนี้ | Vendor Bill (posted) + DS/ transfer = เอกสารครบ | DONE |
| **ขาที่ 2**: เรียกเก็บจากประกัน | Customer Invoice → ส่งให้ประกันจ่าย | DONE |
| ขาที่ 2: กดขอวางบิลใน ePart/BlueVenture | ต้องทำด้วยมือใน ePart (Phase 1) | MANUAL |
| ขาที่ 2: บัญชีออกใบแจ้งหนี้/ใบกำกับ/ใบเสร็จ | Odoo Invoicing: Customer Invoice → Print/Send | DONE |
| Mark as Done | ปุ่ม "Mark as Done" — ตรวจว่า Invoice + Bill ชำระแล้วทั้งคู่ถึงปิดงานได้ | DONE |

---

## ข้อ 10: รวบรวมเอกสารส่งประกันวางบิล ทุกวันจันทร์

### สถานะ: MANUAL

| ความต้องการ | สิ่งที่ทำแล้ว | Gap |
|-------------|--------------|-----|
| รวบรวมใบอนุมัติจาก ePart + ใบแจ้งหนี้/ใบเสร็จ DP | Odoo สามารถ print Customer Invoice ได้ — รวบรวมด้วยมือ Phase 1 | PARTIAL |
| ส่ง บ.ทิพย ทุกวันจันทร์ | ยังไม่มี batch/schedule สำหรับรวบรวมเอกสารอัตโนมัติ | MANUAL |

### สิ่งที่ยังไม่ได้ทำ (Phase 2):
- Batch report: รวม Invoice ที่ต้องวางบิลประจำสัปดาห์
- PDF export รวมเอกสารทั้งหมดเป็นชุด
- Auto reminder ทุกวันจันทร์

---

## สรุป Status ทั้งหมด

| ข้อ | ความต้องการ | สถานะ Odoo | สถานะ ePart |
|-----|------------|------------|-------------|
| 1 | รับออเดอร์ | **DONE** — Procure Order + Part Lines | MANUAL sync |
| 2 | หาสินค้า/ขอราคา | **DONE** — Send RFQ + Portal + Countdown | MANUAL (LINE) |
| 3 | เสนอราคา/เลือกร้าน | **DONE** — Compare + Select Vendor | — |
| 4 | อนุมัติ + Confirm | **DONE** — Approval Portal + Auto SO/PO | MANUAL sync |
| 5 | จัดส่ง Dropship | **DONE** — DS/ + Partial + Auto Shipped | MANUAL (LINE) |
| 6 | เซ็นรับ/อัปโหลด | **PARTIAL** — Validate DS/ (ไม่มีลายเซ็น) | MANUAL sync |
| 7 | ตรวจสอบ/ขอวางบิล | **PARTIAL** — ตรวจใน Odoo ได้ | MANUAL sync |
| 8 | อนุมัติวางบิล | **DONE** — Create Invoices | MANUAL sync |
| 9 | วางบิล 2 ขา | **DONE** — Vendor Bill + Customer Invoice + Payment | MANUAL sync |
| 10 | รวบรวมส่งประกัน | **MANUAL** — Print ได้ แต่ไม่มี batch | MANUAL |

---

## Phase 2 Roadmap (อนาคต)

| ลำดับ | Feature | ข้อที่เกี่ยวข้อง |
|-------|---------|------------------|
| P2-1 | LINE Messaging API — ส่ง Portal Link + แจ้งสถานะอัตโนมัติ | 2, 4, 5 |
| P2-2 | ePart API Integration — ดึงรายการ + sync สถานะ | 1, 4, 6, 7, 8 |
| P2-3 | อู่เซ็นรับผ่าน Portal (ลายเซ็นดิจิทัล) | 6 |
| P2-4 | Multi-vendor ต่อ 1 Procure Order | 3 |
| P2-5 | Batch billing report (รวมเอกสารประจำสัปดาห์) | 10 |
| P2-6 | SLA alert + dashboard | 5 |
| P2-7 | ค่าขนส่งแยก field + คำนวณอัตโนมัติ (กรุงเทพฯ ฟรี / ต่างจังหวัด) | 5 |
