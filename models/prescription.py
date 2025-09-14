from odoo import models, fields, api

class Prescription(models.Model):
    _name = 'clinic.prescription'
    _description = 'Prescription médicale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Référence', readonly=True, copy=False, default='/', tracking=True)
    encounter_id = fields.Many2one('clinic.encounter', string='Consultation', required=True, ondelete='cascade', tracking=True)
    patient_id = fields.Many2one(related='encounter_id.patient_id', string='Patient', store=True, readonly=True, tracking=True)
    doctor_id = fields.Many2one(related='encounter_id.doctor_id', string='Médecin', store=True, readonly=True, tracking=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True, tracking=True)
    description = fields.Text(string='Description', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validée'),
        ('delivered', 'Délivrée')
    ], string='État', default='draft', required=True, tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.prescription') or '/'
        return super(Prescription, self).create(vals_list)