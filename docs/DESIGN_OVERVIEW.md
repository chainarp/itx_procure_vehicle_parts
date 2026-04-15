# ITX Procure Vehicle Parts — Design Overview

> Version: 1.0
> Date: 2026-04-14
> Status: Approved for Development
> Authors: Chainaris (DP) + Claude (AI)

---

## 1. Business Context

บริษัท DP Survey & Law เป็น **ตัวกลาง** จัดหาอะไหล่รถยนต์ให้บริษัทประกันภัย
ผ่านระบบ ePart (BlueVenture / EMCS)

### Revenue Model
- **ค่า Fee** จากลูกค้า (บริษัทประกัน)
- **ส่วนลด %** จาก vendor (ร้านอะไหล่)
- **ไม่มี markup** — ราคาเสนอประกัน = ราคา vendor
- รายละเอียด commission ต้องถาม DP เพิ่มเติม

### External Systems
- **ePart / BlueVenture / EMCS** = Source of Truth (ระบบเคลมประกัน)
- **Odoo** = Workflow + Utility (หาของ) + Accounting (แจ้งหนี้/จ่ายหนี้)
- **LINE Messaging API** = ช่องทางแจ้งเตือน vendor + ส่ง link (Phase ถัดไป)
- **Phase 1**: Manual sync (กรอกข้อมูลด้วยมือทั้ง 2 ระบบ)
- **Phase 2 (อนาคต)**: API integration (ePart + LINE)

### Stakeholders & Portal Access

| Role | ระบบ | ต้อง login? |
|------|------|------------|
| DP Staff | Odoo Backend | ใช่ (user ปกติ) |
| ร้านอะไหล่ (Vendor) | Portal — กรอกราคา | ไม่ต้อง (token URL) |
| ประกัน (Insurance) | Portal — อนุมัติ/reject | ไม่ต้อง (token URL) |
| อู่ซ่อม (Garage) | Portal — รับของ/แจ้งปัญหา | ไม่ต้อง (token URL) |

---

## 2. Data Architecture

### 2.1 Source Module Separation (คนละโลก)

ข้อมูล Vehicle Spec (brand, model, generation, spec) แยกระหว่าง module ด้วย field `source_module`:

| Module | source_module | ลักษณะข้อมูล |
|--------|---------------|-------------|
| `itx_revival_vehicle` | `'revival'` | Curate ดีๆ ครบถ้วน (ใช้ search ขายของ) |
| `itx_procure_vehicle_parts` | `'procure'` | กรอกเร็วตามที่ประกันเรียก (ใช้แล้วทิ้งได้) |

**เหตุผล**: ถ้าปนกัน ข้อมูล procure (กรอกเร็ว อาจ typo) จะปนเปื้อนข้อมูล revival (ต้องแม่นยำ) กลายเป็น "source of false"

Field `source_module` เพิ่มบน:
- `itx.info.vehicle.brand`
- `itx.info.vehicle.model`
- `itx.info.vehicle.generation`
- `itx.info.vehicle.spec`

### 2.2 Vehicle Spec — Auto-create Flow

User กรอก **free text** 4 ช่อง + VIN บน Procure Order:

```
┌─────────────────────────────────────────────────┐
│ Brand:    [TOYOTA        ]                      │
│ Model:    [INNOVA         ]                     │
│ Year:     [2015           ]                     │
│ Submodel: [2.8 V          ]                     │
│ VIN:      [MR0FZ29G4F0... ] ← NOT NULL (required)│
│                                                 │
│           [ Create Spec ]  ← ปุ่ม (active เมื่อกรอกครบ 4 ช่อง) │
└─────────────────────────────────────────────────┘
         ↓ กดปุ่ม
Lookup brand "TOYOTA" (source_module='procure')
  → ไม่เจอ? สร้างใหม่
  → เจอ? ใช้เลย
Lookup model "INNOVA" (+ brand_id)
  → ไม่เจอ? สร้างใหม่
  ...เหมือนกันทุก level...
  → ได้ vehicle_spec_id ผูกกับ Procure Order
```

