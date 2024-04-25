# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api, _ # type: ignore
from werkzeug import urls
from odoo.addons.Hesabe_PG_MPGS_v15.models.hesabecrypt import encrypt, decrypt # type: ignore
from odoo.addons.Hesabe_PG_MPGS_v15.models.hesabeutil import checkout # type: ignore
from odoo.exceptions import ValidationError # type: ignore

class PaymentAcquirerHesabe(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def default_get(self, fields):
        res=super(PaymentAcquirerHesabe, self).default_get(fields)
        return res
         
    provider = fields.Selection(selection_add=[('Hesabe_PG_MPGS_v15', 'Hesabe MPGS')], ondelete={'Hesabe_PG_MPGS_v15': 'set default'})
    merchant_code = fields.Char(string="Merchant Code", help="This is Merchant Code", required_if_provider='Hesabe_PG_MPGS_v15')
    secret_key = fields.Char(string="Secret Key", help="This is Secret Key", required_if_provider='Hesabe_PG_MPGS_v15')
    access_code = fields.Char(string="Access Code", help="This is Access Code", required_if_provider='Hesabe_PG_MPGS_v15')
    iv_key = fields.Char(string="IV Key", help="This is IV Key", required_if_provider='Hesabe_PG_MPGS_v15')
    api_version = fields.Char(string="API Version", help="This is API Version", required_if_provider='Hesabe_PG_MPGS_v15', default='2.0')
    production_url = fields.Char(string="Production Url", help="This is Production Url", required_if_provider='Hesabe_PG_MPGS_v15')
    sandbox_url = fields.Char(string="Sandbox Url", help="This is Sandbox Url", required_if_provider='Hesabe_PG_MPGS_v15')
    
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
        
        order = self.env['sale.order'].browse(partnerid)
        current_user =  order.partner_id
        name = current_user.name
        email = current_user.email
        mobile = current_user.phone

        payload = {
            "merchantCode": acqid.merchant_code,
            "currency": company.currency_id.name,
            "amount": amount,
            "responseUrl": urls.url_join(base_url, '/payment/hesabe/%s/return' % ('mpgs' if self.provider == 'Hesabe_PG_MPGS_v15' else 'knet')),
            "paymentType": 2 if self.provider == 'Hesabe_PG_MPGS_v15' else 1,
            "version": acqid.api_version,
            "orderReferenceNumber": referenceno,
            "failureUrl": urls.url_join(base_url, '/payment/hesabe/%s/fail' % ('mpgs' if self.provider == 'Hesabe_PG_MPGS_v15' else 'knet')),
            # Add more variables here
            # "variable1": values['reference'],
            # Use to compare with response value amount
            "variable2": amount,
            # "variable3": values['reference'],
            # "variable4": values['reference'],
            # "variable5": values['reference'],
            "name" : name,
            "mobile_number"  : mobile,
            "email" : email
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
    
    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'Hesabe_PG_MPGS_v15':
          return super()._get_default_payment_method_id()
        return self.env.ref('Hesabe_PG_MPGS_v15.payment_method_Hesabe_PG_MPGS_v15').id