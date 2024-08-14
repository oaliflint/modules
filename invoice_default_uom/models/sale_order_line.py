from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for rec in self:
            if rec.product_id and rec.product_id.product_tmpl_id.sale_uom_id:
                rec.product_uom = rec.product_id.product_tmpl_id.sale_uom_id

        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # @api.onchange("product_id")
    # @api.constrains("product_id")
    # def _onchange_product_id(self):
    #     res = super(AccountMoveLine, self)._onchange_product_id()
    #     for rec in self:
    #         if rec.product_id and rec.product_id.product_tmpl_id.sale_uom_id:
    #             rec.product_uom_id = rec.product_id.product_tmpl_id.sale_uom_id
    #
    #     return res


    def _get_computed_uom(self):
        for rec in self:
            if rec.product_id and rec.product_id.product_tmpl_id.sale_uom_id:
                return rec.product_id.product_tmpl_id.sale_uom_id
            elif rec.product_id:
                return rec.product_id.uom_id

            return False