**Typo correction**: กดปุ่ม Create Spec ได้ซ้ำ — ลบ spec เก่า (ถ้าไม่ถูกใช้ที่อื่น) แล้วสร้างใหม่

### 2.3 Product — Auto-create Flow

User กรอกชื่อ part (free text) ใน Procure Order Line:

```
┌──────────────────────────────────────────────────────┐
│ Part Lines:                                          │
│ # │ Part Description      │ Product    │ Qty │ Price │
│ 1 │ [กิ๊บล๊อกกันชนหน้า  ] │ (auto)     │ 2   │       │
│ 2 │ [ไฟหน้าซ้าย LED     ] │ (auto)     │ 1   │       │
│ 3 │ [กระจกหน้าบานใหญ่   ] │ (auto)     │ 1   │       │
└──────────────────────────────────────────────────────┘
         ↓ ตอน Save หรือ Send RFQ
Lookup product.template by (name + vehicle_spec_id, source_module='procure')
  → ไม่เจอ? สร้างใหม่ (ผูก spec + route dropship + category อะไหล่)
  → เจอ? ใช้เลย
  → เอา product_id ใส่ procure order line
```

**Typo correction**: แก้ `name` ที่ line → save ใหม่ → ถ้าชื่อไม่ตรงกับ product เดิม → ลบเก่า (ถ้าไม่ถูกใช้ที่อื่น) สร้างใหม่

**Dropdown ยังใช้ได้**: `product_id` dropdown มี domain filter เฉพาะ spec ปัจจุบัน สำหรับเลือกของที่เคยสร้างไว้

### 2.4 Cleanup Rules

| Event | สิ่งที่ถูกลบ | เงื่อนไข |
|-------|-------------|----------|
| Delete Procure Order (draft only) | spec, brand, model, gen, product ที่สร้างมา | ถ้าไม่มี order อื่นใช้อยู่ |
| Reset to Draft | vendor quotes ทั้งหมดของ order นี้ | ลบเสมอ (user จะงง ถ้าเก็บไว้) |
| Reset to Draft | procure order lines | **ไม่ลบ** — เก็บไว้ |
| Re-create Spec (กดปุ่มซ้ำ) | spec เก่า | ถ้าไม่มี order อื่นใช้อยู่ |
| Re-save with changed part name | product เก่า | ถ้าไม่มี order อื่นใช้อยู่ |

---

## 3. Core Entities

### 3.1 Procure Order (เอกสารหลัก)

เอกสารร่มที่ track ตั้งแต่รับเคลม จนปิดจบ (ไม่มีหนี้ทั้ง 2 ฝั่ง)

**Header Fields:**
- เลข Procure Order (sequence: PRO-00001)
- บริษัทประกัน (`partner_id` — domain: tag "บริษัทประกัน")
- เลข e-Claim / เลข ePart
- ข้อมูลรถ: 4 textbox (brand, model, year, submodel) + VIN (required) + ปุ่ม Create Spec
- `vehicle_spec_id` (readonly — auto-set จากปุ่ม Create Spec)
- อู่ซ่อม (`garage_id` — domain: tag "อู่ซ่อม")
- วันที่รับ order / กำหนดส่ง
- `approval_token` — token สำหรับ insurance approve ผ่าน portal
- `approval_url` — computed URL สำหรับ copy ส่งให้ประกัน

**State Machine (1 vendor, lifecycle เดียวทั้งเอกสาร):**

```
Draft → Sourcing → Quoted → Selected → Approved → Ordered → Shipped → Billed → Done
  │        │          │         │          │                                       │
  │        │          │         │          └────── auto: SO + PO + confirm         │
  │        │          │         │                                                  │
  └────────┴──────────┴─────────┴──────────────────────────────────► Cancelled
                                │
                                └── Rejected (ประกันไม่อนุมัติ → กลับ Quoted)
```

