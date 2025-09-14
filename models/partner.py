from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Personne'

    @api.depends('date_of_birth')
    def onchange_age(self):
        for rec in self:
            if rec.date_of_birth:
                d1 = rec.date_of_birth
                d2 = datetime.today().date()
                rd = relativedelta(d2, d1)
                rec.age = str(rd.years) + "A" + " " + str(rd.months) + "m" + " " + str(rd.days) + "j"
            else:
                rec.age = "No Date Of Birth!!"


    patient = fields.Boolean(string='Est patient', default=False, help="Indique si la personne est un patient")
    doctor = fields.Boolean(string='Est médecin', default=False, help="Indique si la personne est un médecin")
    patient_sequance = fields.Char(string='Identifiant', copy=False, readonly=True, help="Identifiant unique pour les patients ou médecins")

    maiden_name = fields.Char(string='Nom de jeune fille', store=True)
    date_of_birth = fields.Date(string="Date de naissance")
    place_of_birth = fields.Char(string='Lieu de naissance', store=True)
    Nationality = fields.Char(string='Nationalité', store=True)
    num_carte_chifa = fields.Char(string='N°Carte CHIFA', store=True)
    age = fields.Char(compute=onchange_age, string="Patient Age", store=False)

    situation = fields.Selection([
        ('Célibataire', 'Célibataire'),
        ('Marié(e)', 'Marié(e)'),
        ('Divorcé(e)', 'Divorcé(e)'),
        ('Veuf(ve)', 'Veuf(ve)')], string='Situation Familiale', )
    Conjoint = fields.Char(string='Conjoint', required=False, )


    convention_id = fields.Many2one('clinic.convention', string='Convention', help="Convention associée au patient")
    end_date = fields.Date(string='Date de fin de convention', help="Date de fin de validité de la convention")
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='État Convention', default='active', help="État de la convention ou du profil")

    total_rest = fields.Monetary(string='Reste à payer', compute='_compute_total_rest', store=True, help="Montant total restant à payer pour le patient")


    speciality = fields.Char(string='Spécialité', store=True)
    percentage_cote_part = fields.Float(string='% Cote part', default=0.0, help="Pourcentage de cote part pour les médecins")
    total_cote_part = fields.Monetary(string='Total cote part', compute='_compute_cote', store=True, help="Total des cotes parts dues au médecin")
    total_cote_recue = fields.Monetary(string='Cote part reçue', compute='_compute_cote', store=True, help="Total des cotes parts reçues")
    total_cote_rest = fields.Monetary(string='Cote part restante', compute='_compute_cote', store=True, help="Cote part restante à payer au médecin")


    transactions_cash = fields.One2many('clinic.cash_entry.line', 'doctor_id_dec', string='Transactions cote part')
    received_cash = fields.One2many('clinic.cash_exit', 'partner_id', string='Décaissements reçus')
    transactions_cash_patient = fields.One2many('clinic.cash_entry', 'patient_id', string='Encaissements patient')
    medical_history_ids = fields.One2many('clinic.medical_history', 'patient_id', string='Antécédent Médical')

    @api.constrains('patient', 'doctor')
    def _check_role_exclusivity(self):
        for record in self:
            if record.patient and record.doctor:
                raise ValidationError(_("Une personne ne peut pas être à la fois patient et médecin."))

    @api.depends('transactions_cash_patient', 'transactions_cash_patient.amount_total')
    def _compute_total_rest(self):
        for record in self:
            if record.patient:
                entries = self.env['clinic.cash_entry'].search([('patient_id', '=', record.id)])
                total_residual = sum(entry.amount_residual for entry in entries)
                payed_lefts = sum(entry.amount_payed for entry in entries if entry.rest and not entry.supplement)
                payed_supplements = sum(
                    entry.amount_payed - (entry.montant + entry.tax_amount)
                    for entry in entries if entry.rest and entry.supplement
                )
                record.total_rest = total_residual - payed_lefts - payed_supplements
            else:
                record.total_rest = 0.0

    @api.depends('transactions_cash', 'percentage_cote_part', 'received_cash')
    def _compute_cote(self):
        for record in self:
            if record.doctor:
                record.total_cote_part = sum(line.cote_part for line in record.transactions_cash)
                total_cote_recue = sum(line.montant for line in record.received_cash if line.motif == 'Cote part')
                record.total_cote_recue = total_cote_recue
                record.total_cote_rest = record.total_cote_part - total_cote_recue
            else:
                record.total_cote_part = 0.0
                record.total_cote_recue = 0.0
                record.total_cote_rest = 0.0

    _sql_constraints = [
        ('patient_sequance_unique', 'UNIQUE(patient_sequance, company_id)', 'L\'identifiant doit être unique par compagnie !'),
    ]