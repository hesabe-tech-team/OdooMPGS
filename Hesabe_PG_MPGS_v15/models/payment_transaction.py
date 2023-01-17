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
        if self.provider != 'Hesabe_PG_MPGS_v15':
            return res
        
        rendering_values = self.acquirer_id._get_hesabe_form_generate_values(
            self.acquirer_id,self.currency_id,self.partner_id,self.reference,self.provider,self.amount
        )
        return rendering_values
        
    
    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        transaction = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'Hesabe_PG_MPGS_v15':
            return transaction
            
        reference = data.get('response').get('orderReferenceNumber')
        transaction = self.search([('reference', '=', reference), ('provider', '=', 'Hesabe_PG_MPGS_v15')])
        if not transaction:
            error_msg = (_(
                'Hesabe %s: received data for reference %s; no order found') % (provider, reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
        
            error_msg = (_(
                'Hesabe %s: received data for reference %s; multiple orders found') % (provider, reference))
            raise ValidationError(error_msg)
        return transaction

    def _process_feedback_data(self, data):
        
        super()._process_feedback_data(data)
        if self.provider != 'Hesabe_PG_MPGS_v15':
            return    
        
        status = data.get('status')
        result = self.write({
            'acquirer_reference': data.get('response').get('paymentId'),
        })
        if status:
            self._set_done()
        else:
            self._set_canceled()
        return result