| State | ความหมาย | Trigger |
|-------|----------|---------|
| Draft | กรอกข้อมูลเคลม + รายการอะไหล่ + Create Spec | — |
| Sourcing | ส่ง RFQ ให้ vendor ประกวดราคา | ปุ่ม Send RFQ (wizard) |
| Quoted | ได้ราคาจาก vendor แล้ว (≥ 1 ราย) | Vendor submit ผ่าน portal / DP กรอกเอง |
| Selected | เลือก vendor แล้ว → สร้าง approval token | ปุ่ม Select This Vendor |
| Approved | ประกัน approve → **auto สร้าง SO + PO + confirm** | Portal approve / DP กด approve |
| Ordered | PO confirmed → vendor กำลังจัดส่ง | Auto (หลัง approve) |
| Shipped | อู่รับของแล้ว (partial ได้) | Portal garage / DP กดรับแทน |
| Billed | วางบิลครบทั้ง 2 ฝั่ง | Manual |
| Done | ปิดจบ — ไม่มีหนี้ | Manual |
| Cancelled | ยกเลิก | ปุ่ม Cancel |

### 3.2 Procure Order Line (รายการอะไหล่)

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | ชื่ออะไหล่ free text (ตามที่ประกันเรียก) |
| `product_id` | Many2one | Auto-create/lookup จาก name + spec |
| `part_type` | Selection | ประเภทอะไหล่ |
| `quantity` | Float | จำนวน |
| `uom_id` | Many2one | หน่วยนับ |
| `price_unit` | Float | ราคาต่อหน่วย (จาก vendor ที่เลือก) |
| `price_subtotal` | Float | Computed |
| `notes` | Text | หมายเหตุ |

> Line ใช้ state จาก header (ทั้งเอกสารเดินด้วย lifecycle เดียว)

### 3.3 Vendor Quote (ใบเสนอราคาจาก vendor)

**Per Vendor, Per Procure Order** — เก็บราคาทุก line ที่ vendor เสนอ

| Field | Type | Description |
|-------|------|-------------|
| `order_id` | Many2one | Procure Order |
| `vendor_id` | Many2one | Vendor (domain: tag "ร้านขายอะไหล่รถ") |
| `portal_token` | Char | UUID — vendor เข้า portal ไม่ต้อง login |
| `portal_url` | Char (computed) | URL พร้อม copy (widget CopyClipboardChar) |
| `quote_deadline` | Datetime | กำหนดเวลาเสนอราคา |
| `date_sent` / `date_quoted` | Datetime | Timestamps |
| `amount_total` | Float (computed) | รวมราคาทุก line |
| `is_selected` | Boolean | เลือก vendor นี้ |
| `attachment_ids` | Many2many | แนบเอกสารเสนอราคา |
| `state` | Selection | draft / sent / quoted / expired / selected / cancelled |

**Vendor Quote Line** — 1 line per procure order line:

| Field | Type | Description |
|-------|------|-------------|
| `procure_line_id` | Many2one | Link กลับไป Procure Order Line |
| `price_unit` | Float | ราคาที่ vendor เสนอ |
| `delivery_date` | Date | vendor กำหนดวันส่ง |
| `is_available` | Boolean | vendor มีของหรือไม่ |
| `notes` | Text | หมายเหตุ |

### 3.4 Contact Tags (res.partner.category)

ใช้ Odoo มาตรฐาน `res.partner.category` แบ่งประเภท Contact:

| Tag | ใช้กับ field | ตัวอย่าง |
|-----|-------------|---------|
| บริษัทประกัน | `partner_id` (Procure Order) | วิริยะ, กรุงเทพประกัน |
| อู่ซ่อม | `garage_id` (Procure Order) | อู่ช่างแจ็ค, อู่รวมช่าง |
| ร้านขายอะไหล่รถ | `vendor_ids` (Send RFQ wizard) | ร้าน ก.อะไหล่, ร้านบีเค |

