from odoo import models, fields, api
class Adjunto(models.Model):
    _name        = 'adjunto.mantenimiento'
    _description = 'Adjuntos de Mantenimiento'
    name         = fields.Char(size=60,string='Referencia Archivo')
    adjunto      = fields.Binary()
    equipo       = fields.Many2one('maintenance.equipment',string='Equipo')
    #planequipoproceso   = fields.Many2one('planequipo.mantenimiento')
    
class AdjuntoImagw(models.Model):
    _name        = 'adjuntoimage.mantenimiento'
    name         = fields.Char(size=60,string='Referencia Archivo')
    adjunto      = fields.Binary()
    #equipo       = fields.Many2one('maintenance.equipment',string='Equipo')
    planequipoproceso   = fields.Many2one('planequipoproceso.mantenimiento')
    comentario          = fields.Text()
