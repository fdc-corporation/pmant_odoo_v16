from odoo import api, models, fields


class EventoCalendario (models.Model):
    _inherit = 'calendar.event'
    
    ots_id = fields.Many2one('maintenance.request', string='OTS')