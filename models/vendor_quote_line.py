# -*- coding: utf-8 -*-

from odoo import api, fields, models


class VendorQuoteLine(models.Model):
    _name = 'itx.vendor.quote.line'
    _description = 'Vendor Quote Line'
    _order = 'sequence, id'

    quote_id = fields.Many2one(
        comodel_name='itx.vendor.quote',
        string='Vendor Quote',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # === Link to Procure Order Line ===
    procure_line_id = fields.Many2one(
        comodel_name='itx.procure.order.line',
        string='Procure Line',
        required=True,
        ondelete='cascade',
    )

    sequence = fields.Integer(string='Seq', default=10)

    # === Part Info (from procure line) ===
    name = fields.Char(
        string='Part Description',
        related='procure_line_id.name',
        readonly=True,
    )
    quantity = fields.Float(
        string='Qty Requested',
        related='procure_line_id.quantity',
        readonly=True,
    )

    # === Origin / Condition (vendor อาจเสนอต่างจากที่ประกันสั่ง) ===
    origin_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.origin',
        string='Origin',
        help='แท้/เทียม/Recon — default จาก procure line แต่ vendor แก้ได้',
    )
    condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Condition',
        help='สภาพอะไหล่ — default จาก procure line แต่ vendor แก้ได้',
    )

    # === Part Code (vendor กรอก ถ้ามี) ===
    part_code = fields.Char(
        string='Part Code',
        help='รหัสอะไหล่ที่ vendor เสนอ (nullable)',
    )

    # === Vendor fills these ===
    price_unit = fields.Float(
        string='Unit Price',
        help='ราคาที่ vendor เสนอ',
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
    )
    delivery_date = fields.Date(
        string='Delivery Date',
        help='vendor กำหนดวันส่ง',
    )
    is_available = fields.Boolean(
        string='Available',
        default=True,
        help='vendor มีของหรือไม่',
    )
    notes = fields.Text(string='Notes')

    # === Computes ===
    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
