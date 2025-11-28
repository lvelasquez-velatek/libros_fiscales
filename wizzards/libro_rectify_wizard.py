from odoo import models, fields, api

class LibroRectifyWizard(models.TransientModel):
    _name = 'libro.rectify.wizard'
    _description = 'Asistente de Rectificación de Libro'

    reason = fields.Text(string='Motivo de la Rectificación', required=True)

    def action_confirm(self):
        """Confirma la rectificación y llama al método en el modelo activo."""
        self.ensure_one()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        if active_id and active_model:
            record = self.env[active_model].browse(active_id)
            if hasattr(record, 'rectify_book'):
                record.rectify_book(self.reason)
            
        return {'type': 'ir.actions.act_window_close'}