### 3.5 Odoo Standard Documents (ใช้เลย ไม่สร้างใหม่)

| Document | Model | หน้าที่ใน Flow | สร้างตอนไหน |
|----------|-------|---------------|------------|
| Sale Order | sale.order | ขายให้ประกัน | Auto — ตอน Approve |
| Purchase Order | purchase.order | ซื้อจาก vendor (ข้าม RFQ) | Auto — ตอน Approve |
| Dropship Transfer | stock.picking (DS/) | vendor ส่งของตรงไปอู่ | Auto — ตอน PO confirm |
| Vendor Bill | account.move (in_invoice) | ร้านวางบิล → เราจ่าย | Manual |
| Customer Invoice | account.move (out_invoice) | เราแจ้งหนี้ประกัน | Manual |

---

## 4. Overall Flow

```
บริษัทประกัน              Odoo (DP)                     ร้านอะไหล่           อู่ซ่อม
     │                      │                                │                 │
     │ ① สั่ง (ePart)       │                                │                 │
     │ ·················►   │                                │                 │
     │                      │                                │                 │
     │                      │ ② สร้าง Procure Order          │                 │
     │                      │    กรอก claim info             │                 │
     │                      │    กรอก brand/model/year/VIN   │                 │
     │                      │    กด Create Spec              │                 │
     │                      │    กรอกรายการอะไหล่ (lines)     │                 │
     │                      │    [State: Draft]              │                 │
     │                      │                                │                 │
     │                      │ ③ ส่ง RFQ ให้ vendor            │                 │
     │                      │    กด Send RFQ (เลือก vendor)  │                 │
     │                      │    ได้ portal link + copy       │                 │
     │                      │    ส่ง link ทาง LINE/email      │                 │
     │                      │    เริ่มจับเวลา (15 นาที)       │                 │
     │                      │    [State: Sourcing]           │                 │
     │                      │ ──── LINE/email ─────────────► │                 │
     │                      │                                │                 │
     │                      │ ④ Vendor คลิก link              │                 │
     │                      │    เปิด Portal Form             │                 │
     │                      │    กรอกราคา + กำหนดส่ง           │                 │
     │                      │    (countdown timer)            │                 │
     │                      │    [State: Quoted]              │                 │
     │                      │ ◄──── Portal Submit ─────────── │                 │
     │                      │                                │                 │
     │                      │    (หรือ DP กรอกราคาเอง          │                 │
     │                      │     แล้วกด Mark as Quoted)      │                 │
     │                      │                                │                 │
     │                      │ ⑤ เลือก vendor                  │                 │
     │                      │    กด Select This Vendor        │                 │
     │                      │    ได้ approval link + copy     │                 │
     │                      │    [State: Selected]            │                 │
     │                      │                                │                 │
     │ ⑥ ส่ง link ให้ประกัน  │                                │                 │
     │ ◄── LINE/email ──── │                                │                 │
     │                      │                                │                 │
     │ ⑦ ประกัน approve      │                                │                 │
     │ ── Portal click ──► │                                │                 │
     │   (หรือ reject)      │                                │                 │
     │                      │                                │                 │
     │                      │ ⑧ AUTO: สร้าง SO + PO + confirm │                 │
     │                      │    SO: ขายให้ประกัน             │                 │
     │                      │    PO: ซื้อจาก vendor (ข้าม RFQ)│                 │
     │                      │    DS: Dropship transfer        │                 │
     │                      │    [State: Approved → Ordered]  │                 │
     │                      │ ──── LINE ───────────────────► │                 │
     │                      │                                │                 │
     │                      │ ⑨ Vendor ส่งของไปอู่            │                 │
     │                      │                                │ ── Dropship ──► │
     │                      │                                │                 │
     │                      │ ⑩ อู่รับของ (partial ได้)       │                 │
     │                      │    Portal: tick ชิ้นที่ได้รับ    │                 │
     │                      │    Backorder: ชิ้นที่เหลือ      │                 │
     │                      │    [State: Shipped]             │                 │
     │                      │ ◄──── Portal confirm ──────────────────────────── │
     │                      │    (หรือ DP กดรับแทนอู่)         │                 │
     │                      │                                │                 │
     │                      │ ⑪ วางบิล                        │                 │
     │                      │    Vendor Bill (จ่ายร้าน)       │                 │
     │                      │    Customer Invoice (เก็บประกัน) │                 │
     │                      │    [State: Billed]              │                 │
     │                      │                                │                 │
     │ ◄·· Invoice ··       │ ── Vendor Bill ──────────────► │                 │
     │                      │                                │                 │
     │                      │ ⑫ ปิด Procure Order             │                 │
     │                      │    [State: Done]                │                 │
     │                      │    ไม่มีหนี้ทั้ง 2 ฝั่ง          │                 │

Legend:  ───► = ใน Odoo    ···► = manual (ePart)    ◄─── = portal/external
```

