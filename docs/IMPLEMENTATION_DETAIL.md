# ITX Procure Vehicle Parts — Implementation Detail

> Version: 1.0
> Date: 2026-04-14
> Reference: DESIGN_OVERVIEW.md

---

## 1. Models — Field Definitions

### 1.1 itx.procure.order

```python
_name = 'itx.procure.order'
_inherit = ['mail.thread', 'mail.activity.mixin']
_order = 'date_order desc, id desc'
```

| Field | Type | Attrs | Description |
|-------|------|-------|-------------|
| `name` | Char | required, readonly, copy=False, default='New' | Sequence: PRO-00001 |
| `state` | Selection | tracking, copy=False, default='draft' | 10 states (see DESIGN) |
| `partner_id` | Many2one(res.partner) | required, tracking | บริษัทประกัน |
| `eclaim_number` | Char | index, tracking | เลข e-Claim |
| `epart_number` | Char | index, tracking | เลข ePart |
| `vehicle_brand` | Char | | Free text — user กรอก |
| `vehicle_model` | Char | | Free text — user กรอก |
| `vehicle_year` | Char | | Free text — user กรอก |
| `vehicle_submodel` | Char | | Free text — user กรอก |
| `vehicle_chassis` | Char | **required**, index | VIN — NOT NULL |
| `vehicle_plate` | Char | | ทะเบียนรถ |
| `vehicle_color` | Char | | สี |
| `vehicle_spec_id` | Many2one(itx.info.vehicle.spec) | readonly | Auto-set จากปุ่ม Create Spec |
| `garage_id` | Many2one(res.partner) | | อู่ซ่อม (delivery address) |
| `date_order` | Datetime | required, default=now | วันที่รับ order |
| `delivery_deadline` | Date | | กำหนดส่ง |
| `line_ids` | One2many(itx.procure.order.line) | copy=True | รายการอะไหล่ |
| `vendor_quote_ids` | One2many(itx.vendor.quote) | | ใบเสนอราคาทั้งหมด |
| `vendor_quote_count` | Integer | compute | นับ vendor quotes |
| `sale_order_id` | Many2one(sale.order) | copy=False | SO ที่สร้าง (1 per order) |
| `purchase_order_id` | Many2one(purchase.order) | copy=False | PO ที่สร้าง (1 per order) |
| `approval_token` | Char | copy=False | UUID — สร้างตอน Select Vendor |
| `approval_url` | Char | compute | URL สำหรับ insurance approve |
| `notes` | Html | | Internal notes |

### 1.2 itx.procure.order.line

```python
_name = 'itx.procure.order.line'
_order = 'sequence, id'
```

| Field | Type | Attrs | Description |
|-------|------|-------|-------------|
| `order_id` | Many2one(itx.procure.order) | required, ondelete='cascade' | Parent |
| `sequence` | Integer | default=10 | ลำดับ |
| `product_id` | Many2one(product.product) | | Auto-create/lookup จาก name + spec |
| `name` | Char | required | ชื่ออะไหล่ free text (ตามที่ประกันเรียก) |
| `part_type` | Selection | | ประเภทอะไหล่ |
| `quantity` | Float | default=1 | จำนวน |
| `uom_id` | Many2one(uom.uom) | | หน่วยนับ |
| `price_unit` | Float | | ราคาต่อหน่วย |
| `price_subtotal` | Float | compute, store | quantity × price_unit |
| `notes` | Text | | หมายเหตุ |

### 1.3 itx.vendor.quote

```python
_name = 'itx.vendor.quote'
_inherit = ['mail.thread']
_order = 'create_date desc, id desc'
```

| Field | Type | Attrs | Description |
|-------|------|-------|-------------|
| `name` | Char | compute, store | "PRO-00001 / ร้าน A" |
| `order_id` | Many2one(itx.procure.order) | required, ondelete='cascade' | Parent |
| `vendor_id` | Many2one(res.partner) | required, tracking | Vendor |
| `state` | Selection | tracking, copy=False, default='draft' | 6 states |
| `quote_deadline` | Datetime | | กำหนดเวลาเสนอราคา |
| `date_sent` | Datetime | | วันที่ส่ง |
| `date_quoted` | Datetime | | วันที่ vendor กรอก |
| `portal_token` | Char | copy=False, default=uuid4 | Token สำหรับ portal |
| `portal_url` | Char | compute | URL + CopyClipboardChar widget |
| `line_ids` | One2many(itx.vendor.quote.line) | | ราคาแต่ละ line |
| `amount_total` | Float | compute, store | sum of line subtotals |
| `attachment_ids` | Many2many(ir.attachment) | | แนบเอกสาร |
| `is_selected` | Boolean | default=False | เลือก vendor นี้ |
| `notes` | Text | | หมายเหตุ |

### 1.4 itx.vendor.quote.line

```python
_name = 'itx.vendor.quote.line'
_order = 'sequence, id'
```

| Field | Type | Attrs | Description |
|-------|------|-------|-------------|
| `quote_id` | Many2one(itx.vendor.quote) | required, ondelete='cascade' | Parent |
| `procure_line_id` | Many2one(itx.procure.order.line) | required, ondelete='cascade' | Link to procure line |
| `sequence` | Integer | default=10 | ลำดับ |
| `name` | Char | related='procure_line_id.name', readonly | ชื่อ part |
| `quantity` | Float | related='procure_line_id.quantity', readonly | จำนวน |
| `price_unit` | Float | | ราคาที่ vendor เสนอ |
| `price_subtotal` | Float | compute, store | quantity × price_unit |
| `delivery_date` | Date | | vendor กำหนดวันส่ง |
| `is_available` | Boolean | default=True | vendor มีของ |
| `notes` | Text | | หมายเหตุ |

### 1.5 itx.send.rfq.wizard (TransientModel)

| Field | Type | Description |
|-------|------|-------------|
| `order_id` | Many2one(itx.procure.order) | Procure Order |
| `vendor_ids` | Many2many(res.partner) | domain: tag "ร้านขายอะไหล่รถ" |
| `quote_deadline_minutes` | Integer | default=15 |
| `state` | Selection | 'draft' / 'done' |
| `created_quote_ids` | Many2many(itx.vendor.quote) | Quotes ที่สร้าง (แสดง portal URL) |

---

## 2. Methods — Business Logic

### 2.1 Procure Order

#### `action_create_spec(self)`
ปุ่ม Create Spec — auto-lookup/create vehicle spec

```
Input: vehicle_brand, vehicle_model, vehicle_year, vehicle_submodel (free text)
Logic:
  1. Validate: ต้องกรอกครบ 4 ช่อง
  2. ถ้ามี vehicle_spec_id เดิม → ลบ (ถ้าไม่ถูกใช้ที่อื่น) พร้อม brand/model/gen ที่ orphan
  3. Lookup/create brand (name=vehicle_brand, source_module='procure')
  4. Lookup/create model (name=vehicle_model, brand_id=brand, source_module='procure')
  5. Lookup/create generation (name=vehicle_year, model_id=model, source_module='procure')
  6. Lookup/create spec (name=vehicle_submodel, generation_id=gen, source_module='procure')
  7. Set self.vehicle_spec_id = spec
Output: vehicle_spec_id set, UI refreshed
```

#### `action_approve(self)`
ประกัน approve → auto สร้าง SO + PO + confirm

```
Input: state == 'selected', มี selected vendor quote
Logic:
  1. Validate state == 'selected'
  2. สร้าง Sale Order:
     - partner_id = self.partner_id (ประกัน)
     - partner_shipping_id = self.garage_id (อู่)
     - Lines จาก self.line_ids (ราคาจาก selected quote)
  3. Confirm SO: so.action_confirm()
  4. สร้าง Purchase Order:
     - partner_id = selected_quote.vendor_id (ร้านอะไหล่)
     - dest_address_id = self.garage_id (dropship ไปอู่)
     - Lines จาก selected quote lines (ราคา vendor)
  5. Confirm PO: po.button_confirm()
     → Odoo auto-create DS transfer
  6. Link: self.sale_order_id = so, self.purchase_order_id = po
  7. State: 'approved' → 'ordered'
Output: SO + PO confirmed, DS transfer created
```

#### `action_reject(self)`
ประกัน reject → กลับไปให้ DP เลือก vendor ใหม่

```
Input: state == 'selected'
Logic:
  1. Deselect current vendor quote (is_selected=False, state='quoted')
  2. Clear approval_token
  3. State: 'selected' → 'quoted'
Output: กลับไป state quoted, DP เลือก vendor ใหม่ได้
```

#### `action_reset_draft(self)`
Reset to Draft — ลบ vendor quotes

```
Input: state == 'cancelled'
Logic:
  1. ลบ vendor_quote_ids ทั้งหมด (+ quote lines cascade)
  2. Clear approval_token
  3. Clear sale_order_id, purchase_order_id (ไม่ลบ SO/PO)
  4. State: 'cancelled' → 'draft'
  5. Procure order lines: ไม่ลบ — เก็บไว้
Output: กลับ draft, vendor quotes หายหมด, lines ยังอยู่
```

#### `unlink(self)` override
Delete — cleanup orphan spec/product

```
Input: state == 'draft' (standard Odoo check)
Logic:
  1. เก็บ vehicle_spec_id + product_ids จาก lines
  2. super().unlink()
  3. สำหรับแต่ละ spec/brand/model/gen/product:
     - เช็คว่ามี procure order อื่นใช้อยู่มั้ย
     - ถ้าไม่มี → ลบ
Output: order ลบ + orphan data ลบ
```

### 2.2 Procure Order Line

#### `_auto_create_product(self)` — called on save
Auto-create product จาก name + spec

```
Input: name (free text), order_id.vehicle_spec_id
Logic:
  1. ถ้าไม่มี name หรือไม่มี vehicle_spec_id → skip
  2. ถ้ามี product_id แล้ว:
     a. ถ้า name == product_id.name → skip (ไม่ต้องทำอะไร)
     b. ถ้า name != product_id.name → ลบ product เก่า (ถ้า orphan) → สร้างใหม่
  3. Lookup product.template: (name=name, itx_vehicle_spec_id=spec, source_module='procure')
  4. ไม่เจอ → Create product.template:
     - name = self.name
     - itx_vehicle_spec_id = spec
     - route_ids = dropship route
     - categ_id = อะไหล่ category
  5. Set self.product_id = product.product (first variant)
Output: product_id set
```

### 2.3 Vendor Quote

#### `action_mark_quoted(self)`
DP กรอกราคาเอง → mark as quoted

```
Input: state == 'sent', at least 1 line has price > 0
Logic:
  1. Validate state + price
  2. Write: state='quoted', date_quoted=now
  3. ถ้า order.state == 'sourcing' → order.state = 'quoted'
```

#### `action_select(self)`
เลือก vendor นี้ → สร้าง approval token

```
Input: state == 'quoted'
Logic:
  1. Deselect other quotes on same order
  2. Write: state='selected', is_selected=True
  3. Order: state='selected', approval_token=uuid4()
  4. Return: redirect to procure order form (แสดง approval URL)
```

### 2.4 Send RFQ Wizard

#### `action_send_rfq(self)`

```
Input: vendor_ids, quote_deadline_minutes, order_id
Logic:
  1. Validate: order draft, has lines, has vendors
  2. deadline = now + N minutes
  3. Per vendor:
     a. Check ไม่มี quote ซ้ำ (same order + vendor, not cancelled)
     b. Create itx.vendor.quote (order, vendor, deadline)
     c. Create itx.vendor.quote.line per procure order line
     d. Mark as sent (state='sent', date_sent=now)
  4. Order state = 'sourcing'
  5. Write: state='done', created_quote_ids = quotes
  6. Re-open wizard (target='new') → แสดง portal URLs + copy
```

---

## 3. Portal Routes

### 3.1 Vendor Quote Portal

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/procure/quote/<token>` | GET | public | แสดง form กรอกราคา |
| `/procure/quote/<token>/submit` | POST | public | Submit ราคา |

**GET Logic:**
1. Lookup quote by portal_token
2. Check: is_expired? is_submitted?
3. Render template with quote data + countdown timer

**POST Logic:**
1. Validate: not expired, state in (sent, draft)
2. Per quote line: write price_unit, delivery_date, is_available, notes
3. Quote: state='quoted', date_quoted=now
4. Order: if state='sourcing' → state='quoted'
5. Redirect with success=1

### 3.2 Insurance Approval Portal

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/procure/approve/<token>` | GET | public | แสดงรายละเอียด + ปุ่ม approve/reject |
| `/procure/approve/<token>/confirm` | POST | public | Approve |
| `/procure/approve/<token>/reject` | POST | public | Reject |

**GET Logic:**
1. Lookup order by approval_token
2. Find selected vendor quote (ไม่แสดงชื่อ vendor)
3. Render: claim info + ตาราง parts + ราคา + total + ปุ่ม

**Approve POST:**
1. Validate: state == 'selected'
2. Call action_approve() → auto SO + PO + confirm
3. Redirect with success=1

**Reject POST:**
1. Validate: state == 'selected'
2. Call action_reject() → state back to 'quoted'
3. Redirect with rejected=1

### 3.3 Garage Receipt Portal (Phase 2)

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/procure/delivery/<token>` | GET | public | แสดง DS lines + checkbox รับของ |
| `/procure/delivery/<token>/confirm` | POST | public | ยืนยันรับของ (partial) |
| `/procure/delivery/<token>/report` | POST | public | แจ้งปัญหา |

---

## 4. Views — Key UI Elements

### 4.1 Procure Order Form

```xml
<header>
  [Send RFQ]         invisible="state != 'draft'"
  [Approve]          invisible="state != 'selected'"
  [Cancel]           invisible="state in ('done', 'cancelled')"
  [Reset to Draft]   invisible="state != 'cancelled'"
  <statusbar>
</header>

<sheet>
  <button_box>
    [Quotes (N)]      stat button
    [Sale Order]       stat button
    [Purchase Order]   stat button
  </button_box>

  <title> PRO-00001 </title>

  <!-- Approval Link (visible after Select Vendor) -->
  <alert> Insurance Approval Link: [url] 📋 </alert>    invisible="not approval_token"

  <group "Insurance / Customer">
    partner_id        domain: tag "บริษัทประกัน"
    eclaim_number
    epart_number
    garage_id          domain: tag "อู่ซ่อม"
  </group>
  <group "Dates">
    date_order
    delivery_deadline
  </group>

  <!-- Vehicle Info — free text + Create Spec button -->
  <group "Vehicle Information">
    <group>
      vehicle_brand      placeholder="TOYOTA"
      vehicle_model      placeholder="INNOVA"
      vehicle_year       placeholder="2015"
      vehicle_submodel   placeholder="2.8 V"
    </group>
    <group>
      vehicle_chassis    placeholder="VIN" **REQUIRED**
      vehicle_plate
      vehicle_color
      vehicle_spec_id    readonly, invisible until created
      [Create Spec]      button, invisible="state != 'draft'"
    </group>
  </group>

  <notebook>
    <page "Part Lines">
      line_ids (editable=bottom)
        product_id       optional, domain=[spec filter]
        name             free text
        part_type
        quantity
        uom_id
        price_unit
        price_subtotal
        notes
    </page>
    <page "Vendor Quotes">    invisible="vendor_quote_count == 0"
      vendor_quote_ids (list)
    </page>
    <page "Notes">
      notes (html)
    </page>
  </notebook>
</sheet>
<chatter/>
```

### 4.2 Vendor Quote Form

```xml
<header>
  [Mark as Sent]       invisible="state != 'draft'"
  [Mark as Quoted]     invisible="state != 'sent'"
  [Select This Vendor] invisible="state != 'quoted'"
  [Cancel]             invisible="state in ('selected', 'cancelled')"
  <statusbar>
</header>

<sheet>
  <title> PRO-00001 / ร้าน A </title>

  <group "Quote Info">
    order_id (readonly)
    vendor_id
    amount_total
    is_selected (readonly)
  </group>
  <group "Timing">
    quote_deadline
    date_sent (readonly)
    date_quoted (readonly)
    portal_url (CopyClipboardChar, readonly)
  </group>

  <notebook>
    <page "Quote Lines"> (editable=bottom)
      procure_line_id (readonly)
      name (readonly)
      quantity (readonly)
      is_available
      price_unit
      price_subtotal
      delivery_date
      notes
    </page>
    <page "Attachments">
      attachment_ids (many2many_binary)
    </page>
    <page "Notes">
      notes
    </page>
  </notebook>
</sheet>
<chatter/>
```

---

## 5. Security (ir.model.access.csv)

| Model | Group | Read | Write | Create | Unlink |
|-------|-------|------|-------|--------|--------|
| itx.procure.order | user | ✅ | ✅ | ✅ | ❌ |
| itx.procure.order | manager | ✅ | ✅ | ✅ | ✅ |
| itx.procure.order.line | user | ✅ | ✅ | ✅ | ❌ |
| itx.procure.order.line | manager | ✅ | ✅ | ✅ | ✅ |
| itx.vendor.quote | user | ✅ | ✅ | ✅ | ❌ |
| itx.vendor.quote | manager | ✅ | ✅ | ✅ | ✅ |
| itx.vendor.quote.line | user | ✅ | ✅ | ✅ | ❌ |
| itx.vendor.quote.line | manager | ✅ | ✅ | ✅ | ✅ |
| itx.send.rfq.wizard | user | ✅ | ✅ | ✅ | ✅ |

---

## 6. Data Files

### 6.1 Sequence

```xml
<record id="seq_procure_order" model="ir.sequence">
  <field name="name">Procure Order</field>
  <field name="code">itx.procure.order</field>
  <field name="prefix">PRO-</field>
  <field name="padding">5</field>
</record>
```

### 6.2 Cron — Auto-expire Quotes

```xml
<record id="ir_cron_expire_vendor_quotes" model="ir.cron">
  <field name="name">Expire Vendor Quotes</field>
  <field name="model_id" ref="model_itx_vendor_quote"/>
  <field name="interval_number">1</field>
  <field name="interval_type">minutes</field>
  <field name="code">model._cron_expire_quotes()</field>
</record>
```

```python
@api.model
def _cron_expire_quotes(self):
    expired = self.search([
        ('state', '=', 'sent'),
        ('quote_deadline', '<=', fields.Datetime.now()),
    ])
    expired.write({'state': 'expired'})
```

---

## 7. File Structure

```
itx_procure_vehicle_parts/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── procure_order.py          # Main document + action_approve + action_create_spec
│   ├── procure_order_line.py     # Part lines + auto-create product
│   ├── vendor_quote.py           # Vendor quote + select + portal URL
│   └── vendor_quote_line.py      # Quote line details
├── wizards/
│   ├── __init__.py
│   └── send_rfq_wizard.py        # Send RFQ + show portal links
├── controllers/
│   ├── __init__.py
│   └── portal.py                 # Vendor quote + Insurance approval + (Garage receipt)
├── views/
│   ├── procure_order_views.xml    # Form + List + Search + Action
│   ├── vendor_quote_views.xml     # Form + List + Search + Action
│   ├── send_rfq_wizard_views.xml  # Wizard form + action
│   ├── portal_templates.xml       # Vendor quote form + Insurance approval form
│   └── menuitems.xml              # Vehicle Parts >> Procurement
├── security/
│   └── ir.model.access.csv
├── data/
│   └── ir_sequence_data.xml
├── static/
│   └── description/
│       └── icon.png
└── docs/
    ├── DESIGN_OVERVIEW.md         # Business decisions + architecture
    └── IMPLEMENTATION_DETAIL.md   # This file — technical specs
```

---

## 8. Changes to itx_info_vehicle (Base Module)

### 8.1 Add `source_module` field

เพิ่มใน 4 models:

```python
# models/vehicle_brand.py, vehicle_model.py, vehicle_generation.py, vehicle_spec.py
source_module = fields.Selection([
    ('revival', 'Revival'),
    ('procure', 'Procure'),
], string='Source Module', index=True)
```

- ไม่มี default (legacy data = False/empty)
- Index for performance (domain filter)
- ไม่ต้องมี UI/menu — code set อัตโนมัติ

### 8.2 Impact

- Revival module: ต้องตั้ง `source_module='revival'` ตอนสร้าง spec (แก้ทีหลังได้)
- Existing data: `source_module` = empty → ไม่กระทบ
- Lookup domain: `[('source_module', '=', 'procure')]` — existing data ไม่โผล่ใน procure dropdown
