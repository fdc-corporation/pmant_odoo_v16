from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    ots = fields.Many2one('tarea.mantenimiento', string="OTs")

    def create_mantenimiento(self):
        for order in self:
            try:
                # Crear el registro de mantenimiento
                valores = {
                    'name': order.name + ' - Servicios de mantenimiento',
                    'cliente': order.partner_id.id,
                    'ubicacion': order.partner_shipping_id.id,
                }
                mantenimiento = self.env["tarea.mantenimiento"].create(valores)

                # Obtener el ID del mantenimiento creado
                mantenimiento_id = mantenimiento.id

                # Crear una lista de líneas de equipos a añadir
                lines_to_add = []  # Lista para agregar las líneas
                for line in order.order_line:
                    if line.display_type == 'line_section':  # Verificar si la línea es una sección
                        # Asegúrate de tener correctamente la cadena con 'name / serial_no'
                        cadena = line.name  # Suponiendo que el campo line.name tiene la estructura 'name / serial_no'
                        
                        partes = cadena.split(' / ')  # Dividir la cadena en base a la barra '/'
                        
                        if len(partes) > 1:
                            valor_despues_barra = partes[1]  # Obtener la parte después de la barra '/'
                            
                            # Buscar el equipo según el serial_no
                            equipo = self.env['maintenance.equipment'].search([('serial_no', '=', valor_despues_barra)], limit=1)
                            
                            if equipo:  # Verificar si se encontró el equipo
                                equipo_id = equipo.id
                                
                                # Añadir la línea a la lista solo si es una sección
                                lines_to_add.append((0, 0, {
                                    'equipo': equipo_id,
                                }))

                # Añadir todas las líneas a la tarea de mantenimiento
                mantenimiento.write({'planequipo': lines_to_add})
                self.write({
                    'ots' : mantenimiento_id
                })
            except UserError as e:
                raise UserError(f'Ups, no se logró crear una nueva solicitud de mantenimiento: {str(e)}')

