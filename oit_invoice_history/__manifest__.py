
{
    'name': 'Invoice History',
    'summary': 'Invoice History',
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
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'report/',
        # 'wizard/',
        'views/account_move.xml',
        # 'data/',
    ],
    'demo': [
        # 'demo/',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

