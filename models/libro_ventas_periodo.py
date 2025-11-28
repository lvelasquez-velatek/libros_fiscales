from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io
import csv
import base64


class LibroVentasPeriodo(models.Model):
    _name = 'libro.ventas.periodo'
    _description = 'Periodo del Libro de Ventas'
    _rec_name = 'periodo'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    incluir_sucursales = fields.Boolean(
        string='Incluir Todas las Sucursales',
        default=False,
        help='Si está marcado, incluirá facturas de todas las sucursales de la empresa'
    )

    assistant_id = fields.Many2one(
        'res.users',
        string='Asistente',
        default=lambda self: self.env.user
    )

    contador_name = fields.Char(string='Contador')

    date = fields.Date(string='Fecha Emisión', required=True, default=fields.Date.context_today)

    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.context_today(self).year)
    month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', required=True)

    periodo = fields.Char(
        string='Periodo',
        readonly=True,
        compute='_compute_periodo',
        store=True,
    )

    tipo_libro = fields.Selection([
        ('consumidor', 'Consumidor Final'),
        ('credito', 'Crédito Fiscal'),
    ], string='Tipo de Libro', required=True, readonly=True)

    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
    ], string='Estado', default='draft', tracking=True)

    comentarios = fields.Text(string='Comentarios')

    def action_rectify(self):
        """Abre el wizard para rectificar el libro."""
        self.ensure_one()
        return {
            'name': 'Rectificar Libro',
            'type': 'ir.actions.act_window',
            'res_model': 'libro.rectify.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': self._name},
        }

    def rectify_book(self, reason):
        """Método llamado por el wizard para ejecutar la rectificación."""
        self.ensure_one()
        self.message_post(body=f"Libro rectificado. Motivo: {reason}", subtype_xmlid="mail.mt_note")
        self.state = 'draft'

    invoice_line_ids = fields.One2many(
        'libro.ventas.line',
        'periodo_id',
        string='Detalle Ventas',
        domain=[('move_id.state', '=', 'posted')]
    )

    invoice_line_ids_cancelled = fields.One2many(
        'libro.ventas.line',
        'periodo_id',
        string='Detalle Anuladas',
        domain=[('move_id.state', '=', 'cancel')]
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
        store=True,
    )

    # Campos calculados
    total_ventas_exentas = fields.Monetary(
        string="Total Ventas Exentas",
        compute="_compute_totales",
        currency_field="company_currency_id",
    )

    total_ventas_gravadas = fields.Monetary(
        string="Total Ventas Gravadas",
        compute="_compute_totales",
        currency_field="company_currency_id",
    )

    total_debito_fiscal = fields.Monetary(
        string="Total Débito Fiscal",
        compute="_compute_totales",
        currency_field="company_currency_id",
    )

    # ----------------- COMPUTADOS -----------------

    @api.depends('year', 'month')
    def _compute_periodo(self):
        for rec in self:
            if rec.year and rec.month:
                month_names = {
                    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
                    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
                    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
                }
                rec.periodo = f"{month_names.get(rec.month, '')} {rec.year}"
            else:
                rec.periodo = ''

    year_display = fields.Char(string='Año (Display)', compute='_compute_year_display', store=False)

    @api.depends('year')
    def _compute_year_display(self):
        for rec in self:
            rec.year_display = str(rec.year) if rec.year else ''

    # ----------------- ACCIONES DE SELECCIÓN -----------------

    def action_select_all(self):
        """Seleccionar todas las líneas."""
        for rec in self:
            rec.invoice_line_ids.write({'select': True})

    def action_unselect_all(self):
        """Deseleccionar todas las líneas."""
        for rec in self:
            rec.invoice_line_ids.write({'select': False})

    @api.depends("invoice_line_ids.ventas_exentas",
                 "invoice_line_ids.ventas_gravadas",
                 "invoice_line_ids.debito_fiscal")
    def _compute_totales(self):
        for rec in self:
            rec.total_ventas_exentas = sum(rec.invoice_line_ids.mapped("ventas_exentas"))
            rec.total_ventas_gravadas = sum(rec.invoice_line_ids.mapped("ventas_gravadas"))
            rec.total_debito_fiscal = sum(rec.invoice_line_ids.mapped("debito_fiscal"))

    # ----------------- RESTRICCIONES -----------------

    def write(self, vals):
        """Bloquea edición si el estado no es 'draft', excepto si se cambia el estado."""
        for rec in self:
            if rec.state != 'draft' and 'state' not in vals:
                raise UserError("Solo puedes modificar libros en estado Borrador.")
        return super().write(vals)

    # ----------------- ACCIONES DE ESTADO -----------------

    def action_mark_done(self):
        """Validar el libro."""
        for rec in self:
            rec.state = 'validated'

    def action_reset_to_draft(self):
        """Volver a borrador."""
        for rec in self:
            rec.state = 'draft'

    # ----------------- LÓGICA DE LIBRO -----------------

    def action_load_invoices(self):
        """Generar Detalle: carga facturas del mes según tipo de libro."""
        self.ensure_one()

        if not self.year or not self.month:
            raise UserError("Debe especificar Año y Mes.")

        # Calcular fechas
        date_from = datetime(self.year, int(self.month), 1).date()
        # Último día del mes
        date_to = (date_from + relativedelta(months=1, days=-1))

        # Determinar las compañías a incluir
        if self.incluir_sucursales:
            # Incluir empresa actual + todas sus sucursales
            company_ids = [self.company_id.id] + self.company_id.child_ids.ids
        else:
            # Solo la empresa actual
            company_ids = [self.company_id.id]

        # Limpiar líneas anteriores (tanto normales como anuladas)
        self.invoice_line_ids.unlink()
        self.invoice_line_ids_cancelled.unlink()

        # Definir tipos de documentos según el libro
        if self.tipo_libro == 'consumidor':
            # Facturas (01) y Notas de Crédito/Débito relacionadas a Consumidor
            # Nota: Ajustar códigos según la localización real si difieren
            allowed_doc_types = ['01', '05', '06'] 
        else:
            # Crédito Fiscal (03) y Notas de Crédito/Débito relacionadas
            allowed_doc_types = ['03', '05', '06']

        # --- 1. CARGAR FACTURAS VALIDAS (POSTED) ---
        invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', 'in', company_ids),
        ])

        lines_values = []
        sequence = 1

        for inv in invoices:
            # Filtrar por tipo de documento DTE
            doc_type_code = inv.l10n_latam_document_type_id.code
            if doc_type_code not in allowed_doc_types:
                continue

            # Mapeo de campos DTE
            numero_documento = inv.name
            numero_control = inv.tgr_l10n_sv_edi_numero_control or ''
            codigo_generacion = inv.tgr_l10n_sv_edi_codigo_generacion or ''
            sello_recepcion = inv.tgr_l10n_sv_edi_sello_recibido or ''
            tipo_documento = inv.l10n_latam_document_type_id.code or ''

            # Montos: desglosar según tipo de impuesto
            ventas_exentas = 0.0
            ventas_gravadas = 0.0
            debito_fiscal = 0.0

            # Iterar líneas de la factura para calcular montos
            for line in inv.invoice_line_ids:
                amount_line = line.price_subtotal

                # Determinar si es exento o gravado según impuesto
                if line.tax_ids:
                    # Si tiene impuesto, es gravado
                    ventas_gravadas += amount_line
                    # Débito fiscal = el monto del impuesto
                    debito_fiscal += line.price_total - amount_line
                else:
                    # Si no tiene impuesto, es exento
                    ventas_exentas += amount_line

            # Crear diccionario para la línea
            lines_values.append({
                'periodo_id': self.id,
                'sequence': sequence,
                'move_id': inv.id,
                'partner_id': inv.partner_id.id,
                'invoice_date': inv.invoice_date,
                'numero_documento': numero_documento,
                'numero_control': numero_control,
                'codigo_generacion': codigo_generacion,
                'sello_recepcion': sello_recepcion,
                'tipo_documento': tipo_documento,
                'ventas_exentas': ventas_exentas,
                'ventas_gravadas': ventas_gravadas,
                'debito_fiscal': debito_fiscal,
                'amount_total': inv.amount_total,
            })
            sequence += 1

        # Crear líneas de facturas válidas
        self.env['libro.ventas.line'].create(lines_values)

        # --- 2. CARGAR FACTURAS ANULADAS (CANCEL) ---
        cancelled_invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'cancel'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', 'in', company_ids),
        ])

        cancelled_lines_values = []
        # Reiniciar secuencia o continuar? Generalmente anuladas tienen su propia lista o se mezclan.
        # Aquí las pondremos en su propia pestaña, así que secuencia propia.
        seq_cancelled = 1

        for inv in cancelled_invoices:
            # Filtrar por tipo de documento DTE
            doc_type_code = inv.l10n_latam_document_type_id.code
            if doc_type_code not in allowed_doc_types:
                continue

            # Mapeo de campos DTE
            numero_documento = inv.name
            numero_control = inv.tgr_l10n_sv_edi_numero_control or ''
            codigo_generacion = inv.tgr_l10n_sv_edi_codigo_generacion or ''
            sello_recepcion = inv.tgr_l10n_sv_edi_sello_recibido or ''
            tipo_documento = inv.l10n_latam_document_type_id.code or ''

            # Para anuladas, los montos suelen ser 0 o se muestran informativamente.
            # El usuario pidió "el mismo filtro", asumiremos que quiere ver los datos aunque estén anuladas.
            # Pero contablemente no suman. En el reporte se verá.
            
            ventas_exentas = 0.0
            ventas_gravadas = 0.0
            debito_fiscal = 0.0

            for line in inv.invoice_line_ids:
                amount_line = line.price_subtotal
                if line.tax_ids:
                    ventas_gravadas += amount_line
                    debito_fiscal += line.price_total - amount_line
                else:
                    ventas_exentas += amount_line

            cancelled_lines_values.append({
                'periodo_id': self.id,
                'sequence': seq_cancelled,
                'move_id': inv.id,
                'partner_id': inv.partner_id.id,
                'invoice_date': inv.invoice_date,
                'numero_documento': numero_documento,
                'numero_control': numero_control,
                'codigo_generacion': codigo_generacion,
                'sello_recepcion': sello_recepcion,
                'tipo_documento': tipo_documento,
                'ventas_exentas': ventas_exentas,
                'ventas_gravadas': ventas_gravadas,
                'debito_fiscal': debito_fiscal,
                'amount_total': inv.amount_total,
            })
            seq_cancelled += 1

        # Crear líneas de facturas anuladas
        self.env['libro.ventas.line'].create(cancelled_lines_values)

    def action_generate_excel(self):
        """Generar archivo Excel (.xlsx) con las facturas seleccionadas."""
        selected = self.invoice_line_ids.filtered(lambda l: l.select)
        if not selected:
            raise UserError("Debe seleccionar al menos una factura.")

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
        except ImportError:
            raise UserError("La librería 'openpyxl' no está instalada. Instálela con: pip install openpyxl")

        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Libro de Ventas"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        # Encabezados
        headers = [
            'No', 'Fecha Emisión', 'Número de Documento', 'Número de Control',
            'Código Generación', 'Sello Recepción', 'Cliente', 'Ventas Exentas',
            'Ventas Gravadas', 'Débito Fiscal', 'Total'
        ]
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        # Datos
        for row, line in enumerate(selected, start=2):
            ws.cell(row=row, column=1, value=line.sequence or '')
            ws.cell(row=row, column=2, value=str(line.invoice_date) if line.invoice_date else '')
            ws.cell(row=row, column=3, value=line.numero_documento or '')
            ws.cell(row=row, column=4, value=line.numero_control or '')
            ws.cell(row=row, column=5, value=line.codigo_generacion or '')
            ws.cell(row=row, column=6, value=line.sello_recepcion or '')
            ws.cell(row=row, column=7, value=line.partner_id.name or '')
            ws.cell(row=row, column=8, value=line.ventas_exentas or 0)
            ws.cell(row=row, column=9, value=line.ventas_gravadas or 0)
            ws.cell(row=row, column=10, value=line.debito_fiscal or 0)
            ws.cell(row=row, column=11, value=line.amount_total or 0)

        # Guardar en memoria
        output = io.BytesIO()
        wb.save(output)
        excel_data = base64.b64encode(output.getvalue())
        output.close()

        tipo_nombre = 'Consumidor_Final' if self.tipo_libro == 'consumidor' else 'Credito_Fiscal'
        attachment = self.env['ir.attachment'].create({
            'name': f'Libro_Ventas_{tipo_nombre}_{self.periodo or ""}.xlsx',
            'type': 'binary',
            'datas': excel_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_generate_csv(self):
        """Generar CSV con las facturas seleccionadas."""
        selected = self.invoice_line_ids.filtered(lambda l: l.select)
        if not selected:
            raise UserError("Debe seleccionar al menos una factura.")

        output = io.StringIO()
        writer = csv.writer(output)

        # Encabezados
        writer.writerow([
            'No',
            'Fecha Emisión',
            'Número de Documento',
            'Número de Control',
            'Código Generación',
            'Sello Recepción',
            'Cliente',
            'Ventas Exentas',
            'Ventas Gravadas',
            'Débito Fiscal',
            'Total'
        ])

        # Filas de datos
        for line in selected:
            writer.writerow([
                line.sequence or '',
                line.invoice_date or '',
                line.numero_documento or '',
                line.numero_control or '',
                line.codigo_generacion or '',
                line.sello_recepcion or '',
                line.partner_id.name or '',
                line.ventas_exentas or 0,
                line.ventas_gravadas or 0,
                line.debito_fiscal or 0,
                line.amount_total or 0,
            ])

        data = base64.b64encode(output.getvalue().encode())
        output.close()

        tipo_nombre = 'Consumidor_Final' if self.tipo_libro == 'consumidor' else 'Credito_Fiscal'
        attachment = self.env['ir.attachment'].create({
            'name': f'Libro_Ventas_{tipo_nombre}_{self.periodo or ""}.csv',
            'type': 'binary',
            'datas': data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_print_report(self):
        """Imprimir: genera el PDF del libro."""
        return self.env.ref('libros_fiscales.report_libro_ventas').report_action(self)
