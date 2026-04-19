# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SelectVendorWizard(models.TransientModel):
    _name = 'itx.select.vendor.wizard'
    _description = 'Select Best Vendor Per Line'

    order_id = fields.Many2one(
        comodel_name='itx.procure.order',
        string='Procure Order',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='itx.select.vendor.wizard.line',
        inverse_name='wizard_id',
        string='Selection Lines',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order_id = self.env.context.get('default_order_id')
        if not order_id:
            return res

        order = self.env['itx.procure.order'].browse(order_id)
        lines = []
        for pline in order.line_ids:
            quote_lines = self.env['itx.vendor.quote.line'].search([
                ('procure_line_id', '=', pline.id),
                ('quote_id.state', 'in', ['quoted', 'selected']),
                ('is_available', '=', True),
                ('price_unit', '>', 0),
            ])

            default_qline = pline.selected_quote_line_id
            if not default_qline and quote_lines:
                default_qline = quote_lines.sorted('price_unit')[0]

            lines.append((0, 0, {
                'procure_line_id': pline.id,
                'selected_quote_line_id': default_qline.id if default_qline else False,
            }))

        res['line_ids'] = lines
        return res

    def action_confirm_selection(self):
        """Apply vendor selection to procure order lines"""
        self.ensure_one()
        order = self.order_id

        _logger.info('=== SELECT VENDOR: wizard has %d lines ===', len(self.line_ids))

        # Build mapping: procure_line_id → quote_line_id
        selection_map = {}
        for wline in self.line_ids:
            pline_id = wline.procure_line_id.id
            qline_id = wline.selected_quote_line_id.id if wline.selected_quote_line_id else False
            _logger.info('  wizard line: procure_line=%s, quote_line=%s', pline_id, qline_id)
            if pline_id and qline_id:
                selection_map[pline_id] = qline_id

        if not selection_map:
            raise UserError(_('กรุณาเลือก vendor อย่างน้อย 1 line'))

        # Write selections directly to procure order lines
        ProcureLine = self.env['itx.procure.order.line']
        for pline in order.line_ids:
            qline_id = selection_map.get(pline.id, False)
            pline.write({'selected_quote_line_id': qline_id})

        # Flush to DB
        self.env.flush_all()

        # Verify writes persisted
        self.env.invalidate_all()
        verify_count = sum(1 for pl in order.line_ids if pl.selected_quote_line_id)
        _logger.info('  verified: %d / %d lines have selected_quote_line_id', verify_count, len(order.line_ids))
        if not verify_count:
            raise UserError(_(
                'เลือก vendor แล้ว แต่ค่าไม่ถูกบันทึก — กรุณาแจ้ง developer\n'
                'selection_map: %s'
            ) % selection_map)

        # Mark selected vendor quotes
        order.vendor_quote_ids.write({'is_selected': False})
        selected_quotes = order.line_ids.mapped('selected_quote_line_id.quote_id')
        selected_quotes.write({'is_selected': True, 'state': 'selected'})

        # Update order state
        order.write({'state': 'selected'})

        # Generate approval token
        if not order.approval_token:
            import uuid
            order.write({'approval_token': str(uuid.uuid4())})

        return {'type': 'ir.actions.act_window_close'}


class SelectVendorWizardLine(models.TransientModel):
    _name = 'itx.select.vendor.wizard.line'
    _description = 'Select Vendor Wizard Line'

    wizard_id = fields.Many2one(
        comodel_name='itx.select.vendor.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    procure_line_id = fields.Many2one(
        comodel_name='itx.procure.order.line',
        string='Part',
        readonly=True,
    )
    part_name = fields.Char(
        string='Part Description',
        related='procure_line_id.name',
        readonly=True,
    )
    quantity = fields.Float(
        string='Qty',
        related='procure_line_id.quantity',
        readonly=True,
    )

    # Vendor quote line selection
    selected_quote_line_id = fields.Many2one(
        comodel_name='itx.vendor.quote.line',
        string='Selected Vendor Quote',
        domain="[('procure_line_id', '=', procure_line_id), "
               "('is_available', '=', True), ('price_unit', '>', 0), "
               "('quote_id.state', 'in', ['quoted', 'selected'])]",
    )
    selected_vendor_name = fields.Char(
        string='Vendor',
        related='selected_quote_line_id.quote_id.vendor_id.name',
        readonly=True,
    )
    selected_price = fields.Float(
        string='Price',
        related='selected_quote_line_id.price_unit',
        readonly=True,
    )
    selected_origin = fields.Char(
        string='Origin',
        related='selected_quote_line_id.origin_id.name',
        readonly=True,
    )
    selected_condition = fields.Char(
        string='Condition',
        related='selected_quote_line_id.condition_id.name',
        readonly=True,
    )
    selected_notes = fields.Text(
        string='Notes',
        related='selected_quote_line_id.notes',
        readonly=True,
    )
