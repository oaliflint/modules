""" Initialize Customer Code """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class CustomerCode(models.Model):
    """
        Initialize Customer Code:
         -
    """
    _name = 'customer.code'
    _description = 'Customer Code'
    _sql_constraints = [
        ('unique_partner_id',
         'UNIQUE(partner_id)',
         'Customer must be unique'),
    ]

    partner_id = fields.Many2one(
        'res.partner',
        'Customer',
        copy=False
    )
    customer_code_line_ids = fields.One2many(
        'customer.code.line',
        'customer_code_id',
        copy=True
    )


class CustomerCodeLine(models.Model):
    """
        Initialize Customer Code Line:
         -
    """
    _name = 'customer.code.line'
    _description = 'Customer Code Line'
    _sql_constraints = [('order_product_uniq', 'unique (customer_code_id,product_id)',
                         'Duplicate products in lines not allowed !')]

    # product_template_id = fields.Many2one(
    #     'product.template'
    # )
    product_id = fields.Many2one(
        'product.product',
        # domain="[('product_tmpl_id', '=', product_template_id)]"
    )
    customer_code = fields.Char()
    customer_code_id = fields.Many2one(
        'customer.code'
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='customer_code_id.partner_id'
    )