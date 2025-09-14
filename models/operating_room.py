# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError


class OperatingRoom(models.Model):
    _name = 'clinic.operating.room'
    _description = 'Salle opératoire'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    service_id = fields.Many2one('clinic.service', required=True)
    state = fields.Selection([('free', 'Libre'), ('busy', 'Occupée'), ('blocked', 'Bloquée')], default='free')
    note = fields.Text()

    _sql_constraints = [('uniq_code', 'unique(code)', 'Code salle unique')]


class Operation(models.Model):
    _name = 'clinic.operation'
    _description = 'Intervention programmée'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(readonly=True, copy=False)
    patient_id = fields.Many2one('res.partner', domain=[('patient', '=', True)], required=True, ondelete='cascade')
    room_id = fields.Many2one('clinic.operating.room', required=True, ondelete='restrict')
    start_datetime = fields.Datetime(required=True, tracking=True)
    duration_minutes = fields.Integer(string='Durée prévue (min)', default=60)
    stop_datetime = fields.Datetime(compute='_compute_stop', store=True)
    intervention_id = fields.Many2one('product.product', domain=[('is_medical_act', '=', True)], string='Acte chirurgical')
    surgeon_id = fields.Many2one('res.partner', domain=[('doctor', '=', True)], string='Chirurgien')
    anesthetist_id = fields.Many2one('res.partner', domain=[('doctor', '=', True)], string='Anesthésiste')
    nurse_ids = fields.Many2many('res.users', string='Infirmiers')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmée'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée'),
        ('cancel', 'Annulée')
    ], default='draft', tracking=True)
    report = fields.Html(string='Compte-rendu opératoire')

    # --------------------------------------------------
    @api.depends('start_datetime', 'duration_minutes')
    def _compute_stop(self):
        for rec in self:
            rec.stop_datetime = rec.start_datetime + timedelta(minutes=rec.duration_minutes or 60)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.operation') or 'Nouveau'
        return super().create(vals_list)

    @api.constrains('room_id', 'start_datetime', 'duration_minutes')
    def _check_room_overlap(self):
        for op in self:
            if op.state != 'cancel':
                others = self.search([
                    ('id', '!=', op.id),
                    ('room_id', '=', op.room_id.id),
                    ('state', 'in', ['scheduled', 'in_progress']),
                    ('start_datetime', '<', op.stop_datetime),
                    ('stop_datetime', '>', op.start_datetime),
                ])
                if others:
                    raise UserError(_("La salle est déjà occupée à ce créneau."))

    # ---------------- BUTTONS ----------------
    def action_confirm(self):
        self.write({'state': 'scheduled'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

class KpiOROccupation(models.Model):
    _name = 'clinic.kpi.or.occupation'
    _description = 'KPI Occupation salles OR'
    _auto = False  # pas de table créée, on lit la vue
    _rec_name = 'room_id'

    room_id = fields.Many2one('clinic.operating.room', readonly=True)
    day = fields.Date(readonly=True)
    total_scheduled = fields.Integer(readonly=True)
    total_cancelled = fields.Integer(readonly=True)
    occupation_rate_percent = fields.Float(readonly=True, digits=(5, 2))

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW clinic_kpi_or_occupation AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    room_id,
                    date_trunc('day', start_datetime) AS day,
                    COUNT(*) FILTER (WHERE state != 'cancel') AS total_scheduled,
                    COUNT(*) FILTER (WHERE state = 'cancel') AS total_cancelled,
                    ROUND(
                        SUM(duration_minutes) FILTER (WHERE state != 'cancel') * 100.0 / (24 * 60),
                        2
                    ) AS occupation_rate_percent
                FROM clinic_operation
                GROUP BY room_id, day
            )
        """)