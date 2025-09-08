# -*- coding: utf-8 -*-
{
    'name': "clinic",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','mail','sale_management'],

    # always loaded
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/act_views.xml',
        'views/cash_views.xml',
        'views/convention_views.xml',
        'views/appointment_views.xml',
        'views/admission_views.xml',
        'views/hc_base_views.xml',
        'views/menus.xml',
        'reports/bon.xml',
        'data/sequences.xml',
        'data/queue_stage_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

