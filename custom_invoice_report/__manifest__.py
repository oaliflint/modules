# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
{
    'name': 'Custom Invoice PDF',
    'version': '15.0.1.0',
    'sequence': 1,
    'category': 'Generic Invoice',
    'summary': 'Custom Invoice PDF',
    'description': """
Custom Invoice PDF.
    """,
    'author': '',
    'website': '',
    "images": ['images/main_screenshot.png'],
    'depends': ['base','account'],
    'assets': {
        'web.report_assets_common': [
            '/custom_invoice_report/static/src/scss/cairofont.scss',
            '/custom_invoice_report/static/src/css/reports.css',
        ],
    },
    'data': [
        'views/invoice_report_view.xml',
        'report/invoice_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
