from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    word_num = fields.Char(string="Amount In Words:", compute='_amount_in_word', store=True)

    @api.depends('amount_total')
    def _amount_in_word(self):
        for rec in self:
            rec.word_num = str(rec.currency_id.amount_to_text(rec.amount_total))



class ResCurrencyInherit(models.Model):
    _inherit = "res.currency"

    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name",translate=True)
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name",translate=True)

