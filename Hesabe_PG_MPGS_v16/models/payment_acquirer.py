# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api, _
from werkzeug import urls
from odoo.addons.Hesabe_PG_MPGS_v16.models.hesabecrypt import encrypt, decrypt
from odoo.addons.Hesabe_PG_MPGS_v16.models.hesabeutil import checkout
from odoo.exceptions import ValidationError

class PaymentAcquirerHesabe(models.Model):
    _inherit = 'payment.provider'
    
    @api.model
    def default_get(self, fields):
        res=super(PaymentAcquirerHesabe, self).default_get(fields)
        return res
         
    code = fields.Selection(selection_add=[('Hesabe_PG_MPGS_v16', 'Hesabe MPGS')], ondelete={'Hesabe_PG_MPGS_v16': 'set default'})
    merchant_code = fields.Char(string="Merchant Code", help="This is Merchant Code", required_if_provider='Hesabe_PG_MPGS_v16')
    secret_key = fields.Char(string="Secret Key", help="This is Secret Key", required_if_provider='Hesabe_PG_MPGS_v16')
    access_code = fields.Char(string="Access Code", help="This is Access Code", required_if_provider='Hesabe_PG_MPGS_v16')
    iv_key = fields.Char(string="IV Key", help="This is IV Key", required_if_provider='Hesabe_PG_MPGS_v16')
    api_version = fields.Char(string="API Version", help="This is API Version", required_if_provider='Hesabe_PG_MPGS_v16', default='2.0')
    production_url = fields.Char(string="Production Url", help="This is Production Url", required_if_provider='Hesabe_PG_MPGS_v16')
    sandbox_url = fields.Char(string="Sandbox Url", help="This is Sandbox Url", required_if_provider='Hesabe_PG_MPGS_v16')
    
    
    def _get_hesabe_urls(self, environment):
        self.ensure_one()
        if environment == 'test':
            return {'hesabe_form_url': self.sandbox_url}
        elif environment == 'enabled':
            return {'hesabe_form_url': self.production_url}
        else:
            return {'hesabe_form_url': ''}
    
    def _get_hesabe_form_generate_values(self, acqid,currencyid,partnerid,referenceno,providr,amount):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        company = self.env['res.company'].search([('id', '=', self.env.company.id)], limit=1).sudo()
        
        payload = {
            "merchantCode": acqid.merchant_code,
            "currency": company.currency_id.name,
            "amount": amount,
            "responseUrl": urls.url_join(base_url, '/payment/hesabe/%s/return' % ('mpgs' if self.code == 'Hesabe_PG_MPGS_v16' else 'knet')),
            "paymentType": 2 if self.code == 'Hesabe_PG_MPGS_v16' else 1,
            "version": acqid.api_version,
            "orderReferenceNumber": referenceno,
            "failureUrl": urls.url_join(base_url, '/payment/hesabe/%s/fail' % ('mpgs' if self.code == 'Hesabe_PG_MPGS_v16' else 'knet')),
            # Add more variables here
            # "variable1": values['reference'],
            # Use to compare with response value amount
            "variable2": amount,
            # "variable3": values['reference'],
            # "variable4": values['reference'],
            # "variable5": values['reference'],
        }
        
        ComvertPayload = json.dumps(payload)
        parseComvertPayload = json.loads(ComvertPayload)
        url = self._get_hesabe_urls(self.state)['hesabe_form_url']
        
        if parseComvertPayload['currency'] != "KWD":
            raise ValidationError(_("Invalid currency: Selected currency("+ parseComvertPayload['currency'] +") Please change currency to Kuwaiti Dinar (KWD)"))
        else:
            encryptedText = encrypt(str(json.dumps(payload)), self.secret_key, self.iv_key)
            checkoutToken = checkout(encryptedText, url, self.access_code, 'production' if self.state == 'enabled' else 'test')
            try:
                result = decrypt(checkoutToken, self.secret_key, self.iv_key)
                try:
                    if '"status":false' in result:
                        raise ValidationError(
                            _("Service Unavailable: We are sorry the service is not available for this account. Please contact the business team for further information."))
                    response = json.loads(result)
                    decryptToken = response['response']['data']
                    if decryptToken != '':
                        url = urls.url_join(url, "/payment?data=%s" % (decryptToken))
                    else:
                        url = "/shop"
                except:
                    raise ValidationError(_("An exception occurred"))
                
                vals = {
                    'form_url': url
                }
                return vals
            except:
                if '"status":false' and '"code":501' in checkoutToken:
                    raise ValidationError(_("Invalid Merchant: This Merchant doesn't support this payment method! double check your Access key , secret key and IV Key"))
                elif '"status":false' and '"code":503' in checkoutToken:
                    raise ValidationError(_("Invalid Merchant Service"))
                elif '"status":false' and '"code":519' in checkoutToken:
                    raise ValidationError(_("Invalid currency, Please use the same currency which has been used while authorizing the transaction"))
                elif '"status":false' and '"code":422' in checkoutToken:
                    raise ValidationError(_("Invalid Input"))
                elif '"status":false' and '"code":0' in checkoutToken:
                    raise ValidationError(_("Invalid Response"))
                elif '"status":false' and '"code":500' in checkoutToken:
                    raise ValidationError(_("Invalid Token"))
                elif '"status":false' and '"code":504' in checkoutToken:
                    raise ValidationError(_("Invalid Merchant Login Credentials"))
                elif '"status":false' and '"code":505' in checkoutToken:
                    raise ValidationError(_("Invalid Payment Token"))
                elif '"status":false' and '"code":506' in checkoutToken:
                    raise ValidationError(_("Invalid Request Data"))
                elif '"status":false' and '"code":507' in checkoutToken:
                    raise ValidationError(_("Transaction Error"))
                else:
                    raise ValidationError(_("Something went Wrong Please make sure your input is correct"))
    