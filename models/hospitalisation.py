from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Hospitalisation(models.Model):
    _name = 'clinic.hospitalisation'
    _description = 'Dossier d’hospitalisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'entry_date desc'

    # One2one avec admission
    admission_id = fields.Many2one('clinic.admission', string='Admission', required=True, ondelete='cascade')
    patient_id = fields.Many2one('res.partner', related='admission_id.patient_id', store=True, readonly=True)
    service_id = fields.Many2one('clinic.service', related='admission_id.service_id', store=True, readonly=True)
    bed_id = fields.Many2one('clinic.bed', related='admission_id.bed_id', store=True, readonly=True)
    doctor_id = fields.Many2one('res.partner', related='admission_id.doctor_id', store=True, readonly=True)

    name = fields.Char(string='N° Séjour', readonly=True, copy=False)
    entry_date = fields.Datetime(default=fields.Datetime.now, required=True)
    exit_date = fields.Datetime()
    stay_days = fields.Integer(compute='_compute_stay', store=True)
    state = fields.Selection([
        ('admitted', 'Admis'),
        ('in_progress', 'En cours'),
        ('pre_discharge', 'Sortie prévue'),
        ('discharged', 'Sorti'),
        ('cancelled', 'Annulé')
    ], default='admitted', tracking=True)

    # nursing_plan_ids = fields.One2many('clinic.nursing.plan', 'hospitalisation_id', string='Plans de soins')
    # invoice_ids = fields.One2many('account.move', 'hospitalisation_id', string='Factures')
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    # --------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.hospitalisation') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('entry_date', 'exit_date')
    def _compute_stay(self):
        for rec in self:
            if rec.exit_date:
                delta = (rec.exit_date.date() - rec.entry_date.date()).days + 1
            else:
                delta = (fields.Date.today() - rec.entry_date.date()).days + 1
            rec.stay_days = max(delta, 0)

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    # ---------------- BUTTONS ----------------

    def action_plan_discharge(self):
        self.state = 'pre_discharge'

    def action_discharge(self):
        for h in self:
            if any(not h.exit_date for h in self):
                h.exit_date = fields.Datetime.now()
            h.admission_id.bed_id.action_free_bed()
            h.state = 'discharged'

    def action_view_invoices(self):
        return {
            'name': 'Factures séjour',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('hospitalisation_id', 'in', self.ids)],
        }

    def action_create_nursing_plan(self):
        self.ensure_one()
        plan = self.env['clinic.nursing.plan'].create({
            'hospitalisation_id': self.id,
        })
        return {
            'name': _('Plan de soins'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.nursing.plan',
            'view_mode': 'form',
            'res_id': plan.id,
            'target': 'current',
        }


class NursingPlan(models.Model):
    _name = 'clinic.nursing.plan'
    _description = 'Plan de soins infirmiers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Réf.', readonly=True, copy=False)
    hospitalisation_id = fields.Many2one('clinic.hospitalisation', required=True, ondelete='cascade')
    patient_id = fields.Many2one('res.partner', related='hospitalisation_id.patient_id', store=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    nurse_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    line_ids = fields.One2many('clinic.nursing.plan.line', 'plan_id', string='Lignes de soins')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('clinic.nursing.plan') or 'Nouveau'
        return super().create(vals_list)


class NursingPlanLine(models.Model):
    _name = 'clinic.nursing.plan.line'
    _description = 'Ligne de soin'

    plan_id = fields.Many2one('clinic.nursing.plan', required=True, ondelete='cascade')
    time_slot = fields.Selection([('morning', 'Matin'),
                                  ('noon', 'Midi'),
                                  ('evening', 'Soir'),
                                  ('night', 'Nuit')], required=True)
    product_id = fields.Many2one('product.product', domain=[('type', '=', 'product')], string='Produit / Soin')
    dose = fields.Float()
    dose_unit = fields.Char()
    done = fields.Boolean(default=False)
    done_time = fields.Datetime()