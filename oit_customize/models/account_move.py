
from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Override _onchange_partner_id """
        res = super(AccountMove, self)._onchange_partner_id()
        for rec in self:
            if rec.partner_id.discount_percent:
                rec.ks_global_discount_rate = rec.partner_id.discount_percent
                rec.ks_global_discount_type = 'percent'
            for line in rec.invoice_line_ids:
                line.update({
                    'price_unit': line._get_computed_price_unit()
                })
                # line._onchange_price_subtotal()
                # line._onchange_price_subtotal()
                # line._onchange_amount_currency()
                # line._check_balanced()

        return res


class AccountMoveLine(models.Model):
    """
        Inherit Account Move Line:
         -
    """
    _inherit = 'account.move.line'

    customer_code = fields.Char(
        compute='_compute_customer_code'
    )

    @api.depends('product_id', 'partner_id')
    def _compute_customer_code(self):
        """ Compute customer_code value """
        for rec in self:
            codes = self.env['customer.code.line'].search([
                ('product_id', '=', rec.product_id.id),
                ('partner_id', '=', rec.partner_id.id),
            ])
            if codes:
                rec.customer_code = codes[0].customer_code

            else:
                rec.customer_code = ''
            # rec._get_computed_price_unit()

    def _get_computed_price_unit(self):
        ''' Helper to get the default price unit based on the product by taking care of the taxes
        set on the product and the fiscal position.
        :return: The price unit.
        '''
        self.ensure_one()

        if not self.product_id:
            return 0.0
        if self.move_id.is_sale_document(include_receipts=True):
            document_type = 'sale'
        elif self.move_id.is_purchase_document(include_receipts=True):
            document_type = 'purchase'
        else:
            document_type = 'other'
        line_ids = []
        if self.partner_id.group_category_id:
            move_lines = self.env['account.move.line'].sudo().search([
                ('partner_id.group_category_id', '=', self.partner_id.group_category_id.id),
                ('product_id', '=', self.product_id.id),
                ('price_unit', '!=', 0),
                ('exclude_from_invoice_tab', '=', False),
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted')], order="id desc", limit=1)

            if move_lines:
                # self.product_uom_id = move_lines.product_uom_id.id
                price = abs(move_lines.price_unit)
                return move_lines.product_uom_id._compute_price(price, self.product_uom_id)
            else:
                return self.product_id._get_tax_included_unit_price(
                    self.move_id.company_id,
                    self.move_id.currency_id,
                    self.move_id.date,
                    document_type,
                    fiscal_position=self.move_id.fiscal_position_id,
                    product_uom=self.product_uom_id
                )
        else:
            move_lines = self.env['account.move.line'].sudo().search([
                # ('partner_id.group_category_id', '=', self.partner_id.group_category_id.id),
                ('product_id', '=', self.product_id.id),
                ('partner_id', '=', self.partner_id.id),
                ('price_unit', '!=', 0),
                ('exclude_from_invoice_tab', '=', False),
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted')], order="id desc",  limit=1)

            if move_lines:
                # self.product_uom_id = move_lines.product_uom_id.id
                price = abs(move_lines.price_unit)
                return move_lines.product_uom_id._compute_price(price, self.product_uom_id)
            else:
                return self.product_id._get_tax_included_unit_price(
                    self.move_id.company_id,
                    self.move_id.currency_id,
                    self.move_id.date,
                    document_type,
                    fiscal_position=self.move_id.fiscal_position_id,
                    product_uom=self.product_uom_id
                )
