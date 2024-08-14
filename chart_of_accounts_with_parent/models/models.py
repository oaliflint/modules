# -*- coding: utf-8 -*-

from odoo import models, fields, api


class chart_of_accounts_with_parent(models.Model):
    _inherit = 'account.account'
    acc_parent = fields.Many2one('account.account', string="Parent Account")
    acc_level = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
        ], string="Account Level")
    is_view = fields.Boolean(string="View", related='user_type_id.is_view', readonly="True")

    @api.onchange('acc_parent')
    def new_acc_code(self):
        if self.acc_parent:

            sql = "select MAX(code) maxcode from account_account where acc_parent = '" + str(self.acc_parent.id) + "'"
            self.env.cr.execute(sql)
            max_code = self.env.cr.fetchone()

            if max_code:
                try:
                    self.code = int(max_code[0]) + 1
                except:
                    if self.acc_level == "1":
                        self.code = str(self.acc_parent.code) + "1"
                    if self.acc_level == "2":
                        self.code = str(self.acc_parent.code) + "01"
                    if self.acc_level == "3":
                        self.code = str(self.acc_parent.code) + "001"
                    if self.acc_level == "4":
                        self.code = str(self.acc_parent.code) + "0001"
                    if self.acc_level == "5":
                        self.code = str(self.acc_parent.code) + "00001"
                    if self.acc_level == "6":
                        self.code = str(self.acc_parent.code) + "000001"
                    if not self.acc_level:
                        self.code = ""


class AccountAccountTypeInherit(models.Model):
    _inherit = 'account.account.type'
    is_view = fields.Boolean(string="View")
