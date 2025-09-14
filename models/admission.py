from odoo import api, fields, models

class Admission(models.Model):
    _name = "clinic.admission"
    _description = "Séjour / Admission"

    name = fields.Char("N° Admission", readonly=True, copy=False)
    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True)
    act_id = fields.Many2one('product.product', string='Acte Médical',
                             domain="[('is_medical_act', '=', True)]", required=True)

    speciality_id_dec = fields.Many2one(string='Spécialité', related='act_id.categ_id')

    service_id = fields.Many2one("clinic.service", required=True)
    # ward_id = fields.Many2one("clinic.ward")
    bed_id = fields.Many2one("clinic.bed", )
    admit_datetime = fields.Datetime(string="Date d'admission",required=True, default=fields.Datetime.now)
    discharge_planned = fields.Datetime(string="Sortie prévue")
    discharge_datetime = fields.Datetime(string="Date Sortie",)
    state = fields.Selection([
        ("pre_admit", "Pré-admission"),
        ("admitted", "Admis"),
        ("transferred", "Transféré"),
        ("discharged", "Sorti"),
    ], default="pre_admit")
    observation = fields.Text('Observation')

    moves_ids = fields.One2many("clinic.admission.move", "admission_id", string="Mouvements")

    doctor_id = fields.Many2one('res.partner', domain=[('doctor', '=', True)],
                                string='Médecin responsable')
    hospitalisation_id = fields.Many2one('clinic.hospitalisation',
                                         string='Dossier hospitalisation')
    daily_rate = fields.Monetary(string='Forfait journalier lit')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    def action_confirm_admission(self):
        self.bed_id.action_assign_patient(self.patient_id)
        if not self.hospitalisation_id:
            hosp = self.env['clinic.hospitalisation'].create({
                'patient_id': self.patient_id.id,
                'admission_id': self.id,
                'service_id': self.service_id.id,
            })
            self.hospitalisation_id = hosp.id
        self.state = 'admitted'


    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("clinic.admission")
        return super().create(vals)

class AdmissionMove(models.Model):
    _name = "clinic.admission.move"
    _description = "Transfert de lit"

    admission_id = fields.Many2one("clinic.admission", string="Admission", required=True)
    from_bed_id = fields.Many2one("clinic.bed", string="Depuis le lit")
    to_bed_id = fields.Many2one("clinic.bed", string="Vers le lit", required=True)
    datetime = fields.Datetime(string="Date et heure", required=True, default=fields.Datetime.now)
    reason = fields.Char(string="Raison")
    user_id = fields.Many2one("res.users", string="Utilisateur", default=lambda self: self.env.user)