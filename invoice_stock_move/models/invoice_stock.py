# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tests import Form


class StockWarehouseInherit(models.Model):
    _inherit = 'stock.warehouse'

    is_default_warehouse_for_invoice = fields.Boolean(string="Default Warehouse For Invoice")


class InvoiceStockMove(models.Model):
    _inherit = 'account.move'

    def _get_stock_type_ids(self):
        data = self.env['stock.picking.type'].search([])

        if self._context.get('default_move_type') in ['out_invoice', 'out_refund']:
            for line in data:
                if line.code == 'outgoing':
                    return line
        if self._context.get('default_move_type') in ['in_invoice', 'in_refund']:
            for line in data:
                if line.code == 'incoming':
                    return line

    def button_process_edi_web_services(self):
        pass

    @api.model
    def _get_is_default_warehouse_for_invoice(self):
        return self.env['stock.warehouse'].search([('is_default_warehouse_for_invoice', '=', True)], limit=1).id

    picking_count = fields.Integer(string="Count", copy=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id", copy=False)

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type',
                                      default=_get_stock_type_ids,
                                      help="This will determine picking type of incoming shipment")
    code = fields.Selection(string="Code", related='picking_type_id.code', readonly=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse', default=_get_is_default_warehouse_for_invoice)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('posted', 'Posted'),
        ('post', 'Post'),
        ('cancel', 'Cancelled'),
        ('done', 'Received'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)

    def button_draft(self):
        res = super(InvoiceStockMove, self).button_draft()
        payments = self.env['account.payment'].search([('ref', '=', self.name)])
        for payment in payments:
            payment.action_draft()
            payment.sudo().unlink()
        if self.invoice_picking_id:
            return_form = Form(self.env['stock.return.picking'].with_context(active_ids=self.invoice_picking_id.ids,
                                                                             active_id=self.invoice_picking_id.id,
                                                                             active_model='stock.picking'))
            stock_return_picking = return_form.save()
            print(stock_return_picking)
            res = stock_return_picking.create_returns()['res_id']
            pick = self.env['stock.picking'].browse(res)
            move_ids = self.env['stock.move'].search([('picking_id', '=', pick.id)])
            move_ids._action_assign()
            immediate_transfer_obj = self.env['stock.immediate.transfer'].search(
                [('pick_ids', 'in', pick.ids)])
            if not immediate_transfer_obj:
                immediate_transfer_obj = self.env['stock.immediate.transfer'].create(
                    {'pick_ids': pick.ids,
                     'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': pick.id})]
                     })
            immediate_transfer_obj.process()
            pick._action_done()
            self.invoice_picking_id = False
        return res

    def action_stock_move(self):
        # if not self.picking_type_id:
        #     raise UserError(_(
        #         " Please select a picking type"))
        if self.move_type in ['out_invoice', 'in_refund']:
            if self.warehouse_id:
                picking_type_id = self.warehouse_id.out_type_id
        elif self.move_type in ['out_refund', 'in_invoice']:
            if self.warehouse_id:
                picking_type_id = self.warehouse_id.in_type_id
        for order in self:
            # if not order.invoice_origin and picking_type_id.code == 'outgoing' and not order.warehouse_id:
            #     raise ValidationError(_('Please Select Warehouse'))
            if not self.invoice_picking_id:
                pick = {}
                if self.move_type in ['out_invoice', 'in_refund']:
                    pick = {
                        'picking_type_id': picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'location_id': picking_type_id.default_location_src_id.id,
                        'move_type': 'direct'
                    }
                if self.move_type in ['in_invoice', 'out_refund']:
                    pick = {
                        'picking_type_id': picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                        'location_id': self.partner_id.property_stock_supplier.id,
                        'move_type': 'direct'
                    }
                    print(pick)
                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                moves = order.invoice_line_ids.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking,
                                                                                             origin=order.invoice_origin,
                                                                                             picking_type_id=picking_type_id)
                move_ids = moves.sudo()._action_confirm()
                move_ids.sudo()._action_assign()
                picking.with_context(skip_backorder=True).button_validate()
                # immediate_transfer_obj = self.env['stock.immediate.transfer'].search(
                #     [('pick_ids', 'in', picking.ids)])
                # if not immediate_transfer_obj:
                #     immediate_transfer_obj = self.env['stock.immediate.transfer'].create(
                #         {'pick_ids': picking.ids,
                #          'immediate_transfer_line_ids': [(0, 0, {'to_immediate': True, 'picking_id': picking.id})]
                #          })
                # immediate_transfer_obj.sudo().process()
                # picking.sudo()._action_done()

    def action_post(self):
        res = super(InvoiceStockMove, self).action_post()
        if not self.invoice_origin and self.move_type != 'entry':
            self.sudo().action_stock_move()
        return res

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.

        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''

        if self.picking_type_id.code == 'outgoing':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id), ('code', '=', 'incoming')], limit=1)
            self.picking_type_id = data.id
        elif self.picking_type_id.code == 'incoming':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id), ('code', '=', 'outgoing')], limit=1)
            self.picking_type_id = data.id
        reverse_moves = super(InvoiceStockMove, self)._reverse_moves()
        return reverse_moves


class SupplierInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    def _create_stock_moves(self, picking, origin, picking_type_id):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            # if not origin:
            #     if picking_type_id.code == 'outgoing':
            #         qty_available = self.env['stock.quant']._get_available_quantity(line.product_id,
            #                                                                         picking.picking_type_id.default_location_src_id)
            #         if line.quantity > qty_available:
            #             raise ValidationError(_('Quantity out of stock %s has %s at location %s') % (
            #                 line.product_id.name, qty_available, picking.picking_type_id.default_location_src_id.display_name))
            price_unit = line.price_unit
            if picking.picking_type_id.code == 'outgoing':
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': picking.picking_type_id.default_location_src_id.id,
                    'location_dest_id': line.move_id.partner_id.property_stock_customer.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'price_unit': price_unit,
                    'quantity_done': line.quantity,
                    'picking_type_id': picking.picking_type_id.id,
                    'route_ids': 1 and [
                        (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            if picking.picking_type_id.code == 'incoming':
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': line.move_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'price_unit': price_unit,
                    'quantity_done': line.quantity,
                    'picking_type_id': picking.picking_type_id.id,
                    'route_ids': 1 and [
                        (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            diff_quantity = line.quantity
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
        return done
