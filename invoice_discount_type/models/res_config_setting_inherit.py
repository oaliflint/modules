# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    discount_product_id = fields.Many2one('product.product', string="Discount Product",
                                          domain=[('is_discount_product', '=', True)])
    use_global_discount = fields.Boolean(string="Use Global Discount")
    portal_allow_api_keys = fields.Boolean(string="portal_allow_api_keys")
    account_fiscal_country_id = fields.Boolean(string="portal_allow_api_keys")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['use_global_discount'] = bool(
            self.env['ir.config_parameter'].sudo().get_param('use_global_discount'))
        res['discount_product_id'] = int(
            self.env['ir.config_parameter'].sudo().get_param('discount_product_id'))
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('use_global_discount', self.use_global_discount)
        self.env['ir.config_parameter'].sudo().set_param('discount_product_id', self.discount_product_id.id)
        super(ResConfigSettings, self).set_values()