---

## 5. Portal Pages (3 หน้า — ทั้งหมดไม่ต้อง login)

### 5.1 Vendor Quote Portal (ร้านอะไหล่กรอกราคา)

**URL**: `/procure/quote/<token>`

**แสดง:**
- ข้อมูลรถ (brand, model, plate) + ชื่อประกัน
- Countdown timer (JavaScript) — เหลือกี่นาทีกี่วินาที
- ตารางรายการอะไหล่: ชื่อ, จำนวน
- Input: ✅ มีของ, ราคาต่อหน่วย, กำหนดส่ง, หมายเหตุ
- ปุ่ม Submit

**Validation:**
- Backend: `now() > quote_deadline` → reject "หมดเวลาแล้ว"
- Backend: `state != 'sent'` → reject "เสนอราคาแล้ว"
- หลัง submit → state = `quoted`, order state = `quoted`

**Read-only หลัง submit**: แสดงราคาที่กรอก + total

**DP กรอกแทนได้**: เปิด Vendor Quote form → กรอกราคา → กด "Mark as Quoted"

### 5.2 Insurance Approval Portal (ประกันอนุมัติ)

**URL**: `/procure/approve/<token>`

**แสดง:**
- ข้อมูลเคลม: e-Claim, ePart, ข้อมูลรถ, อู่ซ่อม, กำหนดส่ง
- ตารางรายการอะไหล่ + ราคา + กำหนดส่ง + subtotal + total
- **ไม่แสดงชื่อ vendor** (ความลับทางธุรกิจ)
- ปุ่ม **Approve** + ปุ่ม **Reject**

**Approve**: state → `approved` → auto สร้าง SO + PO + confirm
**Reject**: state → `quoted` (DP เลือก vendor ใหม่ / เจรจาราคา)

**DP กดแทนได้**: ปุ่ม "Approve (Insurance)" บน Procure Order form

### 5.3 Garage Receipt Portal (อู่รับของ) — Phase ถัดไป

**URL**: `/procure/delivery/<token>`

**แสดง:**
- ข้อมูลรถ + รายการอะไหล่ที่จะได้รับ
- Checkbox: tick ✅ ชิ้นที่ได้รับแล้ว
- เลือกเหตุผลถ้ามีปัญหา: ของเสียหาย / ผิดรุ่น / ไม่ครบ
- ช่องหมายเหตุ
- ปุ่ม "ยืนยันรับของ"
- ปุ่ม "แจ้งปัญหา" → สร้าง activity/note แจ้ง DP

**Behind the scenes**:
- Portal → set `quantity` (done) บน DS picking move lines
- Validate picking → Odoo auto-create backorder สำหรับชิ้นที่เหลือ
- State → `shipped`

**DP กดแทนได้**: เปิด DS picking → กรอก quantity → Validate

