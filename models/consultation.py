from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Encounter(models.Model):
    _name = "clinic.encounter"
    _description = "Consultation"
    _order = "start desc"

    name = fields.Char("N° Consultation", readonly=True, copy=False)
    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True)
    admission_id = fields.Many2one("clinic.admission")
    service_id = fields.Many2one("clinic.service", required=True)
    start = fields.Datetime(default=fields.Datetime.now)
    end = fields.Datetime()
    type = fields.Selection([("ambu", "Ambulatoire"), ("inpatient", "Hospitalisé"), ("emergency", "Urgence")])
    state = fields.Selection([("draft", "Brouillon"), ("in_progress", "En cours"), ("done", "Terminé")], default="draft")
    observations_ids = fields.One2many("clinic.observation", "encounter_id")
    prescriptions_ids = fields.One2many("clinic.prescription", "encounter_id")
    appointment_id = fields.Many2one("gestion__clinique.appointment", string="Rendez-vous", ondelete="restrict")
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

    encounter_id = fields.Many2one("clinic.encounter", required=True, ondelete="cascade")
    code = fields.Char("LOINC", required=True)
    value_float = fields.Float()
    value_unit = fields.Char()
    value_str = fields.Char()
    datetime = fields.Datetime(default=fields.Datetime.now)
    performer_id = fields.Many2one("res.users")
    is_abnormal = fields.Boolean()

class Prescription(models.Model):
    _name = "clinic.prescription"
    _description = "Ordonnance"

    name = fields.Char("N° ordonnance", readonly=True, copy=False)
    encounter_id = fields.Many2one("clinic.encounter")
    patient_id = fields.Many2one("res.partner", related="encounter_id.patient_id", store=True)
    physician_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    datetime = fields.Datetime(default=fields.Datetime.now)
    lines_ids = fields.One2many("clinic.medication.line", "prescription_id")

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("clinic.prescription")
        return super().create(vals)

class MedicationLine(models.Model):
    _name = "clinic.medication.line"
    _description = "Ligne médicament"

    prescription_id = fields.Many2one("clinic.prescription", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", domain=[("type","=","product")], required=True)
    dose = fields.Float()
    dose_unit = fields.Char()
    frequency = fields.Char()
    duration_days = fields.Integer()
