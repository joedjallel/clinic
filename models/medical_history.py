from odoo import models, fields, api, _

class MedicalHistory(models.Model):
    _name = 'clinic.medical_history'
    _description = 'Antécédent Médical'
    _order = 'date desc'

    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True, ondelete='cascade')
    history_type = fields.Selection([
        ('allergy', 'Allergie'),
        ('chronic', 'Maladie chronique'),
        ('surgery', 'Chirurgie'),
        ('hospitalization', 'Hospitalisation'),
        ('family', 'Antécédent familial'),
        ('other', 'Autre'),
    ], string='Type d\'antécédent', required=True)
    description = fields.Text(string='Description', required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    doctor_id = fields.Many2one('res.partner', string='Médecin', domain="[('doctor', '=', True)]")
    notes = fields.Text(string='Notes complémentaires')

    _sql_constraints = [
        ('patient_date_unique', 'UNIQUE(patient_id, date, history_type, description)', 'Un antécédent médical doit être unique par patient, date, type et description !'),
    ]