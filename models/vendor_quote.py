# -*- coding: utf-8 -*-

import uuid
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VendorQuote(models.Model):
    _name = 'itx.vendor.quote'
    _description = 'Vendor Quote'
    _inherit = ['mail.thread']
    _order = 'create_date desc, id desc'

    # === Reference ===
    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
    )

    # === Links ===
    order_id = fields.Many2one(
        comodel_name='itx.procure.order',
        string='Procure Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True,
        tracking=True,
        domain="[('supplier_rank', '>', 0)]",
    )

    # === State ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('quoted', 'Quoted'),
        ('expired', 'Expired'),
        ('selected', 'Selected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # === Deadline / Timer ===
    quote_deadline = fields.Datetime(
        string='Quote Deadline',
        help='กำหนดเวลาเสนอราคา — หลังเวลานี้ vendor กรอกไม่ได้',
    )
    date_sent = fields.Datetime(string='Sent Date')
    date_quoted = fields.Datetime(string='Quoted Date')

    # === Portal Access ===
    portal_token = fields.Char(
        string='Portal Token',
        copy=False,
        default=lambda self: str(uuid.uuid4()),
    )

    # === Quote Lines ===
    line_ids = fields.One2many(
        comodel_name='itx.vendor.quote.line',
        inverse_name='quote_id',
        string='Quote Lines',
    )

    # === Totals ===
    amount_total = fields.Float(
        string='Total Amount',
        compute='_compute_amount_total',
        store=True,
    )

    # === Attachments ===
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Attachments',
        help='แนบเอกสารเสนอราคาจาก vendor (เช่น PDF, รูปภาพ)',
    )

    # === Notes ===
    notes = fields.Text(string='Notes')

    # === Is Selected ===
    is_selected = fields.Boolean(
        string='Selected',
        default=False,
        help='เลือก vendor นี้สำหรับ Procure Order',
    )

    # === Computes ===
    @api.depends('order_id.name', 'vendor_id.name')
    def _compute_name(self):
        for rec in self:
            order_name = rec.order_id.name or ''
            vendor_name = rec.vendor_id.name or ''
            rec.name = f"{order_name} / {vendor_name}"

    @api.depends('line_ids.price_subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('price_subtotal'))

    # === Actions ===
    def action_send(self):
        """Mark as sent — start the timer"""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Can only send quotes in Draft state.'))
            rec.write({
                'state': 'sent',
                'date_sent': fields.Datetime.now(),
            })

    def action_mark_quoted(self):
        """DP staff กรอกราคาเองแล้วกดยืนยัน — เปลี่ยน sent → quoted"""
        for rec in self:
            if rec.state != 'sent':
                raise UserError(_('Can only mark as quoted from Sent state.'))
            if not any(line.price_unit > 0 for line in rec.line_ids):
                raise UserError(_('Please fill in at least one price before marking as quoted.'))
            rec.write({
                'state': 'quoted',
                'date_quoted': fields.Datetime.now(),
            })
            # Update procure order state if first quote received
            if rec.order_id.state == 'sourcing':
                rec.order_id.state = 'quoted'

    def action_select(self):
        """Select this vendor for the Procure Order — generate approval token"""
        self.ensure_one()
        if self.state != 'quoted':
            raise UserError(_('Can only select quotes in Quoted state.'))
        # Deselect others on same order
        other_quotes = self.search([
            ('order_id', '=', self.order_id.id),
            ('id', '!=', self.id),
            ('is_selected', '=', True),
        ])
        other_quotes.write({'is_selected': False, 'state': 'quoted'})
        self.write({
            'state': 'selected',
            'is_selected': True,
        })
        # Generate approval token for insurance
        order = self.order_id
        order.write({
            'state': 'selected',
            'approval_token': str(uuid.uuid4()),
        })
        # Return procure order form to show approval URL
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'itx.procure.order',
            'view_mode': 'form',
            'res_id': order.id,
        }

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    # === Cron: Auto-expire ===
    @api.model
    def _cron_expire_quotes(self):
        expired = self.search([
            ('state', '=', 'sent'),
            ('quote_deadline', '<=', fields.Datetime.now()),
        ])
        expired.write({'state': 'expired'})

    # === Portal URL (computed) ===
    portal_url = fields.Char(
        string='Portal URL',
        compute='_compute_portal_url',
    )

    @api.depends('portal_token')
    def _compute_portal_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            if rec.portal_token:
                rec.portal_url = f"{base_url}/procure/quote/{rec.portal_token}"
            else:
                rec.portal_url = False