---

## 6. Dropship & Partial Receipt

### 6.1 Dropship — ใช้ Odoo มาตรฐาน (ทาง A)

| Item | Detail |
|------|--------|
| Module | `stock_dropshipping` (already depends) |
| Route | "Dropship" — ตั้งบน Product Category |
| Picking Type | `dropship` (code: DS) |
| Sequence | DS/00001, DS/00002, ... |
| Flow | PO confirm → auto สร้าง DS transfer (Supplier → Customer) |

**ไม่ต้องเขียน code สร้าง dropship transfer** — Odoo ทำให้อัตโนมัติ

Product Category ของอะไหล่ตั้ง route "Dropship" ครั้งเดียว → ครอบคลุมทุก product

### 6.2 Partial Receipt — ใช้ Odoo Backorder

| Field | ความหมาย |
|-------|----------|
| `product_uom_qty` | จำนวนที่สั่ง (expected) |
| `quantity` | จำนวนที่รับจริง (received) |
| `picked` | Boolean — pick แล้วหรือยัง |

**Flow:**
```
DS Transfer: 5 lines (5 ชิ้น)
     ↓
อู่รับได้ 3 ชิ้น → set quantity = done เฉพาะ 3 lines
     ↓
Validate → Odoo ถาม "Create Backorder?"
  ├── Yes → DS ใหม่ (backorder) สำหรับ 2 ชิ้นที่เหลือ
  └── No → cancel ชิ้นที่เหลือ
     ↓
DS เดิม = done, backorder DS = waiting
```

ตั้ง `create_backorder = 'always'` บน Dropship picking type → ไม่ต้องถาม user สร้าง backorder อัตโนมัติ

---

## 7. Auto-create SO + PO (ตอน Approve)

เมื่อ state เปลี่ยนเป็น `approved` (จาก portal หรือ DP กด):

### 7.1 Sale Order (ขายให้ประกัน)

| Field | Value |
|-------|-------|
| Customer | `partner_id` (บริษัทประกัน) |
| Delivery Address | `garage_id` (อู่ซ่อม) |
| Lines | จาก procure order lines (ราคา vendor + ค่า fee DP) |

→ Auto **confirm** SO

### 7.2 Purchase Order (ซื้อจาก vendor)

| Field | Value |
|-------|-------|
| Vendor | selected quote's `vendor_id` |
| Delivery Address | `garage_id` (อู่ — dropship) |
| Lines | จาก selected vendor quote lines (ราคาที่ vendor เสนอ) |

→ Auto **confirm** PO → Odoo auto สร้าง DS transfer

### 7.3 State Transition

```
Selected → Approved → Ordered (all auto in one click)
              │
              ├── Create SO → Confirm SO
              ├── Create PO → Confirm PO → DS Transfer created
              └── Link SO + PO to Procure Order
```

---

## 8. Vendor Quoting System (Timer + Portal)

### 8.1 Timer Mechanism

| Component | วิธีทำ | หน้าที่ |
|-----------|--------|---------|
| `quote_deadline` | Datetime on Vendor Quote | เก็บเวลาหมดอายุ (now + N นาที) |
| Countdown (Frontend) | JavaScript timer บน Portal Form | แสดง "เหลือ 12:34" |
| Validation (Backend) | Python check `deadline < now()` ตอน submit | ตัวจริง — reject ถ้าเกินเวลา |
| Auto-expire (Cron) | `ir.cron` ทุก 1 นาที | เช็ค expired quotes → update state |

### 8.2 Send RFQ Wizard

```
┌───────────────────────────────────┐
│ Send RFQ to Vendors               │
│                                   │
│ Order: PRO-00001                  │
│ Vendors: [ร้าน A] [ร้าน B] [+]   │  ← domain: tag "ร้านขายอะไหล่รถ"
│ Deadline: [15] minutes            │
│                                   │
│ [ Send RFQ ]  [ Cancel ]          │
└───────────────────────────────────┘
         ↓ กด Send RFQ
┌───────────────────────────────────┐
│ RFQ sent!                         │
│ Copy link to send via LINE/email  │
│                                   │
│ Vendor    │ Portal Link       │📋 │  ← CopyClipboardChar widget
│ ร้าน A   │ http://...token1  │📋 │
│ ร้าน B   │ http://...token2  │📋 │
│                                   │
│ [ Close ]                         │
└───────────────────────────────────┘
```

### 8.3 Vendor Quote States

```
Draft → Sent → Quoted → Selected
         │       ↑          │
         │       │          └──► PO Created (after approve)
         │       │
         │       └── DP กด "Mark as Quoted" (กรอกราคาแทน vendor)
         │
         └──► Expired (auto by cron — หมดเวลา)

Cancelled ← ทุก state (ยกเว้น selected)
```

---

## 9. Relationship Diagram

```
                         Procure Order (Header)
                         │  claim info, vehicle spec
                         │  insurance, garage, VIN
                         │  approval_token
                         │
              ┌──────────┼──────────┬──────────┐
              ▼          ▼          ▼          ▼
          Line 1      Line 2     Line 3    Line 4
          (product)   (product)  (product)  (product)
              │          │          │
              │          │          │
     ┌────────┤   ┌──────┤   ┌─────┤
     ▼        ▼   ▼      ▼   ▼     ▼
  Quote-A  Quote-B ...  ...  ...  ...     ← Vendor Quotes (compare)
  (selected)
     │
     ▼
  ┌── Approve ──┐
  ▼              ▼
  SO             PO (vendor A)
  │              │
  │              ▼
  │         DS Transfer (auto)
  │              │
  │              ▼
  │         Garage Receipt (portal / DP)
  │              │
  ├─── Invoice ──┤
  ▼              ▼
  Customer    Vendor
  Invoice     Bill
```

---

## 10. Menu Structure

```
Vehicle Parts (App)
├── Salvage Processing (seq=10, itx_revival_vehicle)
│   ├── Assessments
│   └── ...
├── Procurement (seq=50, itx_procure_vehicle_parts)
│   ├── Procure Orders
│   └── Vendor Quotes
├── Operations (seq=70)
│   ├── Purchases
│   ├── Sales
│   ├── Transfers
│   ├── Manufacturing
│   └── Adjustments
├── Products (seq=80)
│   ├── Products
│   ├── Product Variants
│   ├── Lots / Serial Numbers
│   └── Bills of Materials
└── Configuration (seq=90)
```

---

## 11. Phase Plan

### Phase 1 — Core Workflow + Portal ✅ (In Progress)

- [x] Procure Order model (header + lines)
- [x] Header-level state machine (10 states)
- [x] Vendor Quote model (with deadline, portal token, portal URL)
- [x] Vendor Quote Line model
- [x] Views: form, list, search (Procure Order + Vendor Quote)
- [x] Send RFQ Wizard (เลือก vendor + deadline + แสดง link + copy)
- [x] Vendor Quote Portal — ร้านกรอกราคา (countdown timer, submit, validation)
- [x] DP กรอกแทน vendor (Mark as Quoted)
- [x] Select Vendor → สร้าง approval token
- [x] Insurance Approval Portal — ประกัน approve (ไม่แสดงชื่อ vendor)
- [x] DP approve แทน (ปุ่ม Approve (Insurance))
- [x] CopyClipboardChar widget สำหรับ portal URL
- [x] Contact Tags (ร้านขายอะไหล่รถ, บริษัทประกัน, อู่ซ่อม)
- [x] Menu under Vehicle Parts >> Procurement
- [x] Security (ir.model.access.csv)
- [x] Sequence (PRO-00001)
- [ ] **Reject** บน portal + backend
- [ ] **source_module** field บน brand/model/generation/spec
- [ ] **Create Spec** button (auto-lookup/create)
- [ ] **Product auto-create** (lookup by name + spec)
- [ ] **VIN required** บน Procure Order
- [ ] **action_approve** → auto SO + PO + confirm
- [ ] **Reset to Draft** → ลบ vendor quotes
- [ ] **Delete Procure Order** → cleanup spec/product ที่ไม่ถูกใช้
- [ ] ir.cron auto-expire quotes

