from odoo import fields, models,api
from odoo.exceptions import UserError


class Service(models.Model):
    _name = "clinic.service"
    _parent_name = "parent_id"
    _description = "Service / Unité fonctionnelle"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True)
    parent_id = fields.Many2one("clinic.service", string="Parent", ondelete="cascade")
    specialty = fields.Char(string="Spécialité")
    bed_count = fields.Integer(string="Nombre de lits")
    active = fields.Boolean(string="Actif", default=True)


# class Ward(models.Model):
#     _name = "clinic.ward"
#     _description = "Service / Unité fonctionnelle"
#
#     name = fields.Char(required=True)
#     code = fields.Char(required=False)
#     service_id = fields.Many2one("clinic.service", string="Service", required=True)
#     bed_count = fields.Integer()
#     active = fields.Boolean(default=True)
#

class Bed(models.Model):
    _name = "clinic.bed"
    _description = "Lit / place"

    name = fields.Char("Label", required=True)
    # ward_id = fields.Many2one("clinic.ward", ondelete="cascade")

    service_id = fields.Many2one("clinic.service", string="Service", required=True)

    state = fields.Selection([("free", "Libre"), ("occupied", "Occupé"), ("maintenance", "Maintenance")],
                             string="État", default="free")
    gender_policy = fields.Selection([("male", "Homme"), ("female", "Femme"), ], string="Politique de genre")

    _sql_constraints = [('uniq_code_service', 'unique(code, service_id)',
                         'Code lit doit être unique par service')]

    room = fields.Char('Chambre')
    floor = fields.Char('Étage')

    current_patient_id = fields.Many2one('res.partner', string='Patient actuel',
                                         domain=[('patient', '=', True)])
    occupation_history_ids = fields.One2many('clinic.bed.occupation', 'bed_id',
                                             string='Historique occupation')

    def action_assign_patient(self, patient_id):
        self.ensure_one()
        if self.state != 'free':
            raise UserError('Lit non disponible')
        self.write({'state': 'occupied', 'current_patient_id': patient_id.id})
        self.env['clinic.bed.occupation'].create({
            'bed_id': self.id,
            'patient_id': patient_id.id,
            'start_date': fields.Datetime.now(),
        })

    def action_free_bed(self):
        self.ensure_one()
        last_occ = self.env['clinic.bed.occupation'].search([
            ('bed_id', '=', self.id), ('end_date', '=', False)], limit=1)
        if last_occ:
            last_occ.end_date = fields.Datetime.now()
        self.write({'state': 'maintenance', 'current_patient_id': False})

class BedOccupation(models.Model):
    _name = 'clinic.bed.occupation'
    _description = 'Historique occupation lit'
    _order = 'start_date desc'

    bed_id = fields.Many2one('clinic.bed', required=True, ondelete='cascade')
    patient_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    start_date = fields.Datetime(default=fields.Datetime.now)
    end_date = fields.Datetime()
    duration_days = fields.Float(compute='_compute_duration', store=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.end_date:
                rec.duration_days = (rec.end_date - rec.start_date).days + 1
            else:
                rec.duration_days = 0

class ConsultationRoom(models.Model):
    _name = "clinic.consultation.room"
    _description = "Salle de Consultation"

    name = fields.Char(string="Nom de la Salle", required=True)
    code = fields.Char(string="Code", required=True)
    service_id = fields.Many2one("clinic.service", string="Service", required=True)
    active = fields.Boolean(string="Actif", default=True)
    capacity = fields.Integer(string="Capacité", default=1, help="Nombre de consultations simultanées possibles")
    description = fields.Text(string="Description")