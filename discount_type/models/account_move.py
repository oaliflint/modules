from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import odoo.addons.decimal_precision as dp
from decimal import Decimal
import math


class AccountAccountInherit(models.Model):
    _inherit = "account.account"

    name = fields.Char(string="Account Name", required=True, index=True, tracking=True, translate=True)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def onchange_product_id_uom_id(self):
        if self.product_id:
            uom_id = self.env['uom.uom'].search(
                [('category_id', '=', self.product_id.uom_id.category_id.id), ('uom_type', '=', 'reference')], limit=1)
            self.product_uom = uom_id.id if uom_id else self.product_id.uom_id.id


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False, default=date.today(),
                               states={'draft': [('readonly', False)]})
    inv_payment_type = fields.Selection(string="Invoice Type", selection=[('cash', 'Cash'), ('credit', 'Credit'), ],
                                        required=True, default='credit')

    def remove_fractions(self, val):
        if val % 1 == 0:
            val = int(val)
        else:
            val = "%.3f" % float(val)
        return val

    def get_amount_discount(self, amount_after_discount):
        if self.ks_global_discount_type == 'percent':
            if self.ks_global_discount_rate > 0:
                amount = (self.ks_global_discount_rate * amount_after_discount) / 100
                return "(" + str("%.3f" % amount) + ")" + " " + str("%.3f" % self.ks_global_discount_rate) + "%"
        else:
            percent = (self.ks_global_discount_rate / amount_after_discount) * 100
            return "(" + str("%.3f" % self.ks_global_discount_rate) + ")" + " " + str("%.3f" % percent) + "%"


    def button_process_edi_web_services(self):
        pass


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], default='amount',
                                            string='Discount Method:')
    global_discount_rate = fields.Monetary('Discount')

    amount_discount = fields.Monetary(string='Discount amount', compute='_compute_global_discount', store=True)

    # @api.onchange('product_id')
    # def onchange_product_id_uom_id(self):
    #     if self.product_id and self._context.get('default_move_type') == 'out_invoice':
    #         uom_id = self.env['uom.uom'].search(
    #             [('category_id', '=', self.product_id.uom_id.category_id.id), ('uom_type', '=', 'reference')], limit=1)
    #         self.product_uom_id = uom_id.id if uom_id else self.product_id.uom_id.id

    @api.onchange('global_discount_type', 'global_discount_rate', 'price_unit', 'quantity')
    def _onchange_global_discount_type(self):
        for line in self:
            disc = line.global_discount_rate > 0 and (
                    line.global_discount_rate / (line.price_unit * line.quantity)) * 100 or 0
            percent = line.global_discount_type == 'percent' and line.global_discount_rate or disc
            line.discount = percent

    def get_price_discount_after_digit(self, amount):
        for rec in self:
            if amount:
                amount = "%.3f" % amount
                return str(amount).split('.')[1]
            else:
                return 0

    @api.depends('quantity', 'price_unit', 'global_discount_type', 'global_discount_rate')
    def _compute_global_discount(self):
        for rec in self:
            amount_discount = self.calculate_discount(rec.quantity * rec.price_unit, rec.global_discount_rate,
                                                      rec.global_discount_type)
            rec.amount_discount = amount_discount

    @api.model
    def calculate_discount(self, amount, discount, discount_type):
        amount_discount = 0
        if discount_type == "amount":
            amount_discount = discount
        elif discount_type == "percent":
            if discount != 0.0:
                amount_discount = amount * (discount / 100.0)
            else:
                amount_discount = 0
        return amount_discount

    def truncate(self, f, n):
        return math.floor(f * 10 ** n) / 10 ** n
