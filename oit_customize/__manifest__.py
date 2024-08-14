
{
    'name': 'Oit Customize',
    'summary': 'Oit Customize',
    'author': "OIT Solutions",
    'company': 'OIT Solutions',
    'website': "http://www.oit-solution.com",
    'version': '15.0.0.1.0',
    'category': "OIT Solutions/apps",
    'license': 'AGPL-3',
    'sequence': 1,
    'depends': [
        'base',
        'account',
        'stock',
        'universal_discount',
        'gts_partner_category',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'report/',
        # 'wizard/',
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/customer_code.xml',
        'views/stock_move.xml',
        # 'data/',
    ],
    'demo': [
        # 'demo/',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

