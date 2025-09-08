from odoo import fields, models


class Service(models.Model):
    _name = "clinic.service"
    _parent_name = "parent_id"
    _description = "Service / Unité fonctionnelle"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    parent_id = fields.Many2one("clinic.service", ondelete="cascade")
    specialty = fields.Char()
    bed_count = fields.Integer()
    active = fields.Boolean(default=True)


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
    # service_id = fields.Many2one("clinic.service", related="ward_id.service_id", store=True)

    service_id = fields.Many2one("clinic.service", string="Service", required=True)

    state = fields.Selection([("free", "Libre"), ("occupied", "Occupé"), ("maintenance", "Maintenance")],
                             default="free")
    gender_policy = fields.Selection([("male", "Homme"), ("female", "Femme"), ])


class ConsultationRoom(models.Model):
    _name = "clinic.consultation.room"
    _description = "Salle de Consultation"

    name = fields.Char(string="Nom de la Salle", required=True)
    code = fields.Char(string="Code", required=True)
    service_id = fields.Many2one("clinic.service", string="Service", required=True)
    active = fields.Boolean(string="Actif", default=True)
    capacity = fields.Integer(string="Capacité", default=1, help="Nombre de consultations simultanées possibles")
    description = fields.Text(string="Description")