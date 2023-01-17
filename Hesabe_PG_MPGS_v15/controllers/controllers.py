# -*- coding: utf-8 -*-

import json
import werkzeug
from odoo import http
from odoo.http import request
import PyPDF2
from odoo.addons.Hesabe_PG_MPGS_v15.models.hesabecrypt import decrypt


class HesabeController(http.Controller):
    
    @http.route(['/payment/hesabe/mpgs/return',
                 '/payment/hesabe/mpgs/fail'], type='http', auth='public', csrf=False, methods=['GET'], save_session=False
    )
    def hesabe_mpgs_return(self, **post):
        hesabe = request.env['payment.acquirer'].search([('provider', '=', 'Hesabe_PG_MPGS_v15')], limit=1).sudo()
        data = decrypt(post['data'], hesabe.secret_key, hesabe.iv_key)
        response = json.loads(data)
        if post:
            request.env['payment.transaction'].sudo()._handle_feedback_data('Hesabe_PG_MPGS_v15' , response)
        return werkzeug.utils.redirect('/payment/status')
    
    return_data_url = '/payment/hesabe'
    @http.route(
        return_data_url, type='http', auth="public", csrf=False, methods=['POST'], save_session=False )
    def hesabe_payment(self, **post):
        return werkzeug.utils.redirect(post.get('form_url'))