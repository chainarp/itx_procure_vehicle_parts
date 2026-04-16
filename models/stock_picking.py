# -*- coding: utf-8 -*-

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Override to update procure order state when DS transfers complete."""
        res = super().button_validate()
        self._update_procure_order_state()
        return res

    def _update_procure_order_state(self):
        """Check if all DS pickings for a PO are done → update procure order."""
        for picking in self:
            if picking.picking_type_code != 'dropship' or picking.state != 'done':
                continue

            # Find procure order linked to this PO
            po = picking.purchase_id
            if not po:
                continue

            procure_order = self.env['itx.procure.order'].search([
                ('purchase_order_id', '=', po.id),
                ('state', '=', 'ordered'),
            ], limit=1)
            if not procure_order:
                continue

            # Check if ALL pickings for this PO are done
            all_pickings = self.env['stock.picking'].search([
                ('purchase_id', '=', po.id),
            ])
            if all(p.state == 'done' for p in all_pickings):
                procure_order.write({'state': 'shipped'})
