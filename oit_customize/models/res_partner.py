""" Initialize Res Partner """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class ResPartner(models.Model):
    """
        Inherit Res Partner:
         - 
    """
    _inherit = 'res.partner'
    
    discount_percent = fields.Float(

    )