from odoo import models, fields, api, _

class Act(models.Model):
    _inherit = 'product.product'
    _description = 'Acte Médical'


    code = fields.Char(string='Code', required=False, help="Code unique de l'acte médical")
    is_medical_act = fields.Boolean(string='Est un acte médical', default=False, help="Indique si le produit est un acte médical")

    @api.model
    def create(self, vals):
        if vals.get('is_medical_act', True):
            vals['type'] = 'service'
            vals['invoice_policy'] = 'order'
            if not vals.get('code'):
                code =self.env['ir.sequence'].next_by_code('clinic.act') or _('ACT000')
                vals['default_code'] = code
                vals['code'] = code
        return super(Act, self).create(vals)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code, company_id)', 'Le code de l\'acte doit être unique par compagnie !'),
    ]