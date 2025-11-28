from odoo import models, fields, api

class LibroComprasLine(models.Model):
    _name = 'libro.compras.line'
    _description = 'Línea de Libro de Compras'
    _order = 'sequence, id'

    periodo_id = fields.Many2one(
        'libro.compras.periodo',
        string='Periodo',
        ondelete='cascade'
    )

    sequence = fields.Integer(string='No')

    # Campos de referencia
    move_id = fields.Many2one('account.move', string='Factura')
    partner_id = fields.Many2one('res.partner', string='Proveedor')

    invoice_date = fields.Date(string='Fecha Emisión')

    codigo_mh = fields.Char(string='Código MH')
    tipo_documento = fields.Char(string='Tipo de Documento')
    tipo_documento_nombre = fields.Char(string='Tipo Documento', compute='_compute_tipo_documento_nombre')

    @api.depends('tipo_documento')
    def _compute_tipo_documento_nombre(self):
        doc_types = {
            '03': 'Crédito Fiscal',
            '05': 'Nota de Crédito',
            '06': 'Nota de Débito',
            '14': 'Sujeto Excluido',
        }
        for rec in self:
            rec.tipo_documento_nombre = doc_types.get(rec.tipo_documento, rec.tipo_documento)
    dcl = fields.Char(string='DCL')
    numero_documento = fields.Char(string='Número de Documento')
    numero_control = fields.Char(string='Número de Control')
    codigo_generacion = fields.Char(string='Código Generación')
    sello_digital = fields.Char(string='Sello Digital')

    # Moneda de la compañía (para el footer)
    currency_id = fields.Many2one(
        'res.currency',
        related='periodo_id.company_currency_id',
        store=True,
        readonly=True,
    )

    # === CAMPOS PARA CSV OFICIAL HACIENDA ===
    
    # Clase de Documento (Columna B)
    clase_documento = fields.Selection([
        ('1', 'Impreso por Imprenta/Tiquetes'),
        ('2', 'Formulario Único'),
        ('3', 'Otros (DM/MI)'),
        ('4', 'DTE - Documento Tributario Electrónico'),
    ], string='Clase de Documento', default='4', help='Tipo físico del documento')
    
    # DUI Proveedor (Columna P) - Opcional para personas naturales
    dui_proveedor = fields.Char(string='DUI Proveedor', size=9, 
        help='Solo para personas naturales (periodos desde enero 2022)')
    
    # NIT del Proveedor (Columna E) - Campo relacionado
    partner_nit = fields.Char(related='partner_id.vat', string='NIT Proveedor', readonly=True)
    
    # === CAMPOS MONETARIOS ===
    
    # Moneda de la compañía (para el footer)
    currency_id = fields.Many2one(
        'res.currency',
        related='periodo_id.company_currency_id',
        store=True,
        readonly=True,
    )
    
    # Columnas G, H, I - Compras/Internaciones/Importaciones Exentas
    compras_internas_exentas = fields.Monetary(
        string="Compras Internas Exentas",
        currency_field="currency_id",
        group_operator="sum",
        help="Columna G - Compras internas exentas y/o no sujetas"
    )
    
    internaciones_exentas = fields.Monetary(
        string="Internaciones Exentas",
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
        help="Columna H - Internaciones exentas desde zonas francas/DPA"
    )
    
    importaciones_exentas = fields.Monetary(
        string="Importaciones Exentas",
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
        help="Columna I - Importaciones exentas desde el exterior"
    )
    
    # Columnas J, K, L, M - Compras/Internaciones/Importaciones Gravadas
    compras_internas_gravadas = fields.Monetary(
        string="Compras Internas Gravadas",
        currency_field="currency_id",
        group_operator="sum",
        help="Columna J - Compras internas gravadas"
    )
    
    internaciones_gravadas_bienes = fields.Monetary(
        string="Internaciones Gravadas de Bienes",
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
        help="Columna K - Internaciones gravadas de bienes"
    )
    
    importaciones_gravadas_bienes = fields.Monetary(
        string="Importaciones Gravadas de Bienes",
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
        help="Columna L - Importaciones gravadas de bienes"
    )
    
    importaciones_gravadas_servicios = fields.Monetary(
        string="Importaciones Gravadas de Servicios",
        currency_field="currency_id",
        group_operator="sum",
        default=0.0,
        help="Columna M - Importaciones gravadas de servicios"
    )
    
    # Columna N - Crédito Fiscal
    credito_fiscal = fields.Monetary(
        string="Crédito Fiscal",
        currency_field="currency_id",
        group_operator="sum",
        help="Columna N - 13% del total de operaciones gravadas (J+K+L+M)"
    )
    
    # Columna O - Total
    amount_total = fields.Monetary(
        string="Total",
        currency_field="currency_id",
        group_operator="sum",
        help="Columna O - Total de la compra (G+H+I+J+K+L+M)"
    )
    
    # === CAMPOS DE CLASIFICACIÓN FISCAL ===
    
    # Columna Q - Tipo de Operación
    tipo_operacion = fields.Selection([
        ('1', 'Gravada'),
        ('2', 'No Gravada'),
        ('3', 'Excluido o no Constituye Renta'),
        ('4', 'Mixta'),
        ('9', 'Instituciones Públicas'),
    ], string='Tipo de Operación', default='1', required=True,
    help='Columna Q - Tipo de operación fiscal')
    
    # Columna R - Clasificación
    clasificacion = fields.Selection([
        ('1', 'Costo'),
        ('2', 'Gasto'),
        ('9', 'Instituciones Públicas'),
    ], string='Clasificación', default='1', required=True,
    help='Columna R - Clasificación del documento')
    
    # Columna S - Sector
    sector = fields.Selection([
        ('1', 'Industria'),
        ('2', 'Comercio'),
        ('3', 'Agropecuaria'),
        ('4', 'Servicios, Profesiones, Artes y Oficios'),
        ('9', 'Instituciones Públicas'),
    ], string='Sector Económico', default='4', required=True,
    help='Columna S - Sector económico de la empresa')
    
    # Columna T - Tipo de Costo/Gasto
    tipo_costo_gasto = fields.Selection([
        ('1', 'Gastos de Venta sin Donación'),
        ('2', 'Gastos de Administración sin Donación'),
        ('3', 'Gastos Financieros sin Donación'),
        ('4', 'Costo Artículos Producidos/Comprados Importaciones/Internaciones'),
        ('5', 'Costo Artículos Producidos/Comprados Interno'),
        ('6', 'Costos Indirectos de Fabricación'),
        ('7', 'Mano de obra'),
        ('8', 'Operaciones informadas en más de 1 anexo'),
        ('9', 'Instituciones Públicas'),
    ], string='Tipo Costo/Gasto', default='5', required=True,
    help='Columna T - Tipo específico de costo o gasto')

    # Campo de selección (existente)
    select = fields.Boolean(string='Seleccionar')
