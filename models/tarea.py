from odoo import models, fields, api, exceptions
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AdjuntoEvaluacion (models.Model):
    _name = 'adjunto.evaluacion'
    _description = 'Adjuntos de evaluación'

    tarea  = fields.Many2one('tarea.mantenimiento', string="Tarea", invisible=True)
    adjuntoimage     = fields.Binary()



class TipoTarea(models.Model):
   _name = 'tipotarea.mantenimiento'
   name = fields.Char(size=25, required=True, string='Nombre')

class Tarea(models.Model):
    _name = 'tarea.mantenimiento'
    _description = 'Tareas de mantenimiento'

    _inherit = ['mail.thread', 'mail.activity.mixin']  # Hereda de mail.thread y mail.activity.mixin
    
    name = fields.Char(size=60, required=True, string='Nombre', write=['pmant.group_pmant_admin'])
    tipo = fields.Many2one('tipotarea.mantenimiento', string="Tipo")
    cliente = fields.Many2one('res.partner', string="Cliente", domain=[('is_company', '=', 'True')], required=False)
    ubicacion = fields.Many2one('res.partner', string="Ubicacion")
    planequipo = fields.One2many('planequipo.mantenimiento', 'tarea', string='Equipo / Plan', required=True, store=True)
    clasi1 = fields.Char(size=50, string="Clasificacion 1")
    clasi2 = fields.Char(size=50, string="Clasificacion 2")
    prioridad = fields.Selection(related="ots.priority")
    adjunto = fields.Binary()
    ots = fields.One2many('maintenance.request', 'tarea', string="ots")
    procesos = fields.One2many('planequipoproceso.mantenimiento', 'tarea', string="Estado de Procesos")
    state_id = fields.Many2one('maintenance.stage', string="Etapa", store=True)
    revisar = fields.Boolean()
    archive = fields.Boolean(related="ots.archive", store=True)
    namefirma = fields.Char(string="Nombre del Firmante")
    dni = fields.Char(string="DNI del Firmante")
    is_admin = fields.Boolean(compute="_is_admin", default=True)
    comentario = fields.Text('Comentario del firmante')
    creado_por = fields.Many2one('res.users', string="Creado por")
    fecha_entrada = fields.Date( string="Fecha de ingreso", compute="_fecha_entrada")
    create_user     = fields.Many2one('res.users', string='Creado por', default=lambda self: self.env.user)
    compania        = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    comentario_tecnico = fields.Text(string="Comentario ingreso")
    adjuntos_evaluaciones     = fields.One2many("adjunto.evaluacion", 'tarea', string='Adjuntos de Evaluacion')
    id_tipo = fields.Integer()
    fecha_hoy = fields.Char(string="Fecha Formateada", compute="_fecha_formateada")

    @api.onchange('tipo')
    def tipo_click(self):
        for record in self:
            if record.tipo.name == 'Evaluación' or record.tipo.name == 'Evaluacion':
                record.id_tipo = record.tipo.id
            else:
                record.id_tipo = 0

    @api.model
    def _fecha_formateada(self):
        # Diccionario para traducir el mes al español
        meses_espanol = {
            "January": "enero", "February": "febrero", "March": "marzo",
            "April": "abril", "May": "mayo", "June": "junio",
            "July": "julio", "August": "agosto", "September": "septiembre",
            "October": "octubre", "November": "noviembre", "December": "diciembre"
        }
        
        # Obtener la fecha actual
        fecha_actual = datetime.now()
        # Formatear la fecha con el mes en inglés y luego traducir
        fecha_formateada = fecha_actual.strftime("Lima, %d de %B del %Y")
        
        # Obtener el nombre del mes en inglés y buscar su traducción en el diccionario
        mes_en_ing = fecha_actual.strftime("%B")
        mes_en_espanol = meses_espanol.get(mes_en_ing, mes_en_ing)  # Usa el mes en inglés si no se encuentra en el diccionario
        fecha_formateada = fecha_formateada.replace(mes_en_ing, mes_en_espanol)

        # Asignar la fecha formateada a los registros
        for record in self:
            record.fecha_hoy = fecha_formateada
            for plan in record.planequipo:
                plan.fecha_hoy = fecha_formateada  # Asegúrate de que el campo exista en el modelo relacionado

        
    @api.model
    def create(self, vals):
        record = super(Tarea, self).create(vals)
        if 'state_id' in vals:
            record._notify_on_change()
        if 'create_user' not in vals:
            vals['create_user'] = self.env.user.id
        if 'compania' not in vals:
            vals['compania'] = self.env.company.id
        return record

    def write(self, vals):
        result = super(Tarea, self).write(vals)
        if 'state_id' in vals:
            for record in self:
                # Verificar si el registro tiene un ID válido
                if record.id:
                    # Actualizar solicitudes de mantenimiento relacionadas
                    ot = self.env['maintenance.request'].search([('tarea', '=', record.id)])
                    if ot:
                        ot.stage_id = record.state_id.id
                        if record.state_id.sequence == 3:
                            fecha_actual = fields.Date.today()
                            ot.fecha_ejec = fecha_actual
                # Si el estado tiene una secuencia específica (por ejemplo, 3)
                if record.state_id.sequence == 3:
                    record._fecha_ejecutada()
                    record._evento_calendario_proximo_servicio()
                    record._notify_on_change()
        return result

    def _fecha_entrada(self):
        for record in self:
            record.fecha_entrada = fields.Date.today()
    
    def _notify_on_change(self):
        for record in self:
            if record.state_id.id == 3:
                message = f"La tarea {record.name} se cambió a {record.state_id.name}. Verificar estado de la tarea realizada."
                partners_to_notify = [ot.user_id.partner_id.id for ot in record.ots if ot.user_id and ot.user_id.partner_id]
                if partners_to_notify and record.id:  # Asegurarse de que el registro está guardado
                    record.message_notify(
                        body=message,
                        partner_ids=partners_to_notify,
                        subject="Actualización de Tarea"
                    )
                    
    def _fecha_ejecutada(self):
        fecha_actual = fields.Date.today()
        for record in self:
            for equipo in record.planequipo:
                equipo.write({'fecha_ejec': fecha_actual})




    def _evento_calendario_proximo_servicio(self):
        for record in self:
            cliente = record.cliente.name
            ubicacion = record.ubicacion.name
            planes_por_fecha = {}
            partner_ids = set()
            
            for ot in record.ots:
                if ot.user_id:
                    partner_ids.add(ot.user_id.partner_id.id)
                if ot.employee_id:
                    partner_ids.add(ot.employee_id.user_id.partner_id.id)
                if ot.empresa:
                    partner_ids.add(ot.empresa.id)
                if ot.ubicacion:
                    partner_ids.add(ot.ubicacion.id)
            partner_ids = list(partner_ids)

            for plan in record.planequipo:
                fecha_ejecprox = plan.fecha_ejecprox
                equipo = plan.equipo.name
                alertas = plan.plan.alarm_ids
                if fecha_ejecprox not in planes_por_fecha:
                    planes_por_fecha[fecha_ejecprox] = []

                planes_por_fecha[fecha_ejecprox].append((equipo, alertas))

            for fecha, equipos_alertas in planes_por_fecha.items():
                descripcion_equipos = ", ".join([equipo for equipo, _ in equipos_alertas])
                event = self.env['calendar.event'].create({
                    'name': f'Servicio de {cliente}',
                    'start': fecha,
                    'stop': fecha,
                    'allday': False,
                    'location': ubicacion,
                    'description': f'Servicios de equipos: {descripcion_equipos}',
                    'partner_ids': [(6, 0, partner_ids)],
                })

                for _, alertas in equipos_alertas:
                    if alertas:
                        event.alarm_ids = [(4, alarma.id) for alarma in alertas]

    # @api.multi
    
            

   
    # @api.onchange('state_id')
    # def fecha_prox_equipo(self):
    #     for record in self:
    #         print('----------------------------------')
    #         print(self.id)
    #         # Busca una solicitud de mantenimiento relacionada con la tarea actual
    #         ot = self.env['maintenance.request'].search([("tarea.id", "=", self.id)])
    #         print('----------------------------------')
    #         print(ot)
    #         if ot:
                
    #             ot.stage_id = record.state_id.id
    #             print('----------------------------------')
    #             print(ot.stage_id)
    #        # Si el estado tiene una secuencia específica (en este caso, 3)
    #         if record.state_id.sequence == 3:
    #             # Llama a métodos internos para realizar acciones adicionales
    #             self._notify_on_change()
    #             self._fecha_ejecutada()
    #             self._evento_calendario_proximo_servicio()

