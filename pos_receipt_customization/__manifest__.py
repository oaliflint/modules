# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'POS Receipt Customization',
    'category': 'Sales/Point of Sale',
    'summary': 'POS Custom Receipt',
    'description': "Customized our point of sale receipt",
    'version': '15.0.1.0',
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'web.assets_qweb': [
            "pos_receipt_customization/static/src/xml/pos.xml",
        ],
    },
    'installable': True,
}
