{
    'name': 'Libros Fiscales - Compras y Ventas',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Genera reportes de Libros de Compras y Ventas según normativa fiscal',
    'author': 'VELATEK',
    'depends': ['account', 'tgr_l10n_sv', 'mail'],  # Depende de tu localización
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Acciones (wizards, menús, etc.) - ANTES de las vistas
        'wizzards/libro_rectify_wizard_views.xml',
        'actions/libro_compras_action.xml',
        'actions/libro_ventas_action.xml',
        
        # Vistas
        'views/libro_compras_views.xml',
        'views/libro_ventas_views.xml',

        # Paperformats
        'reports/paperformat.xml',
        
        # Reportes
        'reports/libro_compras_report.xml',
        'reports/libro_ventas_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
