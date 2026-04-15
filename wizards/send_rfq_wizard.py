# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SendRFQWizard(models.TransientModel):
    _name = 'itx.send.rfq.wizard'
    _description = 'Send RFQ to Vendors'

    order_id = fields.Many2one(
        comodel_name='itx.procure.order',
        string='Procure Order',
        required=True,
    )
    vendor_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Vendors',
        domain="[('category_id.name', '=', 'ร้านขายอะไหล่รถ')]",
        help='เลือก vendor ที่ต้องการส่ง RFQ (เลือกได้หลายราย)',
    )
    quote_deadline_minutes = fields.Integer(
        string='Deadline (minutes)',
        default=15,
        help='กำหนดเวลาเสนอราคา (นาที)',
    )

    # === Result state ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')
    created_quote_ids = fields.Many2many(
        comodel_name='itx.vendor.quote',
        string='Created Quotes',
        readonly=True,
    )

    def action_send_rfq(self):
        """Create Vendor Quote records and change order state to sourcing"""
        self.ensure_one()
        order = self.order_id

        if order.state != 'draft':
            raise UserError(_('Can only send RFQ from Draft state.'))

        if not order.line_ids:
            raise UserError(_('Please add part lines before sending RFQ.'))

        if not self.vendor_ids:
            raise UserError(_('Please select at least one vendor.'))

        if not order.vehicle_spec_id:
            raise UserError(_('Please create vehicle spec before sending RFQ.'))

        # Auto-create products for lines that don't have one
        order.line_ids._auto_create_product()

        deadline = fields.Datetime.now() + timedelta(minutes=self.quote_deadline_minutes)

        VendorQuote = self.env['itx.vendor.quote']
        VendorQuoteLine = self.env['itx.vendor.quote.line']

        created_quotes = VendorQuote
        for vendor in self.vendor_ids:
            # Check if quote already exists for this vendor + order
            existing = VendorQuote.search([
                ('order_id', '=', order.id),
                ('vendor_id', '=', vendor.id),
                ('state', 'not in', ['cancelled']),
            ], limit=1)
            if existing:
                continue

            quote = VendorQuote.create({
                'order_id': order.id,
                'vendor_id': vendor.id,
                'quote_deadline': deadline,
            })

            # Create quote lines matching procure order lines
            for line in order.line_ids:
                VendorQuoteLine.create({
                    'quote_id': quote.id,
                    'procure_line_id': line.id,
                    'sequence': line.sequence,
                    'origin_id': line.origin_id.id if line.origin_id else False,
                    'condition_id': line.condition_id.id if line.condition_id else False,
                })

            # Mark as sent
            quote.action_send()
            created_quotes |= quote

        # Update order state
        order.state = 'sourcing'

        self.write({
            'state': 'done',
            'created_quote_ids': [(6, 0, created_quotes.ids)],
        })

        # Re-open wizard to show links
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
