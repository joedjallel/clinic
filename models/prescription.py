from odoo import models, fields, api

class Prescription(models.Model):
    _name = "clinic.prescription"
    _description = "Ordonnance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'datetime desc'

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
