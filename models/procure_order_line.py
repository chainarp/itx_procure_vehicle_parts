# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProcureOrderLine(models.Model):
    _name = 'itx.procure.order.line'
    _description = 'Procure Order Line'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        comodel_name='itx.procure.order',
        string='Procure Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    sequence = fields.Integer(string='Seq', default=10)

    # === Part Info ===
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    name = fields.Char(
        string='Part Description',
        required=True,
        help='ชื่ออะไหล่ free text (ตามที่ประกันเรียก)',
    )
    part_type = fields.Char(
        string='Part Type',
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit',
        default=lambda self: self.env.ref('uom.product_uom_unit', raise_if_not_found=False),
    )

    # === Price (filled after vendor selected) ===
    price_unit = fields.Float(
        string='Unit Price',
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
    )

    # === Origin / Condition ===
    origin_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.origin',
        string='Origin',
        help='แท้ (OEM) / เทียม (Aftermarket) / Recon',
    )
    condition_id = fields.Many2one(
        comodel_name='itx.info.vehicle.part.condition',
        string='Condition',
        default=lambda self: self.env['itx.info.vehicle.part.condition'].search(
            [('code', '=', 'NEW')], limit=1,
        ),
        help='สภาพอะไหล่ — default New สำหรับ procure',
    )

    # === Vendor Selection (per-line) ===
    selected_quote_line_id = fields.Many2one(
        comodel_name='itx.vendor.quote.line',
        string='Selected Quote Line',
        help='Vendor quote line ที่ถูกเลือกสำหรับ line นี้',
    )
    selected_vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Selected Vendor',
        related='selected_quote_line_id.quote_id.vendor_id',
        store=True,
    )
    selected_price = fields.Float(
        string='Selected Price',
        related='selected_quote_line_id.price_unit',
        store=True,
    )

    # === Notes ===
    notes = fields.Text(string='Notes')

    # === Computes ===
    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    # === Onchange ===
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            if self.product_id.uom_id:
                self.uom_id = self.product_id.uom_id

    # === CRUD — auto-create product on save ===
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._auto_create_product()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'name' in vals or 'origin_id' in vals or 'condition_id' in vals:
            self._auto_create_product()
        return res

    # === Auto-create Product ===
    def _auto_create_product(self):
        """Lookup/create product template + variant from name + spec + origin + condition.
        Called before Send RFQ.
        """
        ProductTemplate = self.env['product.template']
        default_condition = self.env['itx.info.vehicle.part.condition'].search(
            [('code', '=', 'NEW')], limit=1,
        )
        for line in self:
            spec = line.order_id.vehicle_spec_id
            origin = line.origin_id
            condition = line.condition_id or default_condition
            if not line.name or not spec or not origin:
                continue

            # Already has matching product
            if line.product_id and line.product_id.product_tmpl_id.name == line.name:
                continue

            # Name changed — cleanup old product if orphan
            if line.product_id and line.product_id.product_tmpl_id.name != line.name:
                old_product = line.product_id
                line.product_id = False
                if not self.search_count([
                    ('product_id', '=', old_product.id),
                    ('id', '!=', line.id),
                ]):
                    old_product.product_tmpl_id.unlink()

            # Lookup existing template by name + spec
            tmpl = ProductTemplate.search([
                ('name', '=', line.name),
                ('itx_spec_id', '=', spec.id),
            ], limit=1)

            if not tmpl:
                dropship_route = self.env.ref(
                    'stock_dropshipping.route_drop_shipping',
                    raise_if_not_found=False,
                )
                tmpl = ProductTemplate.create({
                    'name': line.name,
                    'type': 'consu',
                    'is_storable': True,
                    'itx_is_vehicle_part': True,
                    'itx_spec_id': spec.id,
                    'route_ids': [(4, dropship_route.id)] if dropship_route else [],
                })

            # Get/create the correct variant for origin + condition
            if origin and condition:
                variant = tmpl._get_or_create_variant(origin, condition)
                line.product_id = variant.id
            else:
                line.product_id = tmpl.product_variant_id.id
