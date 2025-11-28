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

    ventas_exentas = fields.Monetary(
        string="Ventas Exentas",
        currency_field="currency_id",
        group_operator="sum",
    )

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
