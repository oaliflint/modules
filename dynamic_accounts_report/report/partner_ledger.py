from odoo import api, models, _


class PartnerLedgerReport(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.partner_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('partner_ledger_pdf_report'):

            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             })
        return data


class PartnerLedgerPDF(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.partner_ledger_pdf'


    def _get_partner_total_data(self, partner_id):
        partner = self.env['res.partner'].browse(partner_id)
        basic_domain = [
            ('partner_id', '=', partner_id),
            ('state', 'not in', ['draft', 'cancel']),
        ]
        if partner.customer_rank > partner.supplier_rank:
            invoice_domain = basic_domain + [('move_type', '=', 'out_invoice')]
        else:
            invoice_domain = basic_domain + [('move_type', '=', 'in_invoice')]

        credit_domain = basic_domain + [('move_type', '=', 'out_refund')]
        debit_domain = basic_domain + [('move_type', '=', 'in_refund')]

        invoices = self.env['account.invoice.report'].read_group(invoice_domain, ['price_subtotal'], ['partner_id'])
        total_invoiced = sum(invoice['price_subtotal'] for invoice in invoices)

        credit_notes = self.env['account.invoice.report'].read_group(credit_domain, ['price_subtotal'], ['partner_id'])
        total_credit = sum(invoice['price_subtotal'] for invoice in credit_notes)

        refunds = self.env['account.invoice.report'].read_group(debit_domain, ['price_subtotal'], ['partner_id'])
        total_debit = sum(invoice['price_subtotal'] for invoice in refunds)

        total_refund = total_credit if partner.customer_rank > partner.supplier_rank else total_debit

        return {'total_invoiced': total_invoiced, 'total_credit': total_credit,
                'total_debit': total_debit,
                'total_refund': total_refund}

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('partner_ledger_pdf_report'):
            if data.get('report_data'):
                data.update({'partner_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             'get_partner_total_data': self._get_partner_total_data,
                             })
        return data
