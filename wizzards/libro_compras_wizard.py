from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class LibroComprasWizard(models.TransientModel):
    _name = 'libro.compras.wizard'
    _description = 'Asistente para crear Libro de Compras'

    company_id = fields.Many2one('res.company', string='Empresa',
                                 required=True, default=lambda self: self.env.company)
    year = fields.Integer(string='Año', required=True, default=lambda self: datetime.now().year)
    month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', required=True)

    incluir_sucursales = fields.Boolean(
        string='Incluir Todas las Sucursales',
        default=False
    )
    
    contador_name = fields.Char(string='Nombre del Contador', required=True)
    periodo = fields.Char(string='Periodo', compute='_compute_periodo')

    @api.depends('year', 'month')
    def _compute_periodo(self):
        for rec in self:
            if rec.year and rec.month:
                meses = dict(self._fields['month'].selection)
                rec.periodo = f"{meses[rec.month]} {rec.year}"
            else:
                rec.periodo = False

    def action_create_periodo(self):
        """Crea un nuevo registro de libro de compras (solo el periodo)"""
        self.ensure_one()

        periodo = self.env['libro.compras.periodo'].create({
            'company_id': self.env.company.id,
            'year': self.year,
            'month': self.month,
            'incluir_sucursales': self.incluir_sucursales,
            'contador_name': self.contador_name,
        })

        # Redirige de nuevo a la lista principal
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'libro.compras.periodo',
            'view_mode': 'list,form',
            'name': 'Libro de Compras - Periodos',
        }
