# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json




class AccountMove(models.Model):
    _inherit = 'account.move'

    total_discount = fields.Monetary(string='Discount', compute='calc_total_discount')
    discount_type = fields.Selection(selection=[('amount', 'Amount'), ('percentage', 'Percentage')],
                                     string='Global Discount Type', copy=False)
    global_discount_amount = fields.Monetary(string='Global Discount Amount', copy=False)
    global_discount_percentage = fields.Float(string='Global Discount Percentage', copy=False)
    use_global_discount = fields.Boolean(string="Use Global Discount", compute="_get_use_global_discount")
    invoice_discount_type = fields.Selection(string="Discount Type", selection=[('globle', 'Globle Discount'), ('line', 'Per Line'),],default='globle')


    def button_process_edi_web_services(self):
        pass

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move._payment_state_matters():
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)

            currency = currencies if len(currencies) == 1 else move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move._payment_state_matters() and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (
                        reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move._payment_state_matters():
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            discount_total = sum(move.invoice_line_ids.filtered(lambda x:x.product_id.is_discount_product).mapped('price_subtotal')) if move.invoice_discount_type == 'globle' else 0.0
            move.amount_untaxed = sign * ((total_untaxed_currency if len(currencies) == 1 else total_untaxed)+discount_total)
            move.amount_tax = sign * ((total_tax_currency if len(currencies) == 1 else total_tax) + discount_total)
            move.amount_total = sign * ((total_currency if len(currencies) == 1 else total) + discount_total)
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = abs(move.amount_total) if move.move_type == 'entry' else -(
                        sign * move.amount_total)

            currency = currencies if len(currencies) == 1 else move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move._payment_state_matters() and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (
                        reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

    @api.onchange('discount_type', 'global_discount_amount')
    def reset_discount_fields(self):
        for rec in self:
            if rec.discount_type and rec.use_global_discount:
                if rec.discount_type == 'amount':
                    rec.global_discount_percentage = 0
                elif rec.discount_type == 'percentage':
                    rec.global_discount_amount = 0
            else:
                rec.global_discount_amount = 0
                rec.global_discount_percentage = 0

    @api.depends('partner_id')
    def _get_use_global_discount(self):
        for rec in self:
            rec.use_global_discount = bool(self.env['ir.config_parameter'].sudo().get_param('use_global_discount'))

    @api.constrains('discount_type', 'global_discount_amount', 'global_discount_percentage', 'invoice_line_ids')
    def _check_discount_value(self):
        for record in self:
            if record.use_global_discount and (
                    record.discount_type == 'percentage' or record.discount_type == 'amount'):
                discount_amount = 0.0
                if not record.invoice_line_ids:
                    raise ValidationError("Please enter invoice lines to apply global discount.")
                if record.discount_type == 'percentage' and (
                        record.global_discount_percentage >= 100 or record.global_discount_percentage <= 0):
                    raise ValidationError("Discount Percentage should be between 1 and 100.")

                if record.discount_type == 'amount' and record.global_discount_amount <= 0:
                    raise ValidationError("Discount Amount should be greater than 0.")

                discount_product_id = int(self.env['ir.config_parameter'].sudo().get_param('discount_product_id'))
                if not discount_product_id:
                    raise ValidationError("You need to add  discount product in configuration.")
                product_discount_obj = self.env['product.product'].browse(discount_product_id)
                if record.id:
                    # check if discount product exists or not
                    account_move_line_obj = self.env['account.move.line'].search(
                        [('move_id', '=', record.id), ('product_id', '=', product_discount_obj.id)])
                    if record.discount_type == 'percentage':
                        discount_amount = (-1 * (record.amount_untaxed * record.global_discount_percentage)) / 100.0
                    elif record.discount_type == 'amount':
                        discount_amount = -1 * record.global_discount_amount

                    if account_move_line_obj:
                        account_move_line_obj.write({'price_unit': discount_amount})
                    else:
                        account_id = False
                        fiscal_position = self.fiscal_position_id
                        accounts = product_discount_obj.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                        if self.is_sale_document(include_receipts=True):
                            # Out invoice.
                            account_id = accounts['income']
                        elif self.is_purchase_document(include_receipts=True):
                            # In invoice.
                            account_id = accounts['expense']
                        account_move_line_values = [(0, 0, {
                            'product_id': product_discount_obj.id,
                            'move_id': record.id,
                            'is_discount_line': True,
                            'price_unit': discount_amount,
                            'discount_type': '',
                            'name': product_discount_obj.name,
                            'quantity': 1,
                            'account_id': account_id.id,
                        })]
                        record.invoice_line_ids = account_move_line_values
            else:
                move_line_obj = self.env['account.move.line'].search(
                    [('move_id', '=', record.id), ('is_discount_line', '=', True)])
                if move_line_obj:
                    move_line_obj.sudo().unlink()

    @api.depends('invoice_line_ids')
    def calc_total_discount(self):
        for rec in self:
            total_discount = 0.0
            if rec.invoice_line_ids:
                for line in rec.invoice_line_ids:
                    if line.discount_type == 'fixed':
                        if line.price_unit and line.quantity:
                            discount = (line.discount_amount / (line.price_unit * line.quantity)) * 100
                        else:
                            discount = 0.0
                    else:
                        discount = line.discount_amount
                    total_discount += (line.quantity * line.price_unit * discount / 100)
                total_discount += sum(abs(line.price_unit) for line in rec.invoice_line_ids if line.is_discount_line)
                rec.total_discount = total_discount
            else:
                rec.total_discount = 0.0

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                                                                                      quantity=quantity,
                                                                                      currency=currency,
                                                                                      product=product, partner=partner,
                                                                                      is_refund=move_type in (
                                                                                      'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_type = fields.Selection([('fixed', 'Fixed'), ('percent', 'Percent')], string='Discount Type',
                                     default='fixed')
    discount_amount = fields.Float('Discount')
    sub_total_before_discount = fields.Monetary(string='Subtotal Before Disc.', help='Show Subtotal before discount',
                                                compute='_compute_subtotal_before_discount')
    is_discount_line = fields.Boolean(string='Is Discount', default=False)

    @api.depends('price_unit', 'quantity')
    def _compute_subtotal_before_discount(self):
        for rec in self:
            rec.sub_total_before_discount = rec.quantity * rec.price_unit
