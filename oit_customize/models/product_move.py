""" Initialize Product Move """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class StockMoveLine(models.Model):
    """
        Inherit Stock Move Line:
         -
    """
    _inherit = 'stock.move.line'

    origin = fields.Char(
        related='move_id.picking_id.origin'
    )
    partner_id = fields.Many2one(
        related='picking_id.partner_id'
    )
    price_unit = fields.Float(
        related='move_id.price_unit'
    )
    qty_available = fields.Float(
        related='product_id.qty_available'
    )
