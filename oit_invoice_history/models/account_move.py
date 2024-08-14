
from odoo import api, models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    last_price1 = fields.Float(
        'Last Invoice Price',
        readonly=1
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountMoveLine, self)._onchange_product_id()
        for record in self:
            line_ids = []
            if record.product_id:
                move_lines = self.env['account.move.line'].sudo().search([
                    ('partner_id', '=', record.partner_id.id),
                    ('product_id', '=', record.product_id.id),
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('move_id.state', '=', 'posted')])
                if move_lines:
                    for lines in move_lines:
                        line_ids.append(lines.id)
            final_list = sorted(line_ids, key=int, reverse=True)
            if len(final_list)>=1:
                last_price1 = self.env['account.move.line'].sudo().browse(final_list[0])
                record.last_price1 = last_price1.price_unit





