from odoo import http
from odoo.http import request
from datetime import date, datetime, timedelta
import logging
import base64
import math

_logger = logging.getLogger(__name__)

class PortalPmant(http.Controller):




    @http.route(['/my/sedes/', '/my/sedes/page/<int:pagina>'], type='http', auth="user", website=True)
    def sedes_portal(self, pagina=1):
        user_partner = request.env.user.partner_id
        _logger.info(f"User Partner: {user_partner}")
        dominio_web = request.httprequest.host

        # Número de registros por página
        registros_por_pagina = 15

        if user_partner.is_company:
            # Obtener el total de sedes y calcular el número de páginas
            total_sedes = request.env['res.partner'].sudo().search_count([('parent_id', '=', user_partner.id)])
            total_paginas = math.ceil(total_sedes / registros_por_pagina)

            # Obtener las sedes para la página actual
            offset = (pagina - 1) * registros_por_pagina
            sedes = request.env['res.partner'].sudo().search(
                [('parent_id', '=', user_partner.id)], 
                limit=registros_por_pagina, 
                offset=offset
            )

            _logger.info(f"Sedes found: {sedes}")
            return request.render('pmant.sedes_portal', {
                'sedes': sedes,
                'user_partner': user_partner,
                'dominio': dominio_web,
                'pagina_actual': pagina,
                'total_paginas': total_paginas,
            })
        else:
            return request.redirect(f"/my/sede/{user_partner.id}/equipos/")




    # EQUIPOS POR SEDES - REGISTRADO A LA UBICACION
    @http.route([
        '/my/sede/<int:sede_id>/equipos/', 
        '/my/sede/<int:sede_id>/equipos/page/<int:pagina>'
    ], type="http", auth="user", website=True)
    def equipos_sede(self, sede_id, filtro=None, pagina=1, **kw):
        # Número de registros por página
        per_page = 15
        domain = [('ubicacion', '=', sede_id)]

        # Aplicar filtro si existe
        if filtro:
            domain.append(('name', 'ilike', filtro))

        # Calcular el total de equipos y el número total de páginas
        total_equipos = request.env['maintenance.equipment'].sudo().search_count(domain)
        total_paginas = math.ceil(total_equipos / per_page)

        # Calcular el offset para la página actual
        offset = (pagina - 1) * per_page

        # Obtener los equipos para la página actual
        equipos = request.env['maintenance.equipment'].sudo().search(domain, limit=per_page, offset=offset)
        ubicacion = request.env['res.partner'].sudo().browse(sede_id)

        return request.render('pmant.equipos_sede', {
            'equipos': equipos,
            'ubicacion': ubicacion,
            'filtro': filtro,
            'pagina_actual': pagina,
            'total_paginas': total_paginas,
        })


    # EQUIPOS REGISTRADOS AL USUARIO DE LA CENTRAL
    @http.route(['/my/<int:empresa_id>/equipos/', '/my/<int:empresa_id>/equipos/page/<int:pagina>'], type="http", auth="user", website=True)
    def equipos_portal(self, empresa_id, pagina=1):
        user_partner = request.env.user.partner_id
        per_page = 15  # Número de registros por página

        # Definir el dominio para la búsqueda
        domain = [
            ('propietario', '=', empresa_id),
            ('ubicacion', '=', False)
        ]
        ubicaciones = request.env['res.partner'].sudo().search([('parent_id', '=', user_partner.id)])
        # Obtener el total de registros y calcular el número de páginas
        total_equipos = request.env['maintenance.equipment'].sudo().search_count(domain)
        total_paginas = math.ceil(total_equipos / per_page)

        # Calcular el offset para la página actual
        offset = (pagina - 1) * per_page

        # Obtener los equipos para la página actual
        equipos = request.env['maintenance.equipment'].sudo().search(domain, limit=per_page, offset=offset)

        return request.render('pmant.equipos_central', {
            'equipos': equipos,
            'user_partner': user_partner,
            'pagina_actual': pagina,
            'total_paginas': total_paginas,
            'ubicaciones' : ubicaciones,
            'empresa_id': empresa_id
        })

    @http.route(['/solicitud/equipo/'], type='http', auth="user", methods=['POST'], website=True)
    def solicitud_registro_equipo (self, **kwargs):
        # Recuperar los valores enviados desde el formulario
        ubicacion_id = kwargs.get('ubicacion_id')  # ID de la ubicación
        nombre_equipo = kwargs.get('nombre_equipo')  # Nombre del equipo
        marca_equipo = kwargs.get('marca_equipo')  # Marca del equipo
        modelo_equipo = kwargs.get('modelo')  # Marca del equipo
        numero_serie = kwargs.get('numero_serie')  # Número de serie
        fecha_registro = kwargs.get('fecha_registro')  # Fecha de registro
        imagen = kwargs.get('formFileMultiple')  # Archivo subido
        user_partner = request.env.user.partner_id

        # Validar que todos los campos requeridos estén presentes
        if not (nombre_equipo and marca_equipo and modelo_equipo and numero_serie and fecha_registro):
            return request.render('pmant.error_template', {'error': 'Todos los campos son obligatorios.'})
        image_data = base64.b64encode(imagen.read()) if imagen else False
        # Crear el equipo en el modelo maintenance.equipment
        equipment = request.env['maintenance.equipment'].sudo().create({
            'propietario': int(user_partner),
            'ubicacion': int(ubicacion_id) if ubicacion_id else None,
            'name': nombre_equipo,
            'marca': marca_equipo,
            'marca': modelo_equipo,
            'model': numero_serie,
            'effective_date': fecha_registro,
            'image': image_data  # Leer contenido del archivo
        })
        if ubicacion_id :
            return request.redirect(f"/my/sede/{int(ubicacion_id)}/equipos/")

        # Redirigir a una página de éxito o mostrar un mensaje
        return request.redirect(f"/my/{user_partner.id}/equipos/")


    # REGISTROS - DETALLES DEL EQUIPO

    @http.route(['/my/equipos/<int:equipo_id>/detalles'], type="http", auth="user", website=True)
    def detalle_equipo(self, equipo_id, filtro=None, pagina=1, **kw):
        user_partner = request.env.user.partner_id
        equipo = request.env['maintenance.equipment'].sudo().browse(equipo_id)
        return request.render('pmant.detalle_equipo', {
            'equipo': equipo,
        })

    
    @http.route(['/my/equipo/<int:equipo_id>/historial'], type="http", auth="user", website=True)
    def historial_mantenimiento (self, equipo_id):
        equipo = request.env['maintenance.equipment'].sudo().browse(equipo_id)
        return request.render('pmant.historial_mantenimiento', {'equipo': equipo})







    @http.route(['/my/equipos/descargar_documento/<int:adjunto_id>'], type='http', auth="user", website=True)
    def descargar_documento(self, adjunto_id, **kw):
        adjunto = request.env['adjunto.mantenimiento'].sudo().browse(adjunto_id)
        if not adjunto:
            return request.not_found()

        headers = [
            ('Content-Disposition', 'attachment; filename=%s' % adjunto.name)
        ]
        return request.make_response(adjunto.adjunto, headers=headers)



    # RUTA DE REPORTE DEL SERVICIO POR EQUIPO
    @http.route(['/my/equipos/reporte/<int:id_plan>'], type='http', auth="user", website=True)
    def generar_reporte(self, id_plan):
        plan = request.env['planequipo.mantenimiento'].sudo().search([('id', '=', int(id_plan))])
        data = {
                    'docs': plan
                }
        return request.render('pmant.reporte_tarea_asignada', data)


    # RUTA PARA SOLICITUD  DE MANTENIMIENTO POR EQUIPO
    @http.route(['/my/equipos/<int:id_equipo>/solicitud'], type='http', auth="user", website=True)
    def solicitud_servicio(self, id_equipo, **post):
        equipo = request.env['maintenance.equipment'].sudo().browse(id_equipo)
        usuario = request.env.user        
        return request.render('pmant.form_solicitud', {
            'equipo': equipo,
            'usuario': usuario
        })

    # RUTA PARA REGISTRAR LA SOLICITUD DE MANTENIMIENTO
    @http.route(['/solicitud/mantenimiento/'], type='http', auth="user", methods=['POST'], website=True)
    def registrar_solicitud(self, **post):
        # Recoger datos del formulario
        id_equipo = post.get('id_equipo')
        correo = post.get('correo')
        telefono = post.get('telefono')
        equipo = post.get('equipo')
        marca = post.get('marca')
        modelo = post.get('modelo')
        serie = post.get('serie')
        servicio = post.get('servicio')
        nombre = post.get('nombre', 'Cliente no especificado')

        # Formatear fecha actual
        fecha_actual = datetime.now()
        fecha_formateada = fecha_actual.strftime("%Y-%m-%d")
        grupo_manager = request.env.ref('pmant.group_pmant_manager')
        usuarios_manager = request.env['res.users'].sudo().search([
            ('groups_id', 'in', [grupo_manager.id]),
            ('login', '=', 'jdavila@fdc-corporation.com')
        ], limit=1)

        # Crear lead en CRM
        try:
            lead_solicitud = request.env['crm.lead'].sudo().create({
                'name': f'Solicitud mantenimiento - {equipo}',
                'user_id':usuarios_manager.id,
                'email_from': correo,
                'phone': telefono,
                'description': f'Solicitud admitida desde la web, https://fdccorp.com.pe <br/>'
               f'Cliente: {nombre} <br/>'
               f'Equipo: {equipo} <br/>'
               f'Modelo: {modelo} <br/>'
               f'Marca: {marca} <br/>'
               f'Fecha de solicitud: {fecha_formateada} <br/>'
               f'Tipo de servicio: {servicio}',
            })
        except Exception as e:
            _logger.error(f"Error al crear lead de CRM: {str(e)}")
            return request.render('pmant.error_template', {
                'error_message': 'No se pudo completar su solicitud debido a un error interno.'
            })
    

        if 'imagenes' in request.httprequest.files:
            images = request.httprequest.files.getlist('imagenes')
            _logger.info("Processing %d images", len(images))

            for image in images:
                if image.content_type in ['image/jpeg', 'image/png']:
                    image_data = image.read()
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': image.filename,
                        'type': 'binary',
                        'datas': base64.b64encode(image_data),
                        'res_model': 'crm.lead',
                        'res_id': lead_solicitud.id,
                        'mimetype': image.content_type,
                        'public': True,
                    })
                    _logger.info("Created attachment %s", attachment.id)
        else:
            _logger.warning("No images found in the upload")

        return request.redirect('/contactus-thank-you')


    # Descarga de reprote de equipos de la sede
    @http.route(['/download/reporte_sede_equipos/<int:id_ubicacion>'], type='http', auth='user', website=True)
    def download_reporte_sede_equipos(self, id_ubicacion):
        # Renderizar el PDF pasando el ID de la ubicación como una lista
        pdf = request.env.ref('pmant.report_reporte_sede_equipos').sudo()._render_qweb_pdf([id_ubicacion])[0]

        # Definir las cabeceras para la descarga del PDF
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename="Reporte_Sede_Equipos.pdf"')
        ]

        # Retornar la respuesta para descargar el archivo
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/download/planequipo/<int:planequipo>'], type='http', auth='public', website=True)
    def download_plaequipo(self, planequipo):
        # Renderizar el PDF pasando el ID de la ubicación como una lista
        pdf = request.env.ref('pmant.action_reporte_cert_operatividad').sudo()._render_qweb_pdf([planequipo])

        # Definir las cabeceras para la descarga del PDF
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename="Certificafo-operatividad.pdf"')
        ]

        # Retornar la respuesta para descargar el archivo
        return request.make_response(pdf, headers=pdfhttpheaders)