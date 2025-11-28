from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class LibroVentasWizard(models.TransientModel):
    _name = 'libro.ventas.wizard'
    _description = 'Asistente para crear Libro de Ventas'

    company_id = fields.Many2one('res.company', string='Empresa',
                                 required=True, default=lambda self: self.env.company)
    year = fields.Integer(string='Año', required=True, default=lambda self: datetime.now().year)
    month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', required=True)
    
    contador_name = fields.Char(string='Nombre del Contador', required=True)
    periodo = fields.Char(string='Periodo', compute='_compute_periodo')
    tipo_libro = fields.Selection([
        ('consumidor', 'Consumidor Final'),
        ('credito', 'Crédito Fiscal'),
    ], string='Tipo de Libro', required=True)

    incluir_sucursales = fields.Boolean(
        string='Incluir Todas las Sucursales',
        default=False
    )

    @api.depends('year', 'month')
    def _compute_periodo(self):
        for rec in self:
            if rec.year and rec.month:
                meses = dict(self._fields['month'].selection)
                rec.periodo = f"{meses[rec.month]} {rec.year}"
            else:
                rec.periodo = False

    def action_create_periodo(self):
        """Crea un nuevo registro de libro de ventas (solo el periodo)"""
        self.ensure_one()

        periodo = self.env['libro.ventas.periodo'].create({
            'company_id': self.company_id.id,
            'year': self.year,
            'month': self.month,
            'contador_name': self.contador_name,
            'tipo_libro': self.tipo_libro,
            'incluir_sucursales': self.incluir_sucursales,
        })

        # Redirige a la lista según tipo de libro
        if self.tipo_libro == 'consumidor':
            action_ref = 'libros_fiscales.action_libro_consumidor_periodo_view'
        else:
            action_ref = 'libros_fiscales.action_libro_credito_periodo_view'

        return self.env.ref(action_ref).read()[0]
