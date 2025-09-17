from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class Appointment(models.Model):
    _name = "clinic.appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rendez-vous"
    _order = "date_rdv desc, priorite desc, name"
    _rec_name = 'display_name'

    # === CHAMPS DE BASE ===
    name = fields.Char(string='Référence', required=True,copy=False, readonly=True,
        default=lambda self: _('Nouveau'),tracking=True )

    display_name = fields.Char(string='Nom d\'affichage',compute='_compute_display_name', store=True)

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
        tracking=True,
        index=True
    )

    date_rdv = fields.Datetime(string='Date et Heure du Rendez-vous',store=True,
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True
    )

    duration = fields.Float(
        string='Durée estimée (heures)',
        default=0.5,
        help="Durée estimée de la consultation"
    )

    date_rdv_end = fields.Datetime(
        string='Fin estimée',
        compute='_compute_date_rdv_end',
        store=True
    )

    # === CHAMPS D'ÉTAT ===
    etat = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('confirme', 'Confirmé'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé')
    ], string='État', default='brouillon', tracking=True, index=True)

    etape_file = fields.Many2one(
        'clinic.queue_stage',
        string='Étape File d\'Attente',
        required=False,
        store=True,
        default=lambda self: self._get_default_stage(),
        group_expand='_read_group_stage_ids',
        tracking=True,
        index=True
    )

    priorite = fields.Selection([
        ('normale', 'Normale'),
        ('urgente', 'Urgente')
    ], string='Priorité', default='normale', tracking=True, index=True)

    # === CHAMPS RELATIONNELS ===
    room_id = fields.Many2one(
        "clinic.consultation.room",
        string="Salle de Consultation",
        ondelete="restrict",
        tracking=True
    )

    service_id = fields.Many2one(
        'clinic.service',
        string='Service',
        related='room_id.service_id',
        store=True,
        readonly=True
    )

    encounter_id = fields.Many2one(
        'clinic.encounter',
        string='Consultation associée',
        readonly=True,
        ondelete='set null'
    )

    bon_id = fields.Many2one(
        comodel_name='clinic.cash_entry',
        string='N°BON',
        ondelete='restrict'
    )

    # === AUTRES CHAMPS ===
    note = fields.Text(string='Observations')
    couleur = fields.Integer(string='Index Couleur')

    # === CHAMPS CALCULÉS ===
    is_past_due = fields.Boolean(
        string='En retard',
        compute='_compute_is_past_due'
    )

    can_start_encounter = fields.Boolean(
        string='Peut démarrer consultation',
        compute='_compute_can_start_encounter'
    )

    @api.constrains('date_rdv', 'doctor_id', 'room_id')
    def _check_availability(self):
        """Vérifier la disponibilité du médecin et de la salle"""
        for appointment in self:
            if appointment.etat in ['annule']:
                continue

            # Vérifier les conflits de médecin
            if appointment.doctor_id:
                conflicting_doctor = self.search([
                    ('doctor_id', '=', appointment.doctor_id.id),
                    ('date_rdv', '<=', appointment.date_rdv_end),
                    ('date_rdv_end', '>=', appointment.date_rdv),
                    ('etat', 'not in', ['annule', 'termine']),
                    ('id', '!=', appointment.id)
                ], limit=1)

                if conflicting_doctor:
                    raise ValidationError(
                        _("Le médecin %s n'est pas disponible à ce créneau. "
                          "Conflit avec le RDV %s") % (
                            appointment.doctor_id.name,
                            conflicting_doctor.name
                        )
                    )

            # Vérifier les conflits de salle
            if appointment.room_id:
                conflicting_room = self.search([
                    ('room_id', '=', appointment.room_id.id),
                    ('date_rdv', '<=', appointment.date_rdv_end),
                    ('date_rdv_end', '>=', appointment.date_rdv),
                    ('etat', 'not in', ['annule', 'termine']),
                    ('id', '!=', appointment.id)
                ], limit=1)

                if conflicting_room:
                    raise ValidationError(
                        _("La salle %s n'est pas disponible à ce créneau. "
                          "Conflit avec le RDV %s") % (
                            appointment.room_id.name,
                            conflicting_room.name
                        )
                    )

    @api.constrains('date_rdv')
    def _check_date_rdv(self):
        """Vérifier que la date de RDV n'est pas dans le passé pour les nouveaux RDV"""
        for appointment in self:
            if appointment.etat == 'brouillon' and appointment.date_rdv < fields.Datetime.now():
                raise ValidationError(_("La date de rendez-vous ne peut pas être dans le passé."))

    # === CHAMPS CALCULÉS - MÉTHODES ===
    @api.depends('name', 'patient_id', 'date_rdv')
    def _compute_display_name(self):
        for appointment in self:
            if appointment.patient_id:
                appointment.display_name = f"{appointment.name} - {appointment.patient_id.name}"
            else:
                appointment.display_name = appointment.name or _('Nouveau')

    @api.depends('date_rdv', 'duration')
    def _compute_date_rdv_end(self):
        for appointment in self:
            if appointment.date_rdv and appointment.duration:
                appointment.date_rdv_end = appointment.date_rdv + timedelta(hours=appointment.duration)
            else:
                appointment.date_rdv_end = appointment.date_rdv

    @api.depends('date_rdv')
    def _compute_is_past_due(self):
        now = fields.Datetime.now()
        for appointment in self:
            appointment.is_past_due = (
                    appointment.date_rdv < now and
                    appointment.etat not in ['termine', 'annule']
            )

    @api.depends('etat', 'doctor_id', 'patient_id', 'room_id')
    def _compute_can_start_encounter(self):
        for appointment in self:
            appointment.can_start_encounter = (
                    appointment.etat == 'en_cours' and
                    appointment.doctor_id and
                    appointment.patient_id and
                    not appointment.encounter_id
            )

    def _get_default_stage(self):
        """Retourner l'étape par défaut"""
        return self.env['clinic.queue_stage'].search([('sequence', '=', 1)], limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Étendre les groupes pour afficher toutes les étapes"""
        return self.env['clinic.queue_stage'].search([], order=order)

    @api.model
    def create(self, vals):
        """Surcharger create pour générer la séquence"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('clinic.appointment') or _('Nouveau')

        # Auto-confirmation pour les urgences
        if vals.get('priorite') == 'urgente' and vals.get('etat') == 'brouillon':
            vals['etat'] = 'confirme'

        return super().create(vals)

    def write(self, vals):
        """Surcharger write pour la logique métier"""
        # Empêcher la modification des RDV terminés ou annulés
        if any(appointment.etat in ['termine', 'annule'] for appointment in self):
            protected_fields = {'patient_id', 'doctor_id', 'date_rdv', 'room_id'}
            if protected_fields.intersection(set(vals.keys())):
                raise UserError(_("Impossible de modifier un rendez-vous terminé ou annulé."))

        return super().write(vals)

    def action_confirmer(self):
        """Confirmer le rendez-vous"""
        self.ensure_one()
        if self.etat != 'brouillon':
            raise UserError(_("Seuls les rendez-vous en brouillon peuvent être confirmés."))

        self.write({
            'etat': 'confirme',
            'etape_file': self.env['clinic.queue_stage'].search([('sequence', '=', 1)], limit=1).id
        })

        # Envoyer notification (si module de notification disponible)
        self._send_confirmation_notification()

    def action_en_cours(self):
        """Passer le rendez-vous en cours"""
        self.ensure_one()
        if self.etat != 'confirme':
            raise UserError(_("Seuls les rendez-vous confirmés peuvent être mis en cours."))
        encounter_vals = {
            'patient_id': self.patient_id.id,
            'doctor_id': self.doctor_id.id,
            'appointment_id': self.id,
            'room_id': self.room_id.id if self.room_id else False,
            'start': self.date_rdv,
            'type': 'ambu',
            'state': 'draft',
        }

        encounter = self.env['clinic.encounter'].create(encounter_vals)

        # Mettre à jour l'appointment
        self.write({
            'encounter_id': encounter.id,
            'etape_file': self.env['clinic.queue_stage'].search([('sequence', '=', 2)], limit=1).id
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.encounter',
            'res_id': encounter.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_appointment_id': self.id}
        }

    def action_terminer(self):
        """Terminer le rendez-vous"""
        self.ensure_one()
        if self.etat == 'termine':
            return

        self.write({
            'etat': 'termine',
            'etape_file': self.env['clinic.queue_stage'].search([('sequence', '=', 3)], limit=1).id
        })

        # Terminer aussi la consultation si elle existe
        if self.encounter_id and self.encounter_id.state != 'done':
            self.encounter_id.write({
                'state': 'done',
                'end': fields.Datetime.now()
            })

    def action_annuler(self):
        """Annuler le rendez-vous"""
        self.ensure_one()
        if self.etat in ['termine', 'annule']:
            raise UserError(_("Impossible d'annuler un rendez-vous déjà terminé ou annulé."))

        self.write({'etat': 'annule'})

        # Annuler aussi la consultation si elle existe
        if self.encounter_id:
            self.encounter_id.unlink()

    def action_reprogrammer(self):
        """Reprogrammer le rendez-vous"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
                'default_priorite': self.priorite,
                'form_view_initial_mode': 'edit'
            }
        }

    # === MÉTHODES UTILITAIRES ===
    def _send_confirmation_notification(self):
        """Envoyer une notification de confirmation"""
        # Placeholder pour l'envoi de notifications
        # Peut être étendu avec un module de notification SMS/Email
        pass

    @api.model
    def _cron_check_past_due_appointments(self):
        """Cron pour identifier les rendez-vous en retard"""
        past_due_appointments = self.search([
            ('date_rdv', '<', fields.Datetime.now()),
            ('etat', 'in', ['confirme', 'en_cours'])
        ])

        for appointment in past_due_appointments:
            appointment.message_post(
                body=_("Ce rendez-vous est en retard."),
                message_type='notification'
            )

    @api.model
    def get_appointment_stats(self, date_from=None, date_to=None):
        """Retourner les statistiques des rendez-vous"""
        domain = []
        if date_from:
            domain.append(('date_rdv', '>=', date_from))
        if date_to:
            domain.append(('date_rdv', '<=', date_to))

        appointments = self.search(domain)

        stats = {
            'total': len(appointments),
            'by_state': {},
            'by_priority': {},
            'past_due': len(appointments.filtered('is_past_due'))
        }

        # Stats par état
        for state in ['brouillon', 'confirme', 'en_cours', 'termine', 'annule']:
            stats['by_state'][state] = len(appointments.filtered(lambda a: a.etat == state))

        # Stats par priorité
        for priority in ['normale', 'urgente']:
            stats['by_priority'][priority] = len(appointments.filtered(lambda a: a.priorite == priority))

        return stats

    def write(self, vals):
        """Surcharger write pour la logique métier"""
        # Empêcher la modification des RDV terminés ou annulés
        if any(appointment.etat in ['termine', 'annule'] for appointment in self):
            protected_fields = {'patient_id', 'doctor_id', 'date_rdv', 'room_id'}
            if protected_fields.intersection(set(vals.keys())):
                raise UserError(_("Impossible de modifier un rendez-vous terminé ou annulé."))

        result = super().write(vals)

        # Optional: trigger dashboard opening for doctors
        if vals.get('etape_file'):
            self._try_open_doctor_dashboard()

        return result

    def _try_open_doctor_dashboard(self):
        """Safely try to open doctor dashboard if encounter is started"""
        try:
            # Check if the required records exist
            stage_en_cours = self.env['clinic.queue_stage'].search([('sequence', '=', 2)], limit=1)
            encounter_manager_action = self.env.ref('clinic.encounter_manager', raise_if_not_found=False)

            if not stage_en_cours or not encounter_manager_action:
                return  # Skip if required records don't exist

            for appt in self:
                if (appt.etape_file == stage_en_cours and
                        appt.encounter_id and
                        appt.doctor_id and
                        appt.doctor_id.user_ids):
                    # Send notification to doctor
                    appt.env['bus.bus']._sendone(
                        appt.doctor_id.user_ids[0].partner_id,
                        'clinic_open_dashboard',
                        {
                            'action_id': encounter_manager_action.id,
                            'encounter_id': appt.encounter_id.id,
                            'message': f'Consultation {appt.encounter_id.name} prête'
                        }
                    )
        except Exception as e:
            # Log the error but don't break the appointment flow
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Could not open doctor dashboard: {e}")


class QueueStage(models.Model):
    _name = 'clinic.queue_stage'
    _description = 'Étape File d\'Attente'
    _order = 'sequence, id'

    name = fields.Char(string='Nom Étape',required=True,translate=True)

    sequence = fields.Integer(string='Séquence',default=10,help="Ordre d'affichage des étapes" )

    pliable = fields.Boolean(string='Pliable dans Kanban',default=False,
     help="Si coché, cette colonne peut être pliée dans la vue Kanban")

    color = fields.Integer(string='Couleur')

    active = fields.Boolean(default=True,help="Si décoché, l'étape ne sera plus visible")

    appointment_count = fields.Integer(
        string='Nombre de RDV',
        compute='_compute_appointment_count'
    )

    @api.depends()
    def _compute_appointment_count(self):
        for stage in self:
            stage.appointment_count = self.env['clinic.appointment'].search_count([
                ('etape_file', '=', stage.id)
            ])

    def get_appointments(self):
        return self.env['clinic.appointment'].search([
            ('etape_file', '=', self.id)
        ])
