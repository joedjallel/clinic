from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class Encounter(models.Model):
    _name = "clinic.encounter"
    _description = "Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start desc, name"
    _rec_name = 'display_name'

    # === CHAMPS DE BASE ===
    name = fields.Char(
        "N° Consultation",
        readonly=True,
        copy=False,
        tracking=True,
        index=True
    )

    display_name = fields.Char(
        string='Nom d\'affichage',
        compute='_compute_display_name',
        store=True
    )

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        domain="[('patient', '=', True)]",
        required=True,
        tracking=True,
        index=True
    )

    doctor_id = fields.Many2one(
        'res.partner',
        string='Médecin',
        domain="[('doctor', '=', True)]",
        required=True,
        tracking=True,
        index=True
    )

    # === CHAMPS RELATIONNELS ===
    appointment_id = fields.Many2one(
        "clinic.appointment",
        string="Rendez-vous",
        ondelete="restrict",
        tracking=True,
        index=True
    )

    admission_id = fields.Many2one(
        "clinic.admission",
        string="Admission",
        tracking=True,
        index=True
    )

    service_id = fields.Many2one(
        "clinic.service",
        string="Service",
        required=False,
        tracking=True,
        index=True
    )

    room_id = fields.Many2one(
        "clinic.consultation.room",
        string="Salle de Consultation",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True
    )

    # === CHAMPS TEMPORELS ===
    start = fields.Datetime(
        string="Début",
        default=fields.Datetime.now,
        tracking=True,
        required=True,
        index=True
    )

    end = fields.Datetime(
        string="Fin",
        tracking=True,
        index=True
    )

    duration = fields.Float(
        string="Durée (heures)",
        compute='_compute_duration',
        store=True,
        help="Durée réelle de la consultation"
    )

    planned_duration = fields.Float(
        string="Durée planifiée",
        related='appointment_id.duration',
        readonly=True
    )

    # === CHAMPS D'ÉTAT ===
    type = fields.Selection([
        ("ambu", "Ambulatoire"),
        ("inpatient", "Hospitalisé"),
        ("emergency", "Urgence")
    ], string="Type", tracking=True, default="ambu", required=True, index=True)

    state = fields.Selection([
        ("draft", "Brouillon"),
        ("in_progress", "En cours"),
        ("done", "Terminé"),
        ("cancelled", "Annulé")
    ], string="État", default="draft", tracking=True, required=True, index=True)

    # === CHAMPS MÉDICAUX ===
    chief_complaint = fields.Text(
        string="Motif de consultation",
        help="Raison principale de la visite"
    )

    diagnosis = fields.Text(
        string="Diagnostic",
        help="Diagnostic principal et différentiels"
    )

    treatment_plan = fields.Text(
        string="Plan de traitement",
        help="Plan thérapeutique recommandé"
    )

    follow_up = fields.Text(
        string="Suivi recommandé",
        help="Instructions de suivi pour le patient"
    )

    # === RELATIONS ONE2MANY ===
    observations_ids = fields.One2many(
        "clinic.observation",
        "encounter_id",
        string="Observations"
    )

    prescriptions_ids = fields.One2many(
        "clinic.prescription",
        "encounter_id",
        string="Ordonnances"
    )

    # === CHAMPS CALCULÉS ===
    observations_count = fields.Integer(
        string="Nombre d'observations",
        compute='_compute_counts'
    )

    prescriptions_count = fields.Integer(
        string="Nombre de prescriptions",
        compute='_compute_counts'
    )

    is_overdue = fields.Boolean(
        string="En retard",
        compute='_compute_is_overdue'
    )

    can_start = fields.Boolean(
        string="Peut démarrer",
        compute='_compute_can_start'
    )

    can_finish = fields.Boolean(
        string="Peut terminer",
        compute='_compute_can_finish'
    )

    # === CONSTRAINTES ===
    @api.constrains('room_id', 'start', 'end')
    def _check_room_availability(self):
        """Vérifier la disponibilité de la salle"""
        for encounter in self:
            if encounter.room_id and encounter.start and encounter.state != 'cancelled':
                end_time = encounter.end or encounter.start + timedelta(hours=1)

                # Rechercher les consultations en conflit
                conflicting_encounters = self.search([
                    ('room_id', '=', encounter.room_id.id),
                    ('start', '<', end_time),
                    ('end', '>', encounter.start) if encounter.end else ('start', '>',
                                                                         encounter.start - timedelta(hours=1)),
                    ('id', '!=', encounter.id),
                    ('state', 'in', ['draft', 'in_progress']),
                ])

                if conflicting_encounters:
                    raise ValidationError(
                        _("La salle %s est déjà réservée pour une autre consultation à ce moment. "
                          "Conflit avec: %s") % (
                            encounter.room_id.name,
                            ', '.join(conflicting_encounters.mapped('name'))
                        )
                    )

    @api.constrains('doctor_id', 'start', 'end')
    def _check_doctor_availability(self):
        """Vérifier la disponibilité du médecin"""
        for encounter in self:
            if encounter.doctor_id and encounter.start and encounter.state != 'cancelled':
                end_time = encounter.end or encounter.start + timedelta(hours=1)

                conflicting_encounters = self.search([
                    ('doctor_id', '=', encounter.doctor_id.id),
                    ('start', '<', end_time),
                    ('end', '>', encounter.start) if encounter.end else ('start', '>',
                                                                         encounter.start - timedelta(hours=1)),
                    ('id', '!=', encounter.id),
                    ('state', 'in', ['draft', 'in_progress']),
                ])

                if conflicting_encounters:
                    raise ValidationError(
                        _("Le médecin %s n'est pas disponible à ce moment. "
                          "Conflit avec: %s") % (
                            encounter.doctor_id.name,
                            ', '.join(conflicting_encounters.mapped('name'))
                        )
                    )

    @api.constrains('start', 'end')
    def _check_dates_consistency(self):
        """Vérifier la cohérence des dates"""
        for encounter in self:
            if encounter.end and encounter.start and encounter.end <= encounter.start:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début."))

            if encounter.start and encounter.start > fields.Datetime.now() + timedelta(days=1):
                raise ValidationError(_("La date de début ne peut pas être trop éloignée dans le futur."))

    # === MÉTHODES CALCULÉES ===
    @api.depends('name', 'patient_id', 'start')
    def _compute_display_name(self):
        for encounter in self:
            if encounter.patient_id and encounter.start:
                encounter.display_name = f"{encounter.name} - {encounter.patient_id.name} - {encounter.start.strftime('%d/%m/%Y %H:%M')}"
            else:
                encounter.display_name = encounter.name or _('Nouvelle consultation')

    @api.depends('start', 'end')
    def _compute_duration(self):
        for encounter in self:
            if encounter.start and encounter.end:
                delta = encounter.end - encounter.start
                encounter.duration = delta.total_seconds() / 3600.0  # Conversion en heures
            else:
                encounter.duration = 0.0

    @api.depends('observations_ids', 'prescriptions_ids')
    def _compute_counts(self):
        for encounter in self:
            encounter.observations_count = len(encounter.observations_ids)
            encounter.prescriptions_count = len(encounter.prescriptions_ids)

    @api.depends('start', 'planned_duration')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for encounter in self:
            if encounter.state == 'in_progress' and encounter.start and encounter.planned_duration:
                expected_end = encounter.start + timedelta(hours=encounter.planned_duration)
                encounter.is_overdue = now > expected_end
            else:
                encounter.is_overdue = False

    @api.depends('state', 'room_id', 'doctor_id')
    def _compute_can_start(self):
        for encounter in self:
            encounter.can_start = (
                    encounter.state == 'draft' and
                    encounter.room_id and
                    encounter.doctor_id
            )

    @api.depends('state', 'chief_complaint')
    def _compute_can_finish(self):
        for encounter in self:
            encounter.can_finish = (
                    encounter.state == 'in_progress' and
                    encounter.chief_complaint  # Au minimum le motif doit être renseigné
            )


    @api.model
    def create(self, vals):
        """Générer la séquence et logique de création"""
        if not vals.get('name'):
            vals["name"] = self.env["ir.sequence"].next_by_code("clinic.encounter") or _('Nouveau')

        encounter = super().create(vals)

        # Notifier le médecin assigné
        if encounter.doctor_id:
            encounter._notify_doctor_assignment()

        return encounter

    def write(self, vals):
        """Logique de modification"""
        # Empêcher la modification des consultations terminées
        if 'state' not in vals:
            terminated_encounters = self.filtered(lambda e: e.state == 'done')
            if terminated_encounters:
                protected_fields = {'patient_id', 'doctor_id', 'start', 'room_id'}
                if protected_fields.intersection(set(vals.keys())):
                    raise UserError(_("Impossible de modifier une consultation terminée."))

        result = super().write(vals)

        # Synchroniser avec l'appointment si état change
        if 'state' in vals:
            self._sync_with_appointment()

        return result

    # ------------------------------------------------------------------ #
    # 1)  Notifications et synchronisation                               #
    # ------------------------------------------------------------------ #
    def _notify_doctor_assignment(self):
        """
        Notifie le médecin qu'une consultation vient de lui être affectée.
        """
        for rec in self:
            if rec.doctor_id and rec.doctor_id.user_ids:
                rec.message_post(
                    body=_(f"Consultation <b>{rec.name}</b> assignée à <b>{rec.doctor_id.name}</b>."),
                    partner_ids=rec.doctor_id.user_ids.mapped('partner_id').ids,
                    subtype_xmlid='mail.mt_note',
                )

    def _sync_with_appointment(self):
        """
        Synchronise l'état de la consultation avec le rendez-vous lié :
        – passe l'appointment au statut « done » si la consultation est terminée.
        """
        for rec in self:
            if rec.appointment_id and rec.state == 'done':
                rec.appointment_id.etat = 'termine'

    def action_start(self):
        """
        Démarre la consultation : contrôle d'accès + changement d'état.
        """
        self.ensure_one()
        if not self.can_start:
            raise UserError(_("Impossible de démarrer la consultation."))

        self.write({'state': 'in_progress', 'start': fields.Datetime.now()})

    def action_done(self):
        """
        Clôture la consultation : oblige au minimum un motif et calcule l'heure de fin.
        """
        self.ensure_one()
        if not self.can_finish:
            raise UserError(_("Impossible de terminer : le motif de consultation est manquant."))

        self.write({'state': 'done', 'end': fields.Datetime.now()})
        self._sync_with_appointment()  # mise à jour éventuelle du RDV

    def action_cancel(self):
        """
        Annule la consultation (état annulé + remise à zéro des dates si besoin).
        """
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Une consultation terminée ne peut plus être annulée."))

        self.write({'state': 'cancelled', 'end': False})


    def unlink(self):
        """
        Empêche la suppression d'une consultation terminée ou en cours.
        """
        if any(rec.state in ('done', 'in_progress') for rec in self):
            raise UserError(_("Vous ne pouvez pas supprimer une consultation en cours ou terminée."))
        return super().unlink()

    def open_observations(self):
        """
        Retourne une action fenêtre pour afficher uniquement les observations
        liées à cette consultation.
        """
        self.ensure_one()
        return {
            'name': _('Observations'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.observation',
            'view_mode': 'tree,form',
            'domain': [('encounter_id', '=', self.id)],
            'context': {'default_encounter_id': self.id},
        }

    def open_prescriptions(self):
        """
        Retourne une action fenêtre pour afficher uniquement les ordonnances
        liées à cette consultation.
        """
        self.ensure_one()
        return {
            'name': _('Ordonnances'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.prescription',
            'view_mode': 'tree,form',
            'domain': [('encounter_id', '=', self.id)],
            'context': {'default_encounter_id': self.id},
        }

    def add_observation(self, code, value_float=None, value_unit=None,
                        value_str=None, performer=None, is_abnormal=False):
        """
        Crée une observation rapide reliée à la consultation.
        Retourne l'enregistrement créé.
        """
        self.ensure_one()
        return self.env['clinic.observation'].create({
            'encounter_id': self.id,
            'code': code,
            'value_float': value_float,
            'value_unit': value_unit,
            'value_str': value_str,
            'performer_id': performer or self.env.user.id,
            'is_abnormal': is_abnormal,
        })

    def add_prescription(self, lines_vals_list=None):
        """
        Crée une ordonnance rapide.
        `lines_vals_list` : liste de dictionnaires (product_id, dose, dose_unit, frequency, duration_days).
        Retourne l'ordonnance créée.
        """
        self.ensure_one()
        if not lines_vals_list:
            raise UserError(_("Aucun médicament fourni."))

        prescription = self.env['clinic.prescription'].create({
            'encounter_id': self.id,
            'physician_id': self.env.user.id,
        })
        for vals in lines_vals_list:
            vals['prescription_id'] = prescription.id
            self.env['clinic.medication.line'].create(vals)
        return prescription


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
