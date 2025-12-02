from odoo import models, fields, api


class LibroVentasLine(models.Model):
    _name = 'libro.ventas.line'
    _description = 'Línea de Libro de Ventas'
    _order = 'sequence, id'

    periodo_id = fields.Many2one(
        'libro.ventas.periodo',
        string='Periodo',
        ondelete='cascade'
    )

    sequence = fields.Integer(string='No')

    # Campos de referencia
    move_id = fields.Many2one('account.move', string='Factura')
    partner_id = fields.Many2one('res.partner', string='Cliente')

    invoice_date = fields.Date(string='Fecha Emisión')

    # Campos específicos de ventas
    numero_documento = fields.Char(string='Número de Documento')
    numero_control = fields.Char(string='Número de Control')
    codigo_generacion = fields.Char(string='Código Generación')
    sello_recepcion = fields.Char(string='Sello Recepción')
    tipo_documento = fields.Char(string='Tipo Documento')
    tipo_documento_nombre = fields.Char(string='Tipo Documento', compute='_compute_tipo_documento_nombre')

    @api.depends('tipo_documento')
    def _compute_tipo_documento_nombre(self):
        doc_types = {
            '01': 'Consumidor Final',
            '03': 'Crédito Fiscal',
            '05': 'Nota de Crédito',
            '06': 'Nota de Débito',
            '11': 'Factura de Exportación',
            '14': 'Factura de Sujeto Excluido',
        }
        for rec in self:
            rec.tipo_documento_nombre = doc_types.get(rec.tipo_documento, rec.tipo_documento)

    # Moneda de la compañía (para el footer)
    currency_id = fields.Many2one(
        'res.currency',
        related='periodo_id.company_currency_id',
        store=True,
        readonly=True,
    )

    # --- CAMPOS PARA CSV HACIENDA (ANEXO 2 - CONSUMIDOR FINAL) ---
    
    # K. Ventas Exentas
    ventas_exentas = fields.Monetary(string='Ventas Exentas', default=0.0)
    
    # L. Ventas Internas Exentas no Sujetas a Proporcionalidad
    ventas_exentas_no_sujetas = fields.Monetary(string='Ventas Exentas No Sujetas', default=0.0)
    
    # M. Ventas No Sujetas
    ventas_no_sujetas = fields.Monetary(string='Ventas No Sujetas', default=0.0)
    
    # N. Ventas Gravadas Locales
    ventas_gravadas_locales = fields.Monetary(string='Ventas Gravadas Locales', default=0.0)
    
    # O. Exportaciones dentro del Área Centroamericana
    exportaciones_centroamerica = fields.Monetary(string='Exp. Centroamérica', default=0.0)
    
    # P. Exportaciones fuera del Área Centroamericana
    exportaciones_fuera_centroamerica = fields.Monetary(string='Exp. Fuera Centroamérica', default=0.0)
    
    # Q. Exportaciones de Servicios
    exportaciones_servicios = fields.Monetary(string='Exp. Servicios', default=0.0)
    
    # R. Ventas a Zonas Francas y DPA (Tasa Cero)
    ventas_zonas_francas = fields.Monetary(string='Ventas Zonas Francas', default=0.0)
    
    # S. Venta a Cuenta de Terceros No Domiciliados
    ventas_cuenta_terceros = fields.Monetary(string='Ventas Cuenta Terceros', default=0.0)
    
    # T. Total Ventas
    total_ventas = fields.Monetary(string='Total Ventas', default=0.0)
    
    # U. Tipo de Operación (Renta) - Enero 2025
    tipo_operacion_renta = fields.Selection([
        ('1', 'Gravada'),
        ('2', 'No Gravada o Exento'),
        ('3', 'Excluido o no Constituye Renta'),
        ('4', 'Mixta'),
        ('12', 'Ingresos sujetos de retención'),
        ('13', 'Sujetos pasivos excluidos'),
    ], string='Tipo Operación (Renta)', default='1', help='Requerido a partir de Enero 2025')
    
    # V. Tipo de Ingreso (Renta) - Enero 2025
    tipo_ingreso_renta = fields.Selection([
        ('1', 'Profesiones, Artes y Oficios'),
        ('2', 'Actividades de Servicios'),
        ('3', 'Actividades Comerciales'),
        ('4', 'Actividades Industriales'),
        ('5', 'Actividades Agropecuarias'),
        ('6', 'Utilidades y Dividendos'),
        ('7', 'Exportaciones de bienes'),
        ('8', 'Servicios en el Exterior'),
        ('9', 'Exportaciones de servicios'),
        ('10', 'Otras Rentas Gravables'),
        ('12', 'Ingresos sujetos de retención'),
        ('13', 'Sujetos pasivos excluidos'),
    ], string='Tipo Ingreso (Renta)', default='3', help='Requerido a partir de Enero 2025')



    ventas_gravadas = fields.Monetary(
        string="Ventas Gravadas",
        currency_field="currency_id",
        group_operator="sum",
    )

    debito_fiscal = fields.Monetary(
        string="Débito Fiscal",
        currency_field="currency_id",
        group_operator="sum",
    )

    amount_total = fields.Monetary(
        string="Total",
        currency_field="currency_id",
        group_operator="sum",
    )

    select = fields.Boolean(string='Seleccionar')
