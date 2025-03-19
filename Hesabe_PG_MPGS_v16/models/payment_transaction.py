# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_compare

class PaymentTransactionHesabe(models.Model):
    _inherit = 'payment.transaction'
    
    def _get_specific_rendering_values(self, processing_values):
       
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'Hesabe_PG_MPGS_v16':
            return res
        
        rendering_values = self.provider_id._get_hesabe_form_generate_values(
            self.provider_id,self.currency_id,self.partner_id,self.reference,self.provider_code,self.amount
        )
        return rendering_values
        
        
    @api.model
    def _get_tx_from_notification_data(self, provider_code, data):
        
        transaction = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'Hesabe_PG_MPGS_v16' or len(transaction) == 1:
            return transaction
            
        reference = data.get('response').get('orderReferenceNumber')
        transaction = self.search([('reference', '=', reference), ('provider_code', '=', 'Hesabe_PG_MPGS_v16')])
        if not transaction:
            error_msg = (_(
                'Hesabe %s: received data for reference %s; no order found') % (provider, reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_(
                'Hesabe %s: received data for reference %s; multiple orders found') % (provider, reference))
            raise ValidationError(error_msg)
        return transaction
        
    def _process_notification_data(self, data):
        
        super()._process_notification_data(data)
        if self.provider_code != 'Hesabe_PG_MPGS_v16':
            return    
        
        status = data.get('status')
        result = self.write({
            'provider_reference': data.get('response').get('paymentId'),
            
        })
        if status:
            self._set_done()
        else:
            self._set_canceled()
        return result