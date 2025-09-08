from odoo import models, fields, api, _


class Appointment(models.Model):
    _name = "clinic.appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rendez-vous"
    _order = "name,doctor_id"


    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('Nouveau'))
    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True)
    doctor_id = fields.Many2one('res.partner', string='Médecin', domain="[('doctor', '=', True)]")

    bon_id = fields.Many2one(
        comodel_name='clinic.cash_entry',
        string='N°BON', ondelete='restrict')

    date_rdv = fields.Datetime(string='Date et Heure du Rendez-vous', required=True, default=fields.Datetime.now)
    etat = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé')
    ], string='État', default='brouillon', tracking=True)

    etape_file = fields.Many2one(
        'clinic.queue_stage',
        string='Étape File d\'Attente',
        required=False,
        default=lambda self: self.env['clinic.queue_stage'].search([('sequence', '=', 1)], limit=1)

    )

    priorite = fields.Selection([
        ('normale', 'Normale'),
        ('urgente', 'Urgente')
    ], string='Priorité', default='normale')
    note = fields.Text(string='Observations')
    couleur = fields.Integer(string='Index Couleur', )

    room_id = fields.Many2one("clinic.consultation.room", string="Salle de Consultation", ondelete="restrict")

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or _('Nouveau')
        return super().create(vals)

    def action_create_encounter(self):
        self.ensure_one()
        
        encounter = self.env['clinic.encounter'].create({
            'patient_id': self.patient_id.id,
            'appointment_id': self.id,
            'room_id': self.room_id.id if self.room_id else False,  # Synchronisation de la salle
            'start': self.date_checkup,
            'type': 'ambu',
            'state': 'draft',
            'service_id': self.room_id.service_id.id if self.room_id else self.env['clinic.service'].search([], limit=1).id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.encounter',
            'res_id': encounter.id,
            'view_mode': 'form',
            'target': 'current',
        }
        
class QueueStage(models.Model):
    _name = 'clinic.queue_stage'
    _description = 'Étape File d\'Attente'
    _order = 'sequence'

    name = fields.Char(string='Nom Étape', required=True, translate=True)
    sequence = fields.Integer(string='Séquence', default=10)
    pliable = fields.Boolean(string='Pliable dans Kanban', default=False)
