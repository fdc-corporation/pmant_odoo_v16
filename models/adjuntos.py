from odoo import models, fields, api
import mimetypes
class Adjunto(models.Model):
    _name        = 'adjunto.mantenimiento'
    _description = 'Adjuntos de Mantenimiento'
    name         = fields.Char(size=60,string='Referencia Archivo')
    adjunto      = fields.Binary()
    equipo       = fields.Many2one('maintenance.equipment',string='Equipo')
    #planequipoproceso   = fields.Many2one('planequipo.mantenimiento')


    def get_mimetype(self, filename):
        """Devuelve el tipo MIME basado en la extensión del archivo."""
        mimetype, _ = mimetypes.guess_type(filename)
        return mimetype or 'application/octet-stream'

class Adjunto_Atchmento(models.Model):
    _inherit = 'ir.attachment'

    id_equipo       = fields.Many2one('maintenance.equipment',string='Equipo')

# class AdjuntoImagw(models.Model):
#     _name        = 'adjuntoimage.mantenimiento'
#     name         = fields.Char(size=60,string='Referencia Archivo')
#     adjunto      = fields.Binary()
#     #equipo       = fields.Many2one('maintenance.equipment',string='Equipo')
#     planequipoproceso   = fields.Many2one('planequipoproceso.mantenimiento')
#     comentario          = fields.Text()
