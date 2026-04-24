# Blueprint: As-Is & To-Be Analysis
## ระบบจัดหาอะไหล่รถยนต์ผ่านเคลมประกันภัย

> **Module**: `itx_procure_vehicle_parts` (Odoo 19)
> **Company**: บริษัท ดี พี เซอร์เวย์ แอนด์ลอว์ จำกัด (DP Survey & Law Co., Ltd.)
> **Prepared by**: Chainaris Padungkul + Claude AI
> **Date**: 2026-04-19
> **Version**: 1.0

---

## สารบัญ

1. [Executive Summary](#1-executive-summary)
2. [As-Is: กระบวนการปัจจุบัน](#2-as-is-กระบวนการปัจจุบัน)
3. [To-Be: ระบบใหม่](#3-to-be-ระบบใหม่)
4. [Feature Matrix](#4-feature-matrix)
5. [Workflow Comparison](#5-workflow-comparison)
6. [Module Breakdown](#6-module-breakdown)
7. [Integration Points](#7-integration-points)
8. [Reports & Documents](#8-reports--documents)
9. [Open Questions](#9-open-questions)
10. [Risks & Assumptions](#10-risks--assumptions)
11. [Implementation Phases](#11-implementation-phases)

---

## 1. Executive Summary

### 1.1 วัตถุประสงค์

พัฒนา Odoo 19 module สำหรับ **DP Survey & Law** ซึ่งเป็น **ตัวกลางจัดหาอะไหล่** (Parts Broker) ให้บริษัทประกันภัย เพื่อ:

1. **Digitize** กระบวนการจัดหาอะไหล่ที่ปัจจุบันทำด้วยมือทั้งหมด (โทร/LINE/กระดาษ/Excel)
2. **Automate** การสร้างเอกสาร SO/PO/Invoice/Bill/Dropship ที่ปัจจุบันกรอกซ้ำซ้อน
3. **Centralize** ข้อมูลราคา, สถานะ, เอกสาร ที่ปัจจุบันกระจัดกระจายอยู่หลายช่องทาง
4. **Enable multi-vendor** ให้สั่งอะไหล่จากหลายร้านใน 1 order (ที่ปัจจุบันทำไม่ได้สะดวก)

### 1.2 ขอบเขต

| ขอบเขต | รายละเอียด |
|--------|-----------|
| **ธุรกิจหลัก** | จัดหาอะไหล่รถยนต์ผ่านเคลมประกัน (ePart/BlueVenture/EMCS) |
| **Users** | DP Staff (Odoo Backend), ร้านอะไหล่ (Portal), ประกัน (Portal), อู่ซ่อม (Phase 2 Portal) |
| **Module** | `itx_procure_vehicle_parts` (depends: `itx_info_vehicle`, `sale`, `purchase`, `stock_dropshipping`, `account`, `website`, `mail`) |
| **Phase 1** | Odoo + Manual ePart sync — ฟีเจอร์ครบ flow หลัก |
| **Phase 2** | API integration (ePart, LINE, E-Billing) + Portal อู่ + Dashboard + Reports |

### 1.3 Revenue Model

DP เป็นตัวกลาง — รายได้มาจาก:
- **ค่า Fee** จากบริษัทประกัน (ยังไม่ชัดเจน → ดู Q1-Q5)
- **ส่วนลด %** จาก vendor (ร้านอะไหล่)
- **ไม่มี markup** — ราคาเสนอประกัน = ราคา vendor (assumption → ต้อง confirm)

---

## 2. As-Is: กระบวนการปัจจุบัน

> **แหล่งข้อมูล**: เอกสารการทำงานส่งให้ทีม odoo ver2.pdf (10 ขั้นตอน + ตัวอย่างเอกสารจริง)

### 2.1 Flow หลัก: จัดหาอะไหล่ผ่านเคลมประกัน

```
ePart ──► DP รับเคลม ──► DP ติดต่อร้าน ──► ร้านเสนอราคา ──► DP กรอก ePart
   ──► ประกันอนุมัติ ──► DP confirm ร้าน ──► จัดส่งอู่ ──► ตรวจสอบ+วางบิล
   ──► จ่ายเงิน 2 ขา ──► ปิดงาน
```

#### ขั้นตอนที่ 1: รับออเดอร์

| รายการ | รายละเอียด |
|--------|-----------|
| **Input** | รายการสั่งอะไหล่จากบริษัทประกัน ผ่านระบบ ePart/BlueVenture/EMCS |
| **ข้อมูลที่ได้** | เลข e-Claim, เลข ePart, ข้อมูลรถ (ยี่ห้อ/รุ่น/ปี/VIN/ทะเบียน/สี/cc), ชื่ออู่, รายการอะไหล่ 5-10 รายการ |
| **เครื่องมือ** | ePart (เว็บ BlueVenture) |
| **Output** | DP จดข้อมูลลง Excel/สมุด |
| **จุดอ่อน** | ❌ ไม่มีระบบ track สถานะ, ❌ ข้อมูลไม่เชื่อมกับ flow ถัดไป |

#### ขั้นตอนที่ 2: หาสินค้า — ติดต่อร้านอะไหล่ขอราคา

| รายการ | รายละเอียด |
|--------|-----------|
| **Input** | รายการอะไหล่จากขั้นตอนที่ 1 |
| **วิธีการ** | DP จัดส่งรายการอะไหล่ไปให้ร้านอะไหล่ โดยร้านอะไหล่จะเสนอราคากลับมาในไลน์ |
| **รูปแบบเอกสาร** | ใบรายการอะไหล่ (PDF/กระดาษ) — มีข้อมูลประกัน, ข้อมูลรถ, ตารางอะไหล่ (ลำดับ, หมายเลขอะไหล่, รายการ, ประเภท, จำนวน, ราคา) |
| **เครื่องมือ** | โทรศัพท์ + LINE (ส่งรูป/PDF) |
| **คำถามจากเอกสาร (สีแดง)** | "ของระบบ Odoo สามารถขอราคาได้กี่ร้าน และ มีตั้งกำหนดเวลาในการขอใบเสนอราคาได้ไหม" |
| **Output** | ร้านเขียนราคาลงบนใบรายการ (ด้วยมือ) + เซ็นชื่อ + ส่ง LINE กลับ |
| **จุดอ่อน** | ❌ ใช้เวลามาก (โทรทีละร้าน), ❌ ข้อมูลกระจาย (LINE), ❌ ร้านอาจลืมตอบ |

#### ขั้นตอนที่ 3: เสนอราคา — เลือกร้านอะไหล่

| รายการ | รายละเอียด |
|--------|-----------|
| **เกณฑ์เลือก** | (1) เสนอราคาเร็ว (2) ราคาถูกกว่า |
| **คำถามจากเอกสาร (สีแดง)** | "Odoo 1 บิล สั่งได้มากกว่า 1 ร้าน ทำอย่างไร?" |
| **เครื่องมือ** | ตาเปล่า — ดูกระดาษ/LINE เทียบราคา |
| **จุดอ่อน** | ❌ เปรียบเทียบด้วยตา, ❌ ไม่มี historical data, ❌ เลือกได้แค่ 1 ร้านต่อ order |

#### ขั้นตอนที่ 4: DP กรอก ePart + ประกันอนุมัติ + Confirm ร้าน

| รายการ | รายละเอียด |
|--------|-----------|
| **4a: DP กรอก ePart** | นำราคาที่ร้านเสนอ → กรอกเสนอราคาในระบบ ePart (หน้าจอ EMCS) |
| **4b: ประกันอนุมัติ** | ประกันดูราคาใน ePart → อนุมัติ |
| **4c: DP confirm ร้าน** | หลังอนุมัติ → confirm ออเดอร์กับร้านอะไหล่ |
| **ช่องทาง confirm ร้าน** | **กลุ่มไลน์** (ระบุไว้ในเอกสาร — สีแดง) |
| **Output** | ใบรายการอะไหล่ + ตราประทับ "อนุมัติจัดอะไหล่ค่ะ" |
| **จุดอ่อน** | ❌ กรอก ePart ด้วยมือ (ซ้ำซ้อน), ❌ confirm ร้านด้วย LINE (ไม่มีหลักฐาน formal) |

#### ขั้นตอนที่ 5: ร้านอะไหล่จัดส่ง

| รายการ | รายละเอียด |
|--------|-----------|
| **SLA** | ไม่เกิน 3 วันทำการ |
| **ค่าขนส่ง** | กรุงเทพฯ ส่งฟรี / ต่างจังหวัดมีค่าขนส่ง |
| **Partial Delivery** | หากเกิดกรณีอะไหล่ทยอยส่ง → ร้านต้องแจ้งอัปเดทการส่งอะไหล่ ครั้งที่ 1, ครั้งที่ 2 จนกว่าจะส่งอะไหล่ครบ |
| **การตรวจเช็ค (สีแดง)** | "ทางเรามีการตรวจเช็คกับทางร้านอะไหล่ โดยร้านอะไหล่ต้องแจ้งอัพเดทการส่งอะไหล่" |
| **จุดอ่อน** | ❌ Track สถานะจัดส่งด้วย LINE, ❌ ไม่รู้ว่าส่งครบหรือยัง |

#### ขั้นตอนที่ 6: เซ็นรับและอัปโหลดเอกสาร

| รายการ | รายละเอียด |
|--------|-----------|
| **อู่ทำ** | เซ็นรับสินค้า |
| **ร้านทำ** | นำใบส่งอะไหล่เข้าระบบ ePart |
| **เอกสาร** | ใบส่งสินค้าชั่วคราว (มี Product Code, รายการ, ประเภท, จำนวน, ราคา, ส่วนลด %) |
| **จุดอ่อน** | ❌ เอกสารกระดาษ, ❌ upload ePart ด้วยมือ |

#### ขั้นตอนที่ 7: บันทึกข้อความและตรวจสอบ

| รายการ | รายละเอียด |
|--------|-----------|
| **DP ตรวจ** | ใบส่งสินค้าครบถ้วน + จำนวนเงินถูกต้อง |
| **DP ทำ** | กดสถานะขอวางบิลในระบบ ePart |
| **จุดอ่อน** | ❌ ตรวจสอบด้วยมือ, ❌ ไม่มี auto reconcile |

#### ขั้นตอนที่ 8: วางบิลได้

| รายการ | รายละเอียด |
|--------|-----------|
| **เจ้าหน้าที่ ePart** | กดอนุมัติให้ร้านอะไหล่วางบิลได้ |
| **จุดอ่อน** | ❌ ขั้นตอนนี้อยู่ใน ePart — Odoo ไม่สามารถเข้าถึง |

#### ขั้นตอนที่ 9: วางบิลและตรวจสอบ — แยก 2 ขาจ่ายเงิน

| รายการ | รายละเอียด |
|--------|-----------|
| **ร้านวางบิล** | ร้านวางบิลมาที่บริษัท DP |
| **DP ตรวจ 3 ส่วน** | (1) ใบแจ้งหนี้ (2) ใบส่งของ (3) ใบอนุมัติสั่งอะไหล่ → **ต้องตรงกัน** (รวมจำนวนเงินและค่าขนส่ง) |
| **ขาที่ 1 — จ่ายร้าน** | เอกสาร: ใบส่งของ (DP) + ใบแจ้งหนี้/ใบเสร็จ/ใบกำกับ → บัญชีตั้งหนี้ → โอนผ่านธนาคาร |
| **ขาที่ 2 — เก็บจากประกัน** | กดขอวางบิลใน ePart/BlueVenture → บัญชีออกใบแจ้งหนี้/ใบกำกับ/ใบเสร็จ/ใบอนุมัติสั่งอะไหล่ → นำเข้า E-Billing |
| **จุดอ่อน** | ❌ ตรวจ 3 ส่วนด้วยมือ, ❌ ePart sync ด้วยมือ |

#### ขั้นตอนที่ 10: รวบรวมเอกสารส่งประกัน

| รายการ | รายละเอียด |
|--------|-----------|
| **เอกสาร** | ใบอนุมัติสั่งอะไหล่ (ePart) + ใบแจ้งหนี้/ใบเสร็จ/ใบกำกับ (DP) |
| **ส่งให้** | บ.ทิพย ประกันภัย (ตัวอย่างในเอกสาร) |
| **ความถี่** | **ทุกวันจันทร์** |
| **จุดอ่อน** | ❌ ทำด้วยมือ, ❌ ไม่มี batch report, ❌ เสี่ยงตกหล่น |

### 2.2 ระบบภายนอกที่เกี่ยวข้อง

| ระบบ | เจ้าของ | หน้าที่ | Odoo เชื่อมต่อ? |
|------|---------|---------|----------------|
| ePart | BlueVenture Group | รับเคลม, เสนอราคา, อนุมัติ, วางบิล | ❌ ไม่ (Manual sync) |
| EMCS | BlueVenture Group | Electronic Motor Claim Solution (หน้าจอ) | ❌ ไม่ (Manual sync) |
| E-Billing | BlueVenture Group | วางบิลอิเล็กทรอนิกส์ | ❌ ไม่ (Manual) |
| LINE | LINE Corp | สื่อสาร vendor/ประกัน/อู่ | ❌ ไม่ (Manual) |
| ธนาคาร | ธนาคารพาณิชย์ | โอนเงินจ่ายร้าน | ❌ ไม่ (Manual) |

### 2.3 เอกสารที่ใช้ (As-Is) — จากตัวอย่างใน PDF

| # | เอกสาร | สร้างโดย | ส่งให้ | รูปแบบ |
|---|--------|---------|--------|--------|
| D1 | ใบรายการอะไหล่ (ว่าง) | DP | ร้านอะไหล่ | PDF → LINE |
| D2 | ใบรายการอะไหล่ (กรอกราคาแล้ว) | ร้านอะไหล่ | DP | กระดาษเขียนมือ + เซ็นชื่อ → LINE |
| D3 | เสนอราคาใน ePart/EMCS | DP | ประกัน | หน้าจอ ePart |
| D4 | ใบอนุมัติจัดอะไหล่ (ตราประทับ) | DP | ร้าน/อู่ | กระดาษ |
| D5 | ใบส่งสินค้าชั่วคราว | ร้านอะไหล่ | อู่/DP | กระดาษ (มี Product Code, ส่วนลด) |
| D6 | ใบแจ้งหนี้/ใบกำกับภาษี/ใบเสร็จรับเงิน | DP | ประกัน | กระดาษ (Product Code, ราคา, VAT 7%, Net Amount) |
| D7 | ใบอนุมัติจ่าย (DP-AC-005) | DP ภายใน | บัญชี DP | กระดาษ (รายการ, จำนวนเงิน, ส่วนลด, ลายเซ็น 4 คน) |

### 2.4 Pain Points สรุป

| # | ปัญหา | ผลกระทบ | ความรุนแรง |
|---|-------|---------|-----------|
| P1 | กรอกข้อมูลซ้ำซ้อน (ePart + Excel + LINE + เอกสาร) | เสียเวลา, ผิดพลาด | สูง |
| P2 | ไม่มีระบบ track สถานะ | ลืม follow up, ส่งช้า | สูง |
| P3 | เปรียบเทียบราคาหลายร้านด้วยตา | เลือกร้านไม่ optimal | กลาง |
| P4 | ไม่มี historical data (ประวัติราคา) | benchmark ไม่ได้ | กลาง |
| P5 | เอกสารกระจัดกระจาย | หาเอกสารยาก, reconcile ยาก | สูง |
| P6 | ไม่มี SLA alert | ไม่รู้ว่าใกล้ deadline | กลาง |
| P7 | Partial delivery track ด้วย LINE | ไม่รู้ว่าส่งครบหรือยัง | กลาง |
| P8 | รวบรวมเอกสารวางบิลด้วยมือทุกจันทร์ | เสียเวลา, ตกหล่น | กลาง |

---

## 3. To-Be: ระบบใหม่

### 3.1 Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        Odoo 19 (Backend)                          │
│  ┌──────────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │ itx_info_vehicle │   │    sale       │   │    purchase      │  │
│  │ (Vehicle Spec,   │   │ (Sale Order)  │   │ (Purchase Order) │  │
│  │  Part Origin,    │   │              │   │                  │  │
│  │  Part Condition) │   │              │   │                  │  │
│  └────────┬─────────┘   └──────┬───────┘   └────────┬─────────┘  │
│           │                    │                     │            │
│  ┌────────▼────────────────────▼─────────────────────▼─────────┐  │
│  │            itx_procure_vehicle_parts                        │  │
│  │                                                             │  │
│  │  Procure Order ──► Vendor Quote ──► Select Vendor Wizard   │  │
│  │       │                                    │                │  │
│  │       ▼                                    ▼                │  │
│  │  Auto: SO + POs (multi-vendor) + Dropship + Invoicing      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│           │                                                       │
│  ┌────────▼─────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │ stock_dropshipping│  │   account     │   │     website      │  │
│  │ (Dropship route) │  │ (Invoice/Bill)│   │ (Portal engine)  │  │
│  └──────────────────┘  └──────────────┘   └────────┬─────────┘  │
│                                                     │            │
└─────────────────────────────────────────────────────┼────────────┘
                                                      │
                    ┌─────────────────────────────────┼────────────┐
                    │           Portal (Public, Token-based)       │
                    │                                              │
                    │  /procure/quote/<token>    → Vendor กรอกราคา │
                    │  /procure/approve/<token>  → ประกัน Approve  │
                    │  /procure/delivery/<token> → อู่รับของ (P2)  │
                    └──────────────────────────────────────────────┘

External (Manual Sync - Phase 1):
  ePart/EMCS ←···· DP กรอกมือ ····→ Odoo
  LINE       ←···· DP copy link ···→ Vendor/ประกัน
```

### 3.2 Flow ใหม่ — ทุกขั้นตอน

```
ePart (Manual)            Odoo (DP Staff)              Portal (Vendor/ประกัน)
     │                         │                              │
     │ ① รับเคลม              │                              │
     │ ····················►  │ สร้าง Procure Order           │
     │                        │ กรอก: ประกัน, e-Claim, ePart   │
     │                        │ กรอก: ยี่ห้อ/รุ่น/ปี/VIN      │
     │                        │ กด [Create Spec] (auto)       │
     │                        │ กรอก Part Lines (free text)    │
     │                        │ [State: DRAFT]                │
     │                        │                              │
     │                        │ ② กด [Send RFQ]              │
     │                        │ เลือก vendor N ร้าน           │
     │                        │ ตั้ง deadline (15 min default) │
     │                        │ ─── Portal link ────────────► │
     │                        │ [State: SOURCING]             │
     │                        │                              │ ③ Vendor เปิด link
     │                        │                              │    เห็นรายการอะไหล่
     │                        │                              │    กรอกราคา/Part Code
     │                        │                              │    เปลี่ยน Origin/Condition
     │                        │                              │    ✓ Available / Notes
     │                        │                              │    [Countdown Timer]
     │                        │ ◄── Submit ────────────────── │
     │                        │ [State: QUOTED]               │
     │                        │                              │
     │                        │ ④ กด [Select Vendors]         │
     │                        │    Wizard: ดูราคาทุกร้าน      │
     │                        │    เลือก vendor ทีละ line     │
     │                        │    (auto-suggest ถูกสุด)       │
     │                        │ [State: SELECTED]             │
     │                        │                              │
     │ ⑤ กรอก ePart (มือ)     │                              │
     │ ◄·····················  │ ─── Approval link ─────────► │
     │                        │                              │ ⑥ ประกัน Approve/Reject
     │                        │ ◄── Approve ────────────────  │
     │                        │                              │
     │                        │ ⑦ AUTO:                       │
     │                        │   - สร้าง SO (ขายประกัน)       │
     │                        │   - สร้าง POs (แยกตาม vendor) │
     │                        │   - Resolve variant           │
     │                        │   - Confirm SO + POs          │
     │                        │   - Auto Dropship transfers   │
     │                        │ [State: ORDERED]              │
     │                        │                              │
     │                        │ ⑧ DP validate DS/ transfer    │
     │                        │    (Partial → Backorder)      │
     │                        │    ครบ = auto Shipped          │
     │                        │ [State: SHIPPED]              │
     │                        │                              │
     │                        │ ⑨ กด [Create Invoices]        │
     │                        │   - Customer Invoice (auto)   │
     │                        │   - Vendor Bills (auto, per PO│)
     │                        │   - Auto post                 │
     │                        │ [State: BILLED]               │
     │                        │                              │
     │ ⑩ วางบิล ePart (มือ)   │ Register Payment              │
     │ ◄·····················  │ ขาที่ 1: จ่ายร้าน (Vendor Bill│)
     │                        │ ขาที่ 2: เก็บประกัน (Invoice)  │
     │                        │                              │
     │                        │ ⑪ กด [Mark as Done]           │
     │                        │    ตรวจ payment ครบ 2 ขา       │
     │                        │ [State: DONE]                 │
```

### 3.3 Odoo Models

| Model | Type | หน้าที่ | Records ต่อ Order |
|-------|------|---------|------------------|
| `itx.procure.order` | Custom | เอกสารหลัก — track lifecycle | 1 |
| `itx.procure.order.line` | Custom | รายการอะไหล่ + per-line vendor selection | 5-10 |
| `itx.vendor.quote` | Custom | ใบเสนอราคา (1 quote per vendor) | 2-5 |
| `itx.vendor.quote.line` | Custom | ราคาแต่ละ line per vendor | 5-10 per quote |
| `itx.select.vendor.wizard` | Transient | Wizard เลือก vendor per line | - |
| `itx.send.rfq.wizard` | Transient | Wizard ส่ง RFQ + แสดง portal links | - |
| `sale.order` | Odoo std | SO ขายให้ประกัน | 1 |
| `purchase.order` | Odoo std | PO ซื้อจาก vendor (N ใบ) | 1-5 |
| `stock.picking` | Odoo std | Dropship transfer (DS/) | 1-5+ |
| `account.move` | Odoo std | Invoice (out) + Bill (in) | 1 + N |

### 3.4 Portal (Token-based, ไม่ต้อง Login)

| Portal | URL Pattern | ใครใช้ | Features |
|--------|-------------|--------|----------|
| Vendor Quote | `/procure/quote/<token>` | ร้านอะไหล่ | กรอกราคา, Part Code, Origin/Condition dropdown, Available checkbox, Notes, Countdown Timer |
| Insurance Approval | `/procure/approve/<token>` | ประกัน | ดูราคาแยกตาม vendor (ตาราง), Approve/Reject buttons |
| Garage Receipt | `/procure/delivery/<token>` | อู่ซ่อม | **Phase 2** — tick รับของ, แจ้งปัญหา |

---

## 4. Feature Matrix

### 4.1 As-Is vs To-Be ทุก Feature

| # | Feature | As-Is | To-Be | Status |
|---|---------|-------|-------|--------|
| **รับออเดอร์** | | | | |
| F01 | รับเคลมจาก ePart | กรอกมือจาก ePart | สร้าง Procure Order ใน Odoo (กรอกมือ Phase 1) | **Implemented** |
| F02 | ข้อมูลรถ (Brand/Model/Year/VIN) | จดลง Excel | Free text 4 ช่อง + VIN (required) | **Implemented** |
| F03 | Auto-create Vehicle Spec | ไม่มี | ปุ่ม Create Spec → auto สร้าง Brand/Model/Gen/Spec | **Implemented** |
| F04 | รายการอะไหล่ | จดลง Excel/กระดาษ | Part Lines: free text + Origin + Condition + Qty | **Implemented** |
| F05 | Auto-create Product | ไม่มี | Save → auto สร้าง product.template + variant | **Implemented** |
| F06 | ePart API (auto import เคลม) | - | Auto ดึงเคลม + รายการอะไหล่จาก ePart | **Planned (P2)** |
| **ขอราคา** | | | | |
| F07 | ส่งรายการให้ vendor | โทร/LINE ทีละร้าน | Send RFQ → Portal link หลายร้านพร้อมกัน | **Implemented** |
| F08 | Vendor กรอกราคา | เขียนบนกระดาษ → LINE | Portal form: ราคา, Part Code, Origin/Condition, Available, Notes | **Implemented** |
| F09 | Countdown Timer | ไม่มี | Timer + auto-expire (default 15 min, เปลี่ยนได้) | **Implemented** |
| F10 | LINE API (ส่ง link auto) | - | Auto ส่ง Portal link ทาง LINE | **Planned (P2)** |
| **เลือก Vendor** | | | | |
| F11 | เปรียบเทียบราคา | ดูกระดาษด้วยตา | Wizard: ดูราคาทุกร้าน เลือกทีละ line | **Implemented** |
| F12 | Multi-vendor per order | ไม่ได้ (1 order = 1 ร้าน) | เลือก vendor แยกต่อ line → หลาย PO | **Implemented** |
| F13 | Auto-suggest ราคาถูกสุด | ไม่มี | Wizard pre-select ราคาถูกสุดให้ | **Implemented** |
| **อนุมัติ** | | | | |
| F14 | DP กรอก ePart | กรอกมือใน ePart | กรอกมือใน ePart (Phase 1) | **Manual** |
| F15 | ประกันอนุมัติ | อนุมัติใน ePart | Portal Approval: ดูราคาแยก vendor + Approve/Reject | **Implemented** |
| F16 | Auto SO + POs | กรอก SO/PO ด้วยมือ | Approve → auto SO + POs (grouped by vendor) + confirm | **Implemented** |
| F17 | Variant resolution | ไม่มี | Vendor เปลี่ยน condition → สร้าง/ใช้ correct variant | **Implemented** |
| F18 | ePart API (auto กรอกราคา) | - | Auto sync ราคาเข้า ePart | **Planned (P2)** |
| **จัดส่ง** | | | | |
| F19 | Dropship | ไม่มีระบบ | DS/ transfer (ร้านส่งตรงไปอู่) | **Implemented** |
| F20 | Partial Delivery | Track ด้วย LINE | Validate → Backorder → DS ใบถัดไป | **Implemented** |
| F21 | Auto Shipped state | DP จำเอง | ทุก DS/ done → auto Shipped | **Implemented** |
| F22 | SLA Alert | ไม่มี | แจ้งเตือนใกล้ delivery_deadline | **Planned (P2)** |
| **เซ็นรับ** | | | | |
| F23 | อู่เซ็นรับ | กระดาษ | DP validate DS/ ใน Odoo (ไม่มีลายเซ็น) | **Partial** |
| F24 | Garage Portal (ลายเซ็นดิจิทัล) | - | อู่เปิด link → tick รับของ + e-sign | **Planned (P2)** |
| **วางบิล** | | | | |
| F25 | สร้าง Invoice/Bill | กรอกมือ | กด 1 ปุ่ม → auto Customer Invoice + Vendor Bills | **Implemented** |
| F26 | Payment tracking | จำเอง | Register Payment + ตรวจ paid ครบ 2 ขา | **Implemented** |
| F27 | Mark as Done | ไม่มี | กด Mark as Done (ตรวจ payment ก่อน) | **Implemented** |
| F28 | ePart วางบิล API | กรอกมือ | Auto กดวางบิลใน ePart | **Planned (P2)** |
| **Reports** | | | | |
| F29 | Batch billing report | ทำมือทุกจันทร์ | Auto batch report ประจำสัปดาห์ | **Planned (P2)** |
| F30 | ใบอนุมัติจ่าย (DP-AC-005) | กระดาษ | QWeb report from Odoo | **Planned (P2)** |
| F31 | Dashboard | ไม่มี | Dashboard: track ทุกเคส + SLA + volume | **Planned (P2)** |

---

## 5. Workflow Comparison

### 5.1 As-Is State Machine

```
ไม่มี state machine — DP จำสถานะเอง / ดูจาก ePart
```

| สถานะ (ไม่ formal) | ตัดสินจาก |
|--------------------|----------|
| รอหาร้าน | DP จำเอง |
| ขอราคาแล้ว | ดูจาก LINE ว่าส่งรูปให้ร้านหรือยัง |
| ได้ราคาแล้ว | ดูจาก LINE ว่าร้านตอบมาหรือยัง |
| อนุมัติแล้ว | ดูจาก ePart |
| ส่งแล้ว | ดูจาก LINE ว่าร้านแจ้งหรือยัง |
| วางบิลแล้ว | ดูจาก ePart + เอกสารกระดาษ |

### 5.2 To-Be State Machine (Odoo)

```
DRAFT ──► SOURCING ──► QUOTED ──► SELECTED ──► ORDERED ──► SHIPPED ──► BILLED ──► DONE
  │          │            │          │                                              │
  └──────────┴────────────┴──────────┴──────────────────────────────────► CANCELLED
                          ◄──────────┘ (Reject → กลับ Quoted)
```

| State | Trigger | ย้อนกลับได้? |
|-------|---------|-------------|
| Draft | สร้าง Procure Order | Cancel → Cancelled |
| Sourcing | กด Send RFQ | Cancel |
| Quoted | Vendor submit ≥1 ราย | Cancel |
| Selected | กด Select Vendors (wizard) | Reject → Quoted, Cancel |
| Ordered | ประกัน Approve (auto SO+POs) | Cancel |
| Shipped | DS/ ทุกใบ done (auto) | - |
| Billed | กด Create Invoices | - |
| Done | กด Mark as Done (payment ครบ) | - |
| Cancelled | กด Cancel (ยกเว้น done) | Reset to Draft |

---

## 6. Module Breakdown

### 6.1 Module: `itx_info_vehicle` (Base)

| รายการ | รายละเอียด |
|--------|-----------|
| **Scope** | Vehicle Master Data (Brand/Model/Generation/Spec), Part Origin, Part Condition, Product Template extensions |
| **ใช้โดย** | `itx_procure_vehicle_parts`, `itx_revival_vehicle` |
| **แยก data** | field `source_module` ('procure' / 'revival') ป้องกันข้อมูลปนกัน |
| **Key feature** | `_get_or_create_variant(origin, condition)` — dynamic product variant |

### 6.2 Module: `itx_procure_vehicle_parts` (Core)

| รายการ | รายละเอียด |
|--------|-----------|
| **Scope** | Procure Order lifecycle, Vendor Quote + Portal, Insurance Approval Portal, Auto SO/PO/DS/Invoice |
| **Dependencies** | `itx_info_vehicle`, `sale`, `purchase`, `stock_dropshipping`, `account`, `website`, `mail` |
| **Models** | 6 custom + 1 override (`stock.picking`) |
| **Wizards** | 2 (`send_rfq`, `select_vendor`) |
| **Portal routes** | 5 (vendor quote GET/POST, approval GET/approve/reject) |
| **Cron** | 1 (auto-expire vendor quotes) |

### 6.3 Dependency Map

```
itx_info_vehicle
      │
      ▼
itx_procure_vehicle_parts
      │
      ├──► sale (Sale Order)
      ├──► purchase (Purchase Order)
      ├──► stock_dropshipping (Dropship route + picking type)
      ├──► account (Invoice + Bill)
      ├──► website (Portal engine)
      └──► mail (Chatter + Activity)
```

---

## 7. Integration Points

### 7.1 Odoo Standard Modules ที่ใช้

| Module | ใช้ทำอะไร | Customization |
|--------|----------|---------------|
| `sale` | สร้าง SO ขายให้ประกัน | ไม่ custom — ใช้ standard |
| `purchase` | สร้าง PO ซื้อจาก vendor | ไม่ custom — ใช้ standard |
| `stock_dropshipping` | Dropship route (ร้านส่งตรงไปอู่) | Override `stock.picking.button_validate()` เพื่อ auto-update procure state |
| `account` | Customer Invoice + Vendor Bill + Payment | ไม่ custom — ใช้ standard |
| `website` | Portal engine (QWeb templates, public routes) | Custom templates + controllers |
| `mail` | Chatter + Activity tracking | ไม่ custom — inherit standard |
| `contacts` | Partner tags (ประกัน/ร้าน/อู่) | ใช้ `res.partner.category` standard |

### 7.2 External Systems (Phase 1 = Manual, Phase 2 = API)

| ระบบ | Phase 1 | Phase 2 | API Available? |
|------|---------|---------|---------------|
| ePart/EMCS | Manual sync (กรอก 2 ระบบ) | API: import เคลม, sync ราคา, sync สถานะ | **ยังไม่รู้** — ต้องสอบถาม BlueVenture (Q12) |
| LINE Messaging | Copy link → paste LINE | API: auto ส่ง Portal link + แจ้งสถานะ | มี (LINE Messaging API) |
| E-Billing | Manual | API: auto วางบิลอิเล็กทรอนิกส์ | **ยังไม่รู้** (Q12) |
| ธนาคาร | Manual โอน | - | - |

---

## 8. Reports & Documents

### 8.1 Reports ที่ต้องทำ

| # | Report | สถานะ | รายละเอียด |
|---|--------|-------|-----------|
| R1 | **ใบรายการอะไหล่** (RFQ — ส่งให้ vendor) | **Planned** | QWeb PDF: ข้อมูลเคลม + ตารางอะไหล่ (ปัจจุบันใช้ Portal link แทน) |
| R2 | **ใบอนุมัติจัดอะไหล่** (DP-AC-005) | **Planned** | QWeb PDF: รายการ + จำนวนเงิน + ส่วนลด + ลายเซ็น 4 ตำแหน่ง (ผู้เสนอ/ผู้สั่งซื้อ/ผู้อนุมัติสั่งซื้อ/ผู้อนุมัติ) |
| R3 | **ใบแจ้งหนี้/ใบกำกับภาษี/ใบเสร็จรับเงิน** | **Partial** | Odoo standard Invoice report — อาจต้อง customize format ตาม DP (Q14) |
| R4 | **ใบอนุมัติจ่ายเงิน** (DP internal approval) | **Planned** | QWeb PDF: รายการ PO + จำนวนเงิน + ลายเซ็น (Q18) |
| R5 | **Batch Billing Report** (รวมเอกสารประจำสัปดาห์) | **Planned** | PDF: รวม Invoice ที่ต้องวางบิล ประจำสัปดาห์ แยกตามบริษัทประกัน |
| R6 | **Dashboard / KPI** | **Planned** | Web: จำนวน order, revenue, ค่าเฉลี่ยราคา, SLA compliance, vendor performance |

### 8.2 Mapping เอกสาร As-Is → Odoo

| เอกสาร As-Is | Odoo equivalent | ต้องทำ custom report? |
|-------------|----------------|---------------------|
| ใบรายการอะไหล่ | Vendor Quote Portal (online form) | ไม่ — ใช้ Portal แทนกระดาษ |
| ใบรายการอะไหล่ (กรอกราคาแล้ว) | Vendor Quote (submitted via Portal) | ไม่ — data อยู่ใน Odoo |
| เสนอราคาใน ePart | Procure Order data (Manual sync) | ไม่ — กรอก ePart ด้วยมือ |
| ใบอนุมัติจัดอะไหล่ | **ต้องทำ R2** | ใช่ — QWeb report |
| ใบส่งสินค้าชั่วคราว | DS/ transfer (Delivery Slip) | อาจ customize |
| ใบแจ้งหนี้/ใบกำกับ | Customer Invoice (account.move) | อาจ customize format |
| ใบอนุมัติจ่าย (DP-AC-005) | **ต้องทำ R4** | ใช่ — QWeb report |

---

## 9. Open Questions

> **42 คำถาม** จัดเป็น 8 หมวด — พร้อม Assumption ปัจจุบันที่ระบบใช้อยู่
> คำถามทุกข้อต้อง confirm กับ user ก่อน Phase 2

### หมวด A: Revenue Model / ราคา (5 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q1 | **ราคาที่เสนอให้ประกัน = ราคา vendor เท่ากันเป๊ะ? หรือมี markup/fee?** | ไม่มี markup — SO price = PO price | เพิ่ม field markup % หรือ fee per line, คำนวณ SO price ≠ PO price |
| Q2 | **ค่า Fee DP คิดอย่างไร? (per order / per line / % ของยอด?)** | ไม่มี fee ในระบบ | เพิ่ม fee field + คำนวณใน Invoice |
| Q3 | **ส่วนลดจาก vendor (Discount %) ที่เห็นในใบส่งสินค้า — DP ได้ส่วนลดนี้ หรือส่งต่อให้ประกัน?** | ไม่มี field ส่วนลด | เพิ่ม discount field + คำนวณ net price |
| Q4 | **ราคาที่กรอกใน Portal/ePart — รวม VAT 7% หรือไม่?** | ใช้ Odoo default tax (Untaxed + VAT) | อาจต้อง configure tax rounding / inclusive pricing |
| Q5 | **ค่าขนส่งต่างจังหวัด — DP จ่ายเอง หรือบวกในราคาเสนอประกัน?** | ต้องเพิ่มเป็น line item ด้วยมือ | เพิ่ม field ค่าขนส่ง แยก + auto คำนวณ (กทม ฟรี / ต่างจังหวัด) |

### หมวด B: Workflow / กระบวนการ (8 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q6 | **DP ต้องกรอก ePart ก่อนหรือหลังส่ง approval link ให้ประกัน?** | Odoo approve แยกจาก ePart (ไม่ sync) | ถ้าก่อน → อาจต้องเพิ่ม state "pending_epart" ก่อน selected |
| Q7 | **ประกันอนุมัติ "ใน ePart" แล้วแจ้ง DP? หรือ DP ส่ง approval link Odoo แยก?** | มี Portal approval แยก (อาจซ้ำซ้อนกับ ePart) | ถ้าอนุมัติใน ePart อย่างเดียว → Portal approval อาจไม่จำเป็น, แค่ให้ DP กด approve ใน Odoo |
| Q8 | **ถ้า vendor ไม่มีของบาง line — DP ทำอย่างไร? ส่ง RFQ ให้ร้านอื่นเฉพาะ line ที่ขาด?** | Wizard ข้าม line ที่ mark "ไม่มีของ" | ถ้าต้อง re-quote → เพิ่ม flow "re-send RFQ for specific lines" |
| Q9 | **SLA 3 วัน — นับจากวันไหน? วันอนุมัติ? วัน PO confirm?** | field `delivery_deadline` (user กรอกเอง) | ถ้านับจาก PO confirm → auto-calculate deadline = PO date + 3 business days |
| Q10 | **อะไหล่ไม่ตรง spec / ชำรุด — มี return flow ไหม?** | ไม่มี return flow | เพิ่ม Return/Refund workflow (Receipt → QC → Return → Credit Note) |
| Q11 | **1 เคลม = 1 Procure Order เสมอ? หรือ 1 เคลม อาจมีหลาย order?** | 1:1 (1 order = 1 e-Claim) | ถ้า 1:N → เพิ่ม link field + group by e-Claim |
| Q12 | **DP ใช้ระบบ ePart ของ BlueVenture ทุกเจ้า? หรือบางเจ้าใช้ EMCS?** | ePart = EMCS (ใช้แทนกันได้) | ถ้าต่างกัน → Phase 2 ต้อง implement หลาย connector |
| Q13 | **Confirm ร้านอะไหล่ (หลัง approve) — ร้านต้อง confirm กลับไหม? หรือแค่แจ้ง?** | PO auto confirm (แจ้ง LINE ด้วยมือ) | ถ้าร้านต้อง confirm → เพิ่ม Portal "Vendor Confirm Order" |

### หมวด C: เอกสาร / Accounting (6 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q14 | **ใบแจ้งหนี้/ใบกำกับภาษี ที่ส่งประกัน — ใช้ format Odoo standard ได้ไหม? หรือต้อง custom?** | ใช้ Odoo standard | ถ้า custom → ทำ QWeb report ตาม format DP |
| Q15 | **"ใบอนุมัติจัดอะไหล่" (ตราประทับ) — ต้อง print จาก Odoo ไหม?** | ไม่มี report | ถ้าต้อง → ทำ R2 (QWeb report) |
| Q16 | **"ใบอนุมัติจ่าย" (DP-AC-005) — ต้อง print จาก Odoo ไหม? มี approval flow ภายใน DP ไหม?** | ไม่มี internal approval + ไม่มี report | ถ้าต้อง → เพิ่ม internal approval model + R4 report |
| Q17 | **"ใบส่งสินค้าชั่วคราว" ที่ร้านออก — DP ต้อง upload/เก็บใน Odoo ไหม?** | Vendor Quote มี tab Attachments | ถ้าต้องเก็บบน DS/ transfer → เพิ่ม attachment field |
| Q18 | **เงื่อนไข Payment vendor — จ่ายกี่วัน? มี credit term?** | ไม่มี payment term customize | ถ้ามี → setup Odoo payment terms per vendor |
| Q19 | **วางบิลประกัน "ทุกวันจันทร์" — ทุกเจ้าเหมือนกัน?** | ทุกจันทร์ (assumption) | ถ้าต่างกัน → เพิ่ม billing schedule per insurance company |

### หมวด D: Finance / การเงิน (5 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q20 | **DP จ่ายร้านก่อน เก็บจากประกันทีหลัง? หรือรอประกันจ่ายก่อน?** | ไม่กำหนด (กดจ่ายเมื่อไหร่ก็ได้) | ถ้ามี order → enforce pay vendor before mark done |
| Q21 | **Invoice ประกัน — ต้องแนบเอกสารอะไรบ้าง? (ePart printout? ใบอนุมัติ? ใบส่งของ?)** | ไม่มี auto-attach | ถ้าต้อง → auto-attach related documents to invoice |
| Q22 | **VAT 7% — DP เป็น VAT registered? ต้องออกใบกำกับภาษี?** | Odoo default tax setup | ถ้าไม่ → disable tax / use different tax rule |
| Q23 | **เงินค่าขนส่ง — track แยกจากค่าอะไหล่ไหม?** | รวมกัน (เพิ่มเป็น line item) | ถ้าแยก → เพิ่ม field ค่าขนส่ง + compute total |
| Q24 | **Bank reconciliation — DP ต้อง reconcile ใน Odoo ไหม? หรือแค่ mark paid?** | Register Payment (manual) | ถ้าต้อง reconcile → setup bank feed / import statement |

### หมวด E: Master Data (5 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q25 | **ร้านอะไหล่ที่ DP ใช้ประจำมีกี่ร้าน? มี list ให้ import?** | สร้าง contact ด้วยมือ | ถ้ามี list → prepare CSV import script |
| Q26 | **บริษัทประกันที่ DP ทำงานด้วยมีกี่เจ้า?** | สร้าง contact ด้วยมือ | ถ้ามี list → prepare CSV import script |
| Q27 | **อู่ซ่อมมีกี่แห่ง? มี list ให้ import?** | สร้าง contact ด้วยมือ | ถ้ามี list → prepare CSV import script |
| Q28 | **Origin ที่ใช้ — มีกี่ประเภท? (แท้/เทียม/Recon — มีอื่นอีก?)** | OEM, Aftermarket, Recon | ถ้ามีเพิ่ม → add master data |
| Q29 | **Condition ที่ใช้ — มีกี่ระดับ? (New/Like New/Used — มีอื่นอีก?)** | New, Used, Like New | ถ้ามีเพิ่ม → add master data |

### หมวด F: Product / Part Code (4 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q30 | **Part Code ที่ร้านกรอก — คือรหัสอะไร? OEM part number? Vendor's internal code?** | Free text (vendor กรอกเอง) | ถ้า OEM → อาจ link กับ product master |
| Q31 | **DP มี Part Master (catalog อะไหล่) ไหม? หรือทุกอย่าง free text?** | ทุกอย่าง free text (auto-create product) | ถ้ามี catalog → import + lookup instead of auto-create |
| Q32 | **Product ที่ auto-create — ต้องเก็บยาว? หรือลบได้หลังปิดงาน?** | เก็บไว้ (cleanup orphan เมื่อลบ order) | ถ้าลบ → add cleanup cron or manual purge |
| Q33 | **1 ชื่ออะไหล่ + 1 รุ่นรถ = 1 product template เสมอ? หรืออาจซ้ำ?** | ใช่ (lookup by name + spec_id) | ถ้าอาจซ้ำ → add dedup logic |

### หมวด G: ปริมาณงาน / UX (5 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q34 | **DP ทำ Procure Order กี่ใบต่อวัน?** | ไม่รู้ | ถ้ามาก (50+/day) → ต้อง optimize list view + search |
| Q35 | **แต่ละ order มีกี่ part lines โดยเฉลี่ย?** | 5 lines (จากตัวอย่าง PDF) | ถ้า 20+ → ต้อง optimize wizard UX |
| Q36 | **ส่ง RFQ ให้กี่ร้านต่อ 1 order โดยเฉลี่ย?** | 2-3 ร้าน | ถ้า 10+ → ต้อง batch send + optimize portal |
| Q37 | **Countdown 15 นาที เพียงพอไหม?** | default 15 min (เปลี่ยนได้) | ถ้าน้อยไป → เปลี่ยน default / add reminder |
| Q38 | **DP ต้องการ mobile-friendly UI ไหม? (ทำงานหน้างานด้วยมือถือ?)** | Desktop only | ถ้ามือถือ → optimize responsive + PWA |

### หมวด H: สิทธิ์ / ความปลอดภัย (4 ข้อ)

| # | คำถาม | Assumption ปัจจุบัน | ถ้าตอบต่าง → ต้องแก้อะไร |
|---|-------|-------------------|------------------------|
| Q39 | **DP มีกี่คนที่ใช้ระบบ? ต้องแบ่ง role ไหม? (staff/manager/บัญชี)** | 2 roles: user + stock manager | ถ้าแยกมากกว่า → add custom groups + record rules |
| Q40 | **Portal link (vendor/ประกัน) — ต้อง expire หลังใช้? หรือเปิดดูซ้ำได้ตลอด?** | ดูซ้ำได้ แต่กรอกซ้ำไม่ได้ | ถ้าต้อง expire → add token expiry |
| Q41 | **Insurance Approval Portal — ประกันเห็นชื่อ vendor ไหม? หรือเห็นแค่ราคา?** | **แสดงชื่อ vendor** (ต้อง confirm!) | ถ้าไม่ → ซ่อน vendor name ใน portal template |
| Q42 | **DP ต้อง audit trail ไหม? (ใคร approve/reject เมื่อไหร่)** | Chatter + mail.tracking (Odoo standard) | ถ้าต้องละเอียดกว่า → custom audit log |

---

## 10. Risks & Assumptions

### 10.1 Assumptions (สิ่งที่ระบบ assume ไว้ — ต้อง confirm)

| # | Assumption | Confidence | ถ้าผิด → Impact |
|---|-----------|------------|----------------|
| A1 | DP เป็นตัวกลาง ไม่ markup ราคา (SO price = PO price) | ต่ำ | ต้องเพิ่ม pricing logic |
| A2 | 1 e-Claim = 1 Procure Order (1:1) | กลาง | ต้อง redesign data model |
| A3 | ePart approval กับ Odoo Portal approval เป็นคนละขั้นตอน | ต่ำ | Portal approval อาจซ้ำซ้อน |
| A4 | ร้านอะไหล่มี LINE / สามารถเปิด web browser ได้ | สูง | - |
| A5 | Vendor Quote deadline 15 นาทีเพียงพอ | กลาง | ต้องเปลี่ยน default |
| A6 | อู่ซ่อมไม่ต้อง confirm รับของผ่าน Odoo (DP validate แทน) Phase 1 | กลาง | ถ้าต้อง → เพิ่ม Garage Portal |
| A7 | DP ไม่ต้องออก "ใบอนุมัติจ่าย" (DP-AC-005) จาก Odoo ใน Phase 1 | กลาง | ถ้าต้อง → ทำ QWeb report |
| A8 | ประกันเห็นชื่อ vendor ใน Approval Portal ได้ | ต่ำ | ถ้าไม่ → ซ่อน vendor name |

### 10.2 Risks

| # | ความเสี่ยง | Likelihood | Impact | การลดความเสี่ยง |
|---|-----------|-----------|--------|----------------|
| R1 | **ePart ไม่มี public API** → Phase 2 integration ทำไม่ได้ | กลาง | สูง | สอบถาม BlueVenture เรื่อง API ก่อนเริ่ม Phase 2 |
| R2 | **Portal token ไม่มี auth** → ใครก็เปิด link ได้ถ้ามี URL | ต่ำ | กลาง | Phase 2: เพิ่ม OTP / token expiry / IP whitelist |
| R3 | **Manual ePart sync ซ้ำซ้อน** → user อาจไม่อยากกรอก 2 ระบบ | สูง | กลาง | Phase 2: API integration ลด manual sync |
| R4 | **Odoo auto-PO จาก dropship conflict กับ manual PO** → PO ซ้ำ | ต่ำ | ต่ำ | แก้แล้ว — ใช้ Odoo auto-PO + update vendor/price |
| R5 | **Volume สูง** → Procure Order list ช้า | ต่ำ | กลาง | เพิ่ม filter + group by + pagination |
| R6 | **Vendor ไม่คุ้นเคยกับ Portal** → กรอกผิด/ไม่กรอก | กลาง | กลาง | ทำ Portal UX ให้ง่ายที่สุด + มี helper text |

---

## 11. Implementation Phases

### Phase 1: Core Workflow — **DONE**

| # | Feature | Status |
|---|---------|--------|
| 1.1 | Procure Order + Part Lines + Create Spec | ✅ Done |
| 1.2 | Auto-create Product (from part name + spec) | ✅ Done |
| 1.3 | Send RFQ Wizard + Portal Link + Countdown | ✅ Done |
| 1.4 | Vendor Quote Portal (กรอกราคา + Origin/Condition) | ✅ Done |
| 1.5 | Auto-expire Quotes (Cron) | ✅ Done |
| 1.6 | Select Vendors Wizard (per-line, multi-vendor) | ✅ Done |
| 1.7 | Insurance Approval Portal (Approve/Reject, multi-vendor display) | ✅ Done |
| 1.8 | Auto SO + POs (grouped by vendor) + Dropship | ✅ Done |
| 1.9 | Product Variant Resolution (vendor เปลี่ยน condition) | ✅ Done |
| 1.10 | Partial Delivery + Auto Shipped State | ✅ Done |
| 1.11 | Create Invoices (Customer Invoice + Vendor Bills) | ✅ Done |
| 1.12 | Payment Check + Mark as Done | ✅ Done |
| 1.13 | Orphan Cleanup (delete order → cleanup spec/product) | ✅ Done |

### Phase 2: Reports & UX — **Planned**

| # | Feature | Priority | Effort |
|---|---------|----------|--------|
| 2.1 | QWeb Report: ใบอนุมัติจัดอะไหล่ (R2) | สูง | 2-3 days |
| 2.2 | QWeb Report: ใบอนุมัติจ่ายเงิน DP-AC-005 (R4) | สูง | 2-3 days |
| 2.3 | Custom Invoice format (R3) | กลาง | 2 days |
| 2.4 | Dashboard + KPI (R6) | กลาง | 3-5 days |
| 2.5 | SLA Alert + Notification | กลาง | 2 days |
| 2.6 | Batch Billing Report (R5) | กลาง | 2-3 days |
| 2.7 | Master Data Import (contacts, origins, conditions) | ต่ำ | 1 day |

### Phase 3: Portal & Automation — **Planned**

| # | Feature | Priority | Effort |
|---|---------|----------|--------|
| 3.1 | Garage Portal (อู่เซ็นรับ + ลายเซ็นดิจิทัล) | กลาง | 5-7 days |
| 3.2 | LINE Messaging API (ส่ง link + แจ้งสถานะ auto) | สูง | 5-7 days |
| 3.3 | ค่าขนส่ง แยก field + auto-calculate | ต่ำ | 1-2 days |
| 3.4 | Return/Refund flow | กลาง | 3-5 days |
| 3.5 | Vendor Confirm Order Portal | ต่ำ | 2-3 days |
| 3.6 | Internal Approval Flow (DP-AC-005 workflow) | กลาง | 3-5 days |

### Phase 4: External Integration — **Future**

| # | Feature | Priority | Effort | Dependency |
|---|---------|----------|--------|------------|
| 4.1 | ePart API: Import เคลม + รายการอะไหล่ | สูง | 10-15 days | ePart API access |
| 4.2 | ePart API: Sync ราคาเสนอ + สถานะ | สูง | 5-7 days | ePart API access |
| 4.3 | E-Billing API: Auto วางบิล | สูง | 5-7 days | E-Billing API access |
| 4.4 | Bank Feed Import (bank reconciliation) | ต่ำ | 3-5 days | Bank API/CSV |

---

*End of Document*
