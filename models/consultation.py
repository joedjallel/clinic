from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Encounter(models.Model):
    _name = "clinic.encounter"
    _description = "Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start desc"

    name = fields.Char("N° Consultation", readonly=True, copy=False, tracking=True)
    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True, tracking=True)
    doctor_id = fields.Many2one('res.partner', string='Médecin', domain="[('doctor', '=', True)]", required=True, tracking=True)
    admission_id = fields.Many2one("clinic.admission", string="Admission", tracking=True)
    service_id = fields.Many2one("clinic.service", string="Service", required=True, tracking=True)
    start = fields.Datetime(string="Début", default=fields.Datetime.now, tracking=True)
    end = fields.Datetime(string="Fin", tracking=True)
    type = fields.Selection([("ambu", "Ambulatoire"), ("inpatient", "Hospitalisé"), ("emergency", "Urgence")], string="Type", tracking=True)
    state = fields.Selection([("draft", "Brouillon"), ("in_progress", "En cours"), ("done", "Terminé")], string="État", default="draft", tracking=True)
    observations_ids = fields.One2many("clinic.observation", "encounter_id", string="Observations")
    prescriptions_ids = fields.One2many("clinic.prescription", "encounter_id", string="Ordonnances")
    appointment_id = fields.Many2one("clinic.appointment", string="Rendez-vous", ondelete="restrict")
    room_id = fields.Many2one("clinic.consultation.room", string="Salle de Consultation", required=True, ondelete="restrict")

    @api.constrains('room_id', 'start', 'end')
    def _check_room_availability(self):
        for encounter in self:
            if encounter.room_id and encounter.start:
                # Vérifier les conflits d'horaires
                conflicting_encounters = self.env['clinic.encounter'].search([
                    ('room_id', '=', encounter.room_id.id),
                    ('start', '<=', encounter.end or encounter.start),
                    ('end', '>=', encounter.start),
                    ('id', '!=', encounter.id),
                    ('state', 'in', ['draft', 'in_progress']),
                ])
                if conflicting_encounters:
                    raise ValidationError(_("La salle %s est déjà réservée pour une autre consultation à ce moment.") % encounter.room_id.name)

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("clinic.encounter")
        return super().create(vals)

class Observation(models.Model):
    _name = "clinic.observation"
    _description = "Observation clinique"

    encounter_id = fields.Many2one("clinic.encounter", string="Consultation", required=True, ondelete="cascade")
    code = fields.Char("LOINC", required=True)
    value_float = fields.Float(string="Valeur flottante")
    value_unit = fields.Char(string="Unité de valeur")
    value_str = fields.Char(string="Valeur de la chaîne")
    datetime = fields.Datetime(string="Date et heure", default=fields.Datetime.now)
    performer_id = fields.Many2one("res.users", string="Exécutant")
    is_abnormal = fields.Boolean(string="Est anormal")

class Prescription(models.Model):
    _name = "clinic.prescription"
    _description = "Ordonnance"

    name = fields.Char("N° ordonnance", readonly=True, copy=False)
    encounter_id = fields.Many2one("clinic.encounter", string="Consultation")
    patient_id = fields.Many2one("res.partner", string="Patient", related="encounter_id.patient_id", store=True)
    physician_id = fields.Many2one("res.users", string="Médecin", default=lambda self: self.env.user)
    datetime = fields.Datetime(string="Date et heure", default=fields.Datetime.now)
    lines_ids = fields.One2many("clinic.medication.line", "prescription_id", string="Lignes de médicaments")

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("clinic.prescription")
        return super().create(vals)

class MedicationLine(models.Model):
    _name = "clinic.medication.line"
    _description = "Ligne médicament"

    prescription_id = fields.Many2one("clinic.prescription", string="Ordonnance", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Produit", domain=[("type","=","product")], required=True)
    dose = fields.Float(string="Dose")
    dose_unit = fields.Char(string="Unité de dose")
    frequency = fields.Char(string="Fréquence")
    duration_days = fields.Integer(string="Jours de durée")
