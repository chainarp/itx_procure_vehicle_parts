# -*- coding: utf-8 -*-
{
    'name': 'ITX Procure Vehicle Parts',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Insurance Claim Parts Procurement & Fulfillment',
    'description': 'By Chainaris Padunkul  & Claude'
ITX Procure Vehicle Parts — Insurance Parts Procurement
========================================================

จัดหาอะไหล่รถยนต์ผ่านระบบเคลมประกันภัย (ePart / BlueVenture / EMCS)

Workflow:
1. รับออเดอร์จากบริษัทประกันภัย
2. จัดหาอะไหล่จากร้านอะไหล่ (หลายร้านต่อ 1 order)
3. เสนอราคา เลือกร้าน (เร็วสุด + ถูกสุด)
4. กรอกราคาเสนอใน ePart
5. รอการอนุมัติจากประกัน → คอนเฟิร์มร้าน
6. ร้านจัดส่งอะไหล่ (SLA ≤ 3 วัน)
7. เซ็นรับ + อัปโหลดเอกสาร
8. ตรวจสอบ + วางบิล
9. การจ่ายเงิน 2 ขา: จ่ายร้าน + เรียกเก็บจากประกัน

Developed by IT Expert Training & Outsourcing Co. (Thailand)
    """,
    'author': 'IT Expert Training & Outsourcing Co.',
    'website': 'https://www.itexpert.co.th',
    'license': 'LGPL-3',
    'depends': [
        'itx_info_vehicle',
        'sale',
        'purchase',
        'stock_dropshipping',
        'account',
        'website',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        # Views
        'views/send_rfq_wizard_views.xml',
        'views/select_vendor_wizard_views.xml',
        'views/procure_order_views.xml',
        'views/vendor_quote_views.xml',
        'views/portal_templates.xml',
        'views/menuitems.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
