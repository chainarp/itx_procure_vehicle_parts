# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request


class VendorQuotePortal(http.Controller):

    # ==========================================
    # Vendor Quote Portal (ร้านอะไหล่กรอกราคา)
    # ==========================================

    @http.route('/procure/quote/<string:token>', type='http', auth='public',
                website=True, csrf=True)
    def vendor_quote_form(self, token, **kwargs):
        """Display the vendor quote form for a given token"""
        quote = request.env['itx.vendor.quote'].sudo().search([
            ('portal_token', '=', token),
        ], limit=1)

        if not quote:
            return request.render('http_routing.404')

        # Load origin/condition options for dropdowns
        origins = request.env['itx.info.vehicle.part.origin'].sudo().search(
            [('active', '=', True)], order='sequence'
        )
        conditions = request.env['itx.info.vehicle.part.condition'].sudo().search(
            [('active', '=', True)], order='sequence'
        )

        values = {
            'quote': quote,
            'order': quote.order_id,
            'lines': quote.line_ids,
            'origins': origins,
            'conditions': conditions,
            'is_expired': (
                quote.quote_deadline
                and fields.Datetime.now() > quote.quote_deadline
            ),
            'is_submitted': quote.state == 'quoted',
            'error': kwargs.get('error'),
            'success': kwargs.get('success'),
        }
        return request.render(
            'itx_procure_vehicle_parts.portal_vendor_quote_form', values
        )

    @http.route('/procure/quote/<string:token>/submit', type='http',
                auth='public', website=True, csrf=True, methods=['POST'])
    def vendor_quote_submit(self, token, **post):
        """Handle vendor quote form submission"""
        quote = request.env['itx.vendor.quote'].sudo().search([
            ('portal_token', '=', token),
        ], limit=1)

        if not quote:
            return request.render('http_routing.404')

        # Check deadline
        if quote.quote_deadline and fields.Datetime.now() > quote.quote_deadline:
            return request.redirect(
                f'/procure/quote/{token}?error=expired'
            )

        # Check state
        if quote.state not in ('sent', 'draft'):
            return request.redirect(
                f'/procure/quote/{token}?error=already_submitted'
            )

        # Process submitted data
        for line in quote.line_ids:
            price_key = f'price_{line.id}'
            available_key = f'available_{line.id}'
            origin_key = f'origin_{line.id}'
            condition_key = f'condition_{line.id}'
            part_code_key = f'part_code_{line.id}'
            notes_key = f'notes_{line.id}'

            vals = {}
            if price_key in post:
                try:
                    vals['price_unit'] = float(post[price_key] or 0)
                except (ValueError, TypeError):
                    vals['price_unit'] = 0

            vals['is_available'] = available_key in post

            if origin_key in post and post[origin_key]:
                try:
                    vals['origin_id'] = int(post[origin_key])
                except (ValueError, TypeError):
                    pass

            if condition_key in post and post[condition_key]:
                try:
                    vals['condition_id'] = int(post[condition_key])
                except (ValueError, TypeError):
                    pass

            if part_code_key in post:
                vals['part_code'] = post[part_code_key] or False

            if notes_key in post:
                vals['notes'] = post[notes_key]

            if vals:
                line.sudo().write(vals)

        # Update quote state
        quote.sudo().write({
            'state': 'quoted',
            'date_quoted': fields.Datetime.now(),
        })

        # Update procure order state if first quote received
        if quote.order_id.state == 'sourcing':
            quote.order_id.sudo().write({'state': 'quoted'})

        return request.redirect(
            f'/procure/quote/{token}?success=1'
        )

    # ==========================================
    # Insurance Approval Portal (ประกันอนุมัติ)
    # ==========================================

    @http.route('/procure/approve/<string:token>', type='http', auth='public',
                website=True, csrf=True)
    def insurance_approval_form(self, token, **kwargs):
        """Display the insurance approval page"""
        order = request.env['itx.procure.order'].sudo().search([
            ('approval_token', '=', token),
        ], limit=1)

        if not order:
            return request.render('http_routing.404')

        # Find the selected quote
        selected_quote = request.env['itx.vendor.quote'].sudo().search([
            ('order_id', '=', order.id),
            ('is_selected', '=', True),
        ], limit=1)

        values = {
            'order': order,
            'quote': selected_quote,
            'lines': selected_quote.line_ids if selected_quote else [],
            'is_approved': order.state in ('approved', 'ordered', 'shipped', 'billed', 'done'),
            'is_rejected': kwargs.get('rejected'),
            'error': kwargs.get('error'),
            'success': kwargs.get('success'),
        }
        return request.render(
            'itx_procure_vehicle_parts.portal_insurance_approval_form', values
        )

    @http.route('/procure/approve/<string:token>/confirm', type='http',
                auth='public', website=True, csrf=True, methods=['POST'])
    def insurance_approval_confirm(self, token, **post):
        """Handle insurance approval submission"""
        order = request.env['itx.procure.order'].sudo().search([
            ('approval_token', '=', token),
        ], limit=1)

        if not order:
            return request.render('http_routing.404')

        if order.state != 'selected':
            return request.redirect(
                f'/procure/approve/{token}?error=invalid_state'
            )

        # Approve → auto SO + PO + confirm
        order.sudo().action_approve()

        return request.redirect(
            f'/procure/approve/{token}?success=1'
        )

    @http.route('/procure/approve/<string:token>/reject', type='http',
                auth='public', website=True, csrf=True, methods=['POST'])
    def insurance_approval_reject(self, token, **post):
        """Handle insurance rejection"""
        order = request.env['itx.procure.order'].sudo().search([
            ('approval_token', '=', token),
        ], limit=1)

        if not order:
            return request.render('http_routing.404')

        if order.state != 'selected':
            return request.redirect(
                f'/procure/approve/{token}?error=invalid_state'
            )

        order.sudo().action_reject()

        return request.redirect(
            f'/procure/approve/{token}?rejected=1'
        )
