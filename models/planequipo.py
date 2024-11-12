from odoo import models, fields, api
from datetime import datetime, timedelta

class PlanEquipo(models.Model):
    _name = 'planequipo.mantenimiento'

    name = fields.Char(compute='_generate_name')
    plan = fields.Many2one('plan.mantenimiento', string='Plan de Tarea')
    equipo = fields.Many2one('maintenance.equipment', string='Equipo', required=True)
    ubicacion = fields.Many2one('res.partner', string='Ubicacion')
    cliente = fields.Many2one('res.partner', string='Cliente')
    tarea = fields.Many2one('tarea.mantenimiento', string='Tarea', required=True)
    ots = fields.One2many('maintenance.request', 'tarea', related="tarea.ots")
    procesos = fields.One2many('planequipoproceso.mantenimiento', 'planequipo', string="Procesos a Utilizar")
    fecha_ejec = fields.Date(string="Fecha", readonly="True", store=True)
    is_admin = fields.Boolean(compute="_generate_tecnico", default=True)
    creador_id = fields.Integer(compute="_generate_tecnico")
    fecha_ejecprox = fields.Date(compute="_generate_tecnico", store=True)
    avisado = fields.Boolean(default=False)
    estado = fields.Char(string="Estado", related="tarea.state_id.name")

    @api.depends('fecha_ejec')
    def _generate_tecnico(self):
        for record in self:
            record.creador_id = record.equipo.create_uid.id
            record.is_admin = self.env['res.users'].has_group('pmant.group_pmant_admin')

            if record.fecha_ejec:
                fecha_prox = datetime.strptime(str(record.fecha_ejec), '%Y-%m-%d')
                fecha_prox += timedelta(days=(record.plan.frecuencia * record.plan.tipo.dias))
                record.fecha_ejecprox = fecha_prox

    def _generate_name(self):
        for record in self:
            if record.fecha_ejec:
                fechaj = " - " + str(record.fecha_ejec)
            else:
                fechaj = " - EN PROCESO"
            record.name = f"{record.equipo.name} - {record.plan.name}{fechaj}"

    @api.onchange('plan')
    def _onchange_procesos(self):
        if self.plan and self.plan.proceso:
            self.procesos = [(5, 0, 0)]  # Limpia los procesos existentes
            procesos_list = []
            for proceso_plan in self.plan.proceso:
                procesos_list.append((0, 0, {
                    'proceso': proceso_plan.id,
                    'planequipo': self.id,
                    'tarea': self.tarea.id,
                    'plan': self.plan.id,
                }))
            self.procesos = procesos_list

