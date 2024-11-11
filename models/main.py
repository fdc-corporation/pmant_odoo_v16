import imaplib
import email
from email.header import decode_header
import webbrowser
import os
from getpass import getpass

# Datos del usuario
username = input("Correo: ")
password = getpass("Password: ")

# Crear conexión
imap = imaplib.IMAP4_SSL("imap.hostinger.com")
# iniciar sesión
imap.login(username, password)

status, mensajes = imap.select("INBOX")
print(mensajes)
# mensajes a recibir

# cantidad total de correos
mensajes = int(mensajes[0])
N = mensajes
for i in range(mensajes, mensajes - N, -1):
    # print(f"vamos por el mensaje: {i}")
#     # Obtener el mensaje
    try:
        res, mensaje = imap.fetch(str(i), "(RFC822)")
    except:
        break
    for respuesta in mensaje:
        if isinstance(respuesta, tuple):
            # Obtener el contenido
            mensaje = email.message_from_bytes(respuesta[1])
            # decodificar el contenido
            subject = decode_header(mensaje["Subject"])[0][0]
            if isinstance(subject, bytes):
                # convertir a string
                subject = subject.decode()
            # de donde viene el correo
            from_ = mensaje.get("From")
            print("Subject:", subject)
            print("From:", from_)
            print("Mensaje obtenido con exito")
            # si el correo es html
            if mensaje.is_multipart():
                # Recorrer las partes del correo
                for part in mensaje.walk():
                    # Extraer el contenido
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        # el cuerpo del correo
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
                    if content_type == "text/html":
                        # Obtener el contenido en HTML
                        html = part.get_payload(decode=True).decode()  # Decodificar el contenido
                        print("Contenido HTML:", html)
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        # Mostrar el cuerpo del correo
                        print(body)
                    elif "attachment" in content_disposition:
#                         # download attachment
                        nombre_archivo = part.get_filename()
                        if nombre_archivo:
                            if not os.path.isdir(subject):
                                # crear una carpeta para el mensaje
                                os.mkdir(subject)
                            ruta_archivo = os.path.join(subject, nombre_archivo)
                            # download attachment and save it
                            open(ruta_archivo, "wb").write(part.get_payload(decode=True))
            else:
                # contenido del mensaje
                content_type = mensaje.get_content_type()
                # cuerpo del mensaje
                body = mensaje.get_payload(decode=True).decode()
                if content_type == "text/plain":
#                     # mostrar solo el texto
                    print(body)
            # if content_type == "text/html":
            #     # Abrir el html en el navegador
            #     if not os.path.isdir(subject):
            #         os.mkdir(subject)
            #     nombre_archivo = f"{subject}.html"
            #     ruta_archivo = os.path.join(subject, nombre_archivo)
            #     open(ruta_archivo, "w").write(body)
            #     # abrir el navegador
            #     webbrowser.open(ruta_archivo)
#             print("********************************")
imap.close()
imap.logout()


# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from odoo.tools.misc import ustr
import stdnum
import logging
_logging = logging.getLogger(__name__)

STATE = [('ACTIVO', 'ACTIVO'),
                 ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
                 ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
                 ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
                 ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
                 ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
                 ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
                 ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
                 ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
                 ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
                 ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
                 ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
                 ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
                 ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')]

CONDITION = [('HABIDO', 'HABIDO'),
                         ('NO HABIDO', 'NO HABIDO'),
                         ('NO HALLADO', 'NO HALLADO'),
                         ('PENDIENTE', 'PENDIENTE'),
                         ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
                         ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
                         ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
                         ('-', 'NO HABIDO'),
                         ('NO HALLADO OTROS MOT', 'NO HALLADO OTROS MOT'),
                         ('NO APLICABLE', 'NO APLICABLE'),
                         ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
                         ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
                         ('POR VERIFICAR', 'POR VERIFICAR'),
                         ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
                         ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')]

class Pertner(models.Model):
        _inherit = "res.partner"

        doc_type = fields.Char(related="l10n_latam_identification_type_id.l10n_pe_vat_code")
        doc_number = fields.Char("Numero de documento", related="vat", store=True)
        commercial_name = fields.Char("Nombre commercial", default="-")
        legal_name = fields.Char("Nombre legal", default="-")
        state = fields.Selection(STATE, string='Estado', default="ACTIVO")
        condition = fields.Selection(CONDITION, string='Condicion', default='HABIDO')
        is_validate = fields.Boolean("Está validado")
        last_update = fields.Datetime("Última actualización")
        buen_contribuyente = fields.Boolean('Buen contribuyente')
        a_partir_del = fields.Date('A partir del')
        resolucion = fields.Char('Resolución')

        cod_doc_rel = fields.Char("Cod Doc relacionado", related="parent_id.l10n_latam_identification_type_id.l10n_pe_vat_code", store=True)
        numero_temp = fields.Char("Número doc relacionado", related="parent_id.vat", store=True)
        nombre_temp = fields.Char("Nombre relacionado", related="parent_id.name", store=True)

        es_agente_retencion = fields.Boolean('Es agente de retención')

        @api.model
        def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
            domain = domain or []

            # Verificar si name es una lista y convertirla en una cadena si es necesario
            if isinstance(name, list):
                name = ' '.join(name)  # Convertir la lista en una cadena unida por espacios

            # Asegurarse de que name es una cadena antes de aplicar split
            if isinstance(name, str) and name:
                name = name.split(' / ')[-1]

            # Si el nombre está presente, construir el dominio para la búsqueda
            if name and operator != 'in':
                domain = ['|', ('doc_number', operator, name), ('name', operator, name)] + domain

            return self._search(domain, limit=limit, order=order)




        @api.constrains('vat', 'country_id')
        def check_vat(self):
                # The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
                # This is for API pushes from external platforms where you have no control over VAT numbers.
                if self.env.context.get('no_vat_validation'):
                        return

                for partner in self:
                        country = partner.commercial_partner_id.country_id
                        if country.id == self.env.ref('base.pe').id:
                                return
                        if partner.vat and self._run_vat_test(partner.vat, country, partner.is_company) is False:
                                partner_label = _("partner [%s]", partner.name)
                                msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat, partner_label)
                                raise ValidationError(msg)


        @api.model
        def simple_vat_check(self, country_code, vat_number):
                '''
                Check the VAT number depending of the country.
                http://sima-pc.com/nif.php
                '''
                return True

                if country_code.upper() == 'PE':
                        return True
                if not ustr(country_code).encode('utf-8').isalpha():
                        return False
                check_func_name = 'check_vat_' + country_code
                check_func = getattr(self, check_func_name, None) or getattr(stdnum.util.get_cc_module(country_code, 'vat'), 'is_valid', None)
                if not check_func:
                        # No VAT validation available, default to check that the country code exists
                        if country_code.upper() == 'EU':
                                # Foreign companies that trade with non-enterprises in the EU
                                # may have a VATIN starting with "EU" instead of a country code.
                                return True
                        country_code = _eu_country_vat_inverse.get(country_code, country_code)
                        return bool(self.env['res.country'].search([('code', '=ilike', country_code)]))
                return check_func(vat_number)

class PertnerBank(models.Model):
        _inherit = "res.partner.bank"

        cci = fields.Char("CCI", help="Codigo cuenta interbancario")


