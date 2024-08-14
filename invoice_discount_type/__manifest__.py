# -*- coding: utf-8 -*-
{
    'name': "Invoice Discount Type",
    'name': "Invoice Discount Type",

    'description': """
        1.Add types to invoice line discount (fixed, percentage). \n
        2.Add global discount in account configuration. \n
        - it's recommended to increase the discount accuracy digits for more accurate calculations.

    """,
    'author': "",
    'website': "",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['base', 'account', ],
    'data': [
        'views/account_move_inherit_view.xml',
        'views/product_inherit_view.xml',
        'views/res_config_settings_inherit_view.xml',
        'reports/invoice_report_templates.xml',
    ],

}