### Phase 2 — Garage Portal + Delivery

- [ ] Garage Receipt Portal — อู่ tick รับของ (partial ได้)
- [ ] Garage แจ้งปัญหา (ของเสียหาย / ผิดรุ่น / ไม่ครบ)
- [ ] DP กดรับแทนอู่
- [ ] Dropship backorder auto-create
- [ ] Delivery token generation

### Phase 3 — Accounting Integration

- [ ] Vendor Bill tracking per Procure Order
- [ ] Customer Invoice tracking per Procure Order
- [ ] State "Billed" → auto when both invoices created
- [ ] State "Done" → auto when no outstanding debt

### Phase 4 — LINE Integration

- [ ] LINE Messaging API service class
- [ ] Configuration (token, channel IDs on res.partner)
- [ ] Send RFQ notification via LINE
- [ ] Send expiry notification via LINE
- [ ] Send PO confirmation via LINE
- [ ] Fallback to email

### Phase 5 — ePart Integration (อนาคต)

- [ ] API connection to ePart/EMCS
- [ ] Auto-sync claim data
- [ ] Auto-update status

---

## 12. Technical Dependencies

```python
'depends': [
    'itx_info_vehicle',      # Vehicle spec master data
    'sale',                   # Sale Order
    'purchase',               # Purchase Order
    'stock_dropshipping',     # Dropship route + picking type
    'account',                # Invoice / Bill
    'website',                # Portal controllers + templates
    'mail',                   # Chatter + email
],
```

---

## 13. Resolved Decisions

| # | Question | Decision | Reason |
|---|----------|----------|--------|
| 1 | Spec data — shared or separate? | แยกด้วย `source_module` | Revival ต้อง curate, Procure กรอกเร็ว |
| 2 | Product naming — pre-defined or free text? | Free text + auto-create | ใช้คำเดียวกับประกันเรียก |
| 3 | Dropship — custom or standard? | Standard Odoo (ทาง A) | ไม่ต้องเขียน code สร้าง DS transfer |
| 4 | Partial receipt — custom? | Standard Odoo backorder | ตั้ง create_backorder='always' |
| 5 | Vendor portal — login required? | ไม่ต้อง (token URL) | ร้านอะไหล่ไม่มี Odoo account |
| 6 | Insurance approval — how? | Portal page (token URL) + DP กดแทนได้ | ประกันไม่มี Odoo account |
| 7 | Garage receipt — how? | Portal page (token URL) + DP กดแทนได้ | อู่ไม่มี Odoo account |
| 8 | Show vendor name to insurance? | ไม่แสดง (ความลับ) | DP เป็นตัวกลาง |
| 9 | Send RFQ channel? | Copy link → ส่ง LINE/email เอง (MVP) | LINE API = Phase ถัดไป |
| 10 | Header vs line state? | Header-level (1 vendor, lifecycle เดียวทั้งเอกสาร) | ลดความซับซ้อน |
| 11 | VIN required? | Yes — NOT NULL | ร้านค้าใช้ VIN เป็นหลัก |
| 12 | Reset to Draft behavior? | ลบ vendor quotes, เก็บ procure lines | User จะงงถ้า quote ยังอยู่ |
| 13 | Typo correction — spec? | กด Create Spec ซ้ำ (ลบเก่า สร้างใหม่) | ไม่ต้อง delete order ใหม่ |
| 14 | Typo correction — product? | แก้ชื่อ + save (ลบเก่า สร้างใหม่) | ไม่ต้อง delete line ใหม่ |
