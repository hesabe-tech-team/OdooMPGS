# -*- coding: utf-8 -*-

import json
import werkzeug

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
import PyPDF2
from odoo.addons.Hesabe_PG_MPGS_v16.models.hesabecrypt import decrypt

class HesabeController(http.Controller):
    
    @http.route(['/payment/hesabe/mpgs/return',
                 '/payment/hesabe/mpgs/fail'], type='http', auth='public', csrf=False, methods=['GET'], save_session=False
    )
    def hesabe_mpgs_return(self, **post):
        hesabe = request.env['payment.provider'].sudo().search([('code', '=', 'Payment_hesabe')], limit=1)
        data = decrypt(post['data'], hesabe.secret_key, hesabe.iv_key)
        response = json.loads(data)
        if post:
            getTrans=request.env['payment.transaction'].sudo()._get_tx_from_notification_data('Hesabe_PG_MPGS_v16', response)
            getTrans._handle_notification_data('Hesabe_PG_MPGS_v16', response)
        return werkzeug.utils.redirect('/payment/status')
    
    return_data_url = '/payment/hesabe'
    @http.route(
        return_data_url, type='http', auth="public", csrf=False, methods=['POST'], save_session=False )
    def hesabe_payment(self, **post):
        return werkzeug.utils.redirect(post.get('form_url'))