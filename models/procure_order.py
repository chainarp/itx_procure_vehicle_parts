# -*- coding: utf-8 -*-

import uuid
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProcureOrder(models.Model):
    _name = 'itx.procure.order'
    _description = 'Procure Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'

    # === Sequence / Name ===
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )

    # === State ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sourcing', 'Sourcing'),
        ('quoted', 'Quoted'),
        ('selected', 'Selected'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('shipped', 'Shipped'),
        ('billed', 'Billed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # === Insurance Company (Customer) ===
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Insurance Company',
        required=True,
        tracking=True,
        domain="[('category_id.name', '=', 'บริษัทประกันภัย')]",
    )

    # === Claim Info ===
    eclaim_number = fields.Char(
        string='e-Claim Number',
        index=True,
        tracking=True,
    )
    epart_number = fields.Char(
        string='ePart Number',
        index=True,
        tracking=True,
    )

    # === Vehicle Info (free text — user กรอก) ===
    vehicle_brand = fields.Char(string='Brand')
    vehicle_model = fields.Char(string='Model')
    vehicle_year = fields.Char(string='Year')
    vehicle_submodel = fields.Char(string='Sub-model')
    vehicle_chassis = fields.Char(
        string='VIN (Chassis)',
        required=True,
        index=True,
    )
    vehicle_plate = fields.Char(string='Plate Number')
    vehicle_color = fields.Char(string='Color')

    # === Vehicle Spec (auto-set จากปุ่ม Create Spec) ===
    vehicle_spec_id = fields.Many2one(
        comodel_name='itx.info.vehicle.spec',
        string='Vehicle Spec',
        readonly=True,
    )

    # === Garage / Delivery Address ===
    garage_id = fields.Many2one(
        comodel_name='res.partner',
        string='Garage (Delivery To)',
        domain="[('category_id.name', '=', 'อู่ซ่อมรถประกัน')]",
    )

    # === Dates ===
    date_order = fields.Datetime(
        string='Order Date',
        default=fields.Datetime.now,
        required=True,
    )
    delivery_deadline = fields.Date(
        string='Delivery Deadline',
    )

    # === Lines ===
    line_ids = fields.One2many(
        comodel_name='itx.procure.order.line',
        inverse_name='order_id',
        string='Part Lines',
        copy=True,
    )

    # === Vendor Quotes ===
    vendor_quote_ids = fields.One2many(
        comodel_name='itx.vendor.quote',
        inverse_name='order_id',
        string='Vendor Quotes',
    )
    vendor_quote_count = fields.Integer(
        compute='_compute_vendor_quote_count',
        string='Quotes',
    )

    # === Linked Documents (1 SO, 1 PO per order) ===
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        copy=False,
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        copy=False,
    )

    # === Insurance Approval Portal ===
    approval_token = fields.Char(
        string='Approval Token',
        copy=False,
    )
    approval_url = fields.Char(
        string='Approval URL',
        compute='_compute_approval_url',
    )

    # === Notes ===
    notes = fields.Html(string='Internal Notes')

    # === Computes ===
    @api.depends('approval_token')
    def _compute_approval_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            if rec.approval_token:
                rec.approval_url = f"{base_url}/procure/approve/{rec.approval_token}"
            else:
                rec.approval_url = False

    @api.depends('vendor_quote_ids')
    def _compute_vendor_quote_count(self):
        for rec in self:
            rec.vendor_quote_count = len(rec.vendor_quote_ids)

    # === CRUD ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'itx.procure.order'
                ) or _('New')
        return super().create(vals_list)

    def unlink(self):
        """Delete — cleanup orphan spec/product if not used elsewhere"""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Can only delete orders in Draft state.'))
        # Collect data to cleanup after delete
        specs_to_check = self.mapped('vehicle_spec_id')
        products_to_check = self.mapped('line_ids.product_id')
        order_ids = self.ids

        result = super().unlink()

        # Cleanup orphan specs (brand → model → gen → spec chain)
        for spec in specs_to_check:
            if spec.source_module == 'procure' and not self.search_count([
                ('vehicle_spec_id', '=', spec.id),
                ('id', 'not in', order_ids),
            ]):
                gen = spec.generation_id
                model = gen.model_id if gen else False
                brand = model.brand_id if model else False
                spec.unlink()
                if gen and gen.source_module == 'procure' and not gen.spec_ids:
                    gen.unlink()
                if model and model.source_module == 'procure' and not model.generation_ids:
                    model.unlink()
                if brand and brand.source_module == 'procure' and not brand.model_ids:
                    brand.unlink()

        # Cleanup orphan products
        ProcureLine = self.env['itx.procure.order.line']
        for product in products_to_check:
            if product and not ProcureLine.search_count([
                ('product_id', '=', product.id),
                ('order_id', 'not in', order_ids),
            ]):
                tmpl = product.product_tmpl_id
                if tmpl:
                    tmpl.unlink()

        return result

    # === Create Spec Button ===
    def action_create_spec(self):
        """Auto-lookup/create vehicle spec from free text fields"""
        self.ensure_one()
        if not all([self.vehicle_brand, self.vehicle_model,
                    self.vehicle_year, self.vehicle_submodel]):
            raise UserError(_('Please fill in Brand, Model, Year, and Sub-model before creating spec.'))

        # Cleanup old spec if exists and orphan
        if self.vehicle_spec_id and self.vehicle_spec_id.source_module == 'procure':
            old_spec = self.vehicle_spec_id
            self.vehicle_spec_id = False
            if not self.search_count([
                ('vehicle_spec_id', '=', old_spec.id),
                ('id', '!=', self.id),
            ]):
                old_gen = old_spec.generation_id
                old_model = old_gen.model_id if old_gen else False
                old_brand = old_model.brand_id if old_model else False
                old_spec.unlink()
                if old_gen and old_gen.source_module == 'procure' and not old_gen.spec_ids:
                    old_gen.unlink()
                if old_model and old_model.source_module == 'procure' and not old_model.generation_ids:
                    old_model.unlink()
                if old_brand and old_brand.source_module == 'procure' and not old_brand.model_ids:
                    old_brand.unlink()

        Brand = self.env['itx.info.vehicle.brand']
        Model = self.env['itx.info.vehicle.model']
        Gen = self.env['itx.info.vehicle.generation']
        Spec = self.env['itx.info.vehicle.spec']

        # Lookup/create brand
        brand_name = self.vehicle_brand.strip()
        brand = Brand.search([
            ('name', '=ilike', brand_name),
            ('source_module', '=', 'procure'),
        ], limit=1)
        if not brand:
            code = brand_name.upper().replace(' ', '_')
            abbr = ''.join(c for c in brand_name if c.isalnum())[:3].upper()
            brand = Brand.create({
                'name': brand_name,
                'code': code,
                'abbr': abbr,
                'source_module': 'procure',
            })

        # Lookup/create model
        model_name = self.vehicle_model.strip()
        model = Model.search([
            ('name', '=ilike', model_name),
            ('brand_id', '=', brand.id),
            ('source_module', '=', 'procure'),
        ], limit=1)
        if not model:
            code = model_name.upper().replace(' ', '_').replace('-', '')
            abbr = ''.join(c for c in model_name if c.isalnum())[:3].upper()
            model = Model.create({
                'name': model_name,
                'code': code,
                'abbr': abbr,
                'brand_id': brand.id,
                'source_module': 'procure',
            })

        # Lookup/create generation
        gen_name = self.vehicle_year.strip()
        gen = Gen.search([
            ('name', '=ilike', gen_name),
            ('model_id', '=', model.id),
            ('source_module', '=', 'procure'),
        ], limit=1)
        if not gen:
            code = gen_name.upper().replace(' ', '-')
            abbr = ''.join(c for c in gen_name if c.isalnum())[:3].upper()
            gen = Gen.create({
                'name': gen_name,
                'code': code,
                'abbr': abbr,
                'model_id': model.id,
                'source_module': 'procure',
            })

        # Lookup/create spec
        spec_name = self.vehicle_submodel.strip()
        spec = Spec.search([
            ('name', '=ilike', spec_name),
            ('generation_id', '=', gen.id),
            ('source_module', '=', 'procure'),
        ], limit=1)
        if not spec:
            code = spec_name.upper().replace(' ', '-').replace('.', '')
            abbr = ''.join(c for c in spec_name if c.isalnum())[:4].upper()
            spec = Spec.create({
                'name': spec_name,
                'code': code,
                'abbr': abbr,
                'generation_id': gen.id,
                'source_module': 'procure',
            })

        self.vehicle_spec_id = spec.id

    # === State Actions ===
    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Cannot cancel a completed Procure Order.'))
            rec.state = 'cancelled'

    def action_reset_draft(self):
        """Reset to draft — delete all vendor quotes"""
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Can only reset cancelled orders to draft.'))
            # Delete vendor quotes (user จะงงถ้าเก็บไว้)
            rec.vendor_quote_ids.unlink()
            rec.write({
                'state': 'draft',
                'approval_token': False,
                'sale_order_id': False,
                'purchase_order_id': False,
            })

    def action_approve(self):
        """ประกัน approve → auto สร้าง SO + PO + confirm"""
        for rec in self:
            if rec.state != 'selected':
                raise UserError(_('Can only approve orders in Selected state.'))

            # Find selected quote
            selected_quote = rec.vendor_quote_ids.filtered(
                lambda q: q.is_selected and q.state == 'selected'
            )
            if not selected_quote:
                raise UserError(_('No vendor selected. Please select a vendor first.'))
            selected_quote = selected_quote[0]

            # === Create Sale Order (ขายให้ประกัน) ===
            so_lines = []
            for qline in selected_quote.line_ids:
                if qline.is_available and qline.price_unit > 0:
                    so_lines.append((0, 0, {
                        'product_id': qline.procure_line_id.product_id.id
                            if qline.procure_line_id.product_id else False,
                        'name': qline.name or qline.procure_line_id.name,
                        'product_uom_qty': qline.quantity,
                        'price_unit': qline.price_unit,
                    }))

            if not so_lines:
                raise UserError(_('No available items with prices to create orders.'))

            so_vals = {
                'partner_id': rec.partner_id.id,
                'partner_shipping_id': rec.garage_id.id if rec.garage_id else rec.partner_id.id,
                'origin': rec.name,
                'order_line': so_lines,
            }
            so = self.env['sale.order'].create(so_vals)
            so.action_confirm()

            # === Create Purchase Order (ซื้อจาก vendor) ===
            po_lines = []
            for qline in selected_quote.line_ids:
                if qline.is_available and qline.price_unit > 0:
                    po_lines.append((0, 0, {
                        'product_id': qline.procure_line_id.product_id.id
                            if qline.procure_line_id.product_id else False,
                        'name': qline.name or qline.procure_line_id.name,
                        'product_qty': qline.quantity,
                        'price_unit': qline.price_unit,
                        'date_planned': qline.delivery_date or fields.Date.today(),
                    }))

            # Find dropship picking type so Odoo creates DS/ transfer
            dropship_picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'dropship'),
                ('company_id', '=', rec.company_id.id),
            ], limit=1)

            po_vals = {
                'partner_id': selected_quote.vendor_id.id,
                'dest_address_id': rec.garage_id.id if rec.garage_id else False,
                'origin': rec.name,
                'order_line': po_lines,
            }
            if dropship_picking_type:
                po_vals['picking_type_id'] = dropship_picking_type.id
            po = self.env['purchase.order'].create(po_vals)
            po.button_confirm()

            rec.write({
                'state': 'ordered',
                'sale_order_id': so.id,
                'purchase_order_id': po.id,
            })

    def action_reject(self):
        """ประกัน reject → กลับไป quoted ให้ DP เลือก vendor ใหม่"""
        for rec in self:
            if rec.state != 'selected':
                raise UserError(_('Can only reject orders in Selected state.'))
            # Deselect current vendor
            selected = rec.vendor_quote_ids.filtered(lambda q: q.is_selected)
            selected.write({'is_selected': False, 'state': 'quoted'})
            rec.write({
                'state': 'quoted',
                'approval_token': False,
            })

    # === Smart Buttons ===
    def action_view_vendor_quotes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Quotes'),
            'res_model': 'itx.vendor.quote',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def action_view_sale_order(self):
        self.ensure_one()
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.sale_order_id.id,
            }

    def action_view_purchase_order(self):
        self.ensure_one()
        if self.purchase_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': self.purchase_order_id.id,
            }
