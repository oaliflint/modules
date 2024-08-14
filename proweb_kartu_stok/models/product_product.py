# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.template'
    unique_uom_id = fields.Many2one('uom.uom',string='Uom For Card Report')

    unique_uom_categ_id = fields.Many2one('uom.category',related='uom_id.category_id',store=True)