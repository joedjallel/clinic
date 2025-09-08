from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CashStatement(models.Model):
    _name = 'clinic.cash_statement'
    _description = 'Relevé de Caisse'
    _inherit = ['mail.thread']
    _order = 'date desc'

    @api.depends('date')
    def _get_previous_statement(self):
        for st in self:
            # Search for the previous statement
            domain = [('date', '<=', st.date)]
            if not isinstance(st.id, models.NewId):
                domain.extend(['|', '&', ('id', '<', st.id), ('date', '=', st.date), '&', ('id', '!=', st.id),
                               ('date', '!=', st.date)])
            previous_statement = self.search(domain, limit=1, order='id desc')
            st.previous_statement_id = previous_statement.id
            previous_statement.write({'state': 'closed', 'date_done': fields.Datetime.now()})

    @api.depends('previous_statement_id', )
    def _compute_starting_balance(self):
        for statement in self:
            if statement.previous_statement_id:
                if statement.previous_statement_id.balance != statement.balance_start:
                   statement.balance_start = statement.previous_statement_id.balance
                else:
                    # Need default value
                    statement.balance_start = statement.balance_start or 0.0

    name = fields.Char(string='Référence', readonly=True, default=lambda self: _('Nouveau'))
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'Ouvert'),
        ('closed', 'Clôturé'),
    ], string='État', default='draft', required=True)

    balance_start = fields.Monetary(string='Solde Initiale', compute='_compute_starting_balance', readonly=False,
                                    store=True)

    previous_statement_id = fields.Many2one('clinic.statement',
                                            help='technical field to compute starting balance correctly',
                                            compute='_get_previous_statement', store=True)

    cash_entry_ids = fields.One2many('clinic.cash_entry', 'statement_id', string='Encaissements')
    cash_exit_ids = fields.One2many('clinic.cash_exit', 'statement_id', string='Décaissements')
    total_cash_entry = fields.Monetary(string='Total Encaissements', compute='_compute_totals', store=True)
    total_cash_exit = fields.Monetary(string='Total Décaissements', compute='_compute_totals', store=True)
    balance = fields.Monetary(string='Solde', compute='_compute_totals', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    date_done = fields.Datetime(string="Closed On")

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('clinic.cash_statement') or _('Nouveau')
        return super(CashStatement, self).create(vals)


    @api.depends('cash_entry_ids.amount_total', 'cash_exit_ids.montant')
    def _compute_totals(self):
        for record in self:
            record.total_cash_entry = sum(entry.amount_total for entry in record.cash_entry_ids)
            record.total_cash_exit = sum(exit.montant for exit in record.cash_exit_ids)
            differance = record.total_cash_entry - record.total_cash_exit
            record.balance = record.balance_start + differance

    def action_open(self):
        self.ensure_one()
        self.state = 'open'

    def action_close(self):
        self.ensure_one()
        self.state = 'closed'



class CashEntry(models.Model):
    _name = 'clinic.cash_entry'
    _description = 'Encaissement'
    _inherit = ['mail.thread']
    _order = 'date,id desc'

    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    n_bon = fields.Char(string='Numéro de bon', readonly=True, default=lambda self: _('Nouveau'))
    patient_id = fields.Many2one('res.partner', string='Patient', domain="[('patient', '=', True)]", required=True)
    doctor_id = fields.Many2one('res.partner', string='Médecin', domain="[('doctor', '=', True)]")
    statement_id = fields.Many2one('clinic.cash_statement', string='Relevé de Caisse', required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    paid_by = fields.Selection([
        ('lui-même ', 'lui-même '),
        ('Conjoint', 'Conjoint'),
        ('Pére', 'Pére'),
        ('Mére', 'Mére'),
        ('Autre', 'Autre')], string='Payment effectué par', )


    acts_ids = fields.One2many('clinic.cash_entry.line', 'entry_id', string='les actes opératoire ',
                               copy=True, )

    tax_amount = fields.Monetary(string='Montant Taxe', compute='_compute_amount', readonly=True, store=True)

    montant = fields.Monetary(string='Montant HT', compute='_compute_amount', store=True, )

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_total', )

    amount_payed = fields.Monetary(string='Montant Payé', readonly=False, store=True, )

    amount_residual = fields.Monetary(string='Rest à Payé', store=True, compute='_compute_amount_residual')

    payment_ref = fields.Char(string='Observation')

    # cote_part = fields.Monetary(string='Cote Part ', readonly=False, compute='_compte_cote', store=True)

    payment_state = fields.Selection(selection=[
        ('Payé', 'Payé'),
        ('Partiellement payé', 'Partiellement payé'),
        ('Non payé', 'Non payé'),
    ], string="État du paiement", store=True, readonly=True, copy=False, tracking=True,
    )

    supplement = fields.Boolean(default=False, string='supplement')

    rest = fields.Boolean(default=False, string=' Payment du rest', store=True, )

    previous_encaissement_id = fields.Many2one('clinic.cash_entry', compute='_get_previous_encaissement',
                                               store=True)

    left_to_pay = fields.Monetary(string='Rest régler', store=True, compute='_compute_left_to_pay')

    convention_dec = fields.Many2one(string='Convention', related='patient_id.convention_id')

    state_dec = fields.Selection(string='Etat', related='patient_id.state')

    end_date_dec = fields.Date(string='date fin de convention', related='patient_id.end_date')

    @api.model
    def create(self, vals):
        if not vals.get('n_bon'):
            vals['n_bon'] = self.env['ir.sequence'].next_by_code('clinic.cash_entry') or _('Nouveau')
        return super(CashEntry, self).create(vals)

    @api.depends('acts_ids', 'acts_ids.amount', 'amount_payed', 'acts_ids.tax', 'acts_ids.difference_amount', 'rest',
                 'supplement')
    def _compute_amount(self):
        for statement in self:

            statement.montant = sum([line.amount for line in statement.acts_ids])
            statement.tax_amount = sum([line.tax_amount for line in statement.acts_ids])
            if not statement.rest:
                statement.amount_total = statement.montant + statement.tax_amount
            elif not statement.supplement:
                statement.amount_total = statement.left_to_pay
            elif statement.rest and statement.supplement:

                statement.amount_total = statement.left_to_pay + statement.montant + statement.tax_amount

            statement.amount_residual = statement.amount_total - statement.amount_payed

            if statement.amount_residual != 0 and statement.amount_payed != 0 and statement.amount_payed != statement.amount_total:
                statement.payment_state = 'Partiellement payé'
            elif statement.amount_payed == statement.amount_total and statement.amount_total != 0:
                statement.payment_state = 'Payé'
            elif statement.rest:
                statement.payment_state = 'Payé'
            elif statement.amount_payed == 0:
                statement.payment_state = 'Non payé'


    @api.depends('acts_ids', 'acts_ids.amount', 'acts_ids.tax_amount')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(line.amount + line.tax_amount for line in record.acts_ids)

    @api.depends('amount_total', 'amount_payed')
    def _compute_amount_residual(self):
        for record in self:
            record.amount_residual = record.amount_total - record.amount_payed

    @api.depends('amount_residual')
    def _compute_payment_state(self):
        for record in self:
            if record.amount_residual <= 0:
                record.payment_state = 'Payé'
            elif record.amount_payed > 0:
                record.payment_state = 'Partiellement payé'
            else:
                record.payment_state = 'Non payé'

    @api.constrains('statement_id', 'payment_state')
    def _check_statement_state(self):
        for record in self:
            if record.statement_id.state == 'closed' and record.payment_state != 'Payé':
                raise ValidationError(_("Impossible d'ajouter ou modifier un encaissement dans un relevé clôturé."))

    def print_bon(self):
        if self.statement_id.id:
            return self.env.ref('clinic.report_caiss_view').report_action(self)
        else:
            raise UserError(_("il faut d' abord sauvegarder"))


class CashEntryLine(models.Model):
    _name = 'clinic.cash_entry.line'
    _description = 'Ligne de facture'

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )

    entry_id = fields.Many2one('clinic.cash_entry', string='Encaissement', required=True, ondelete='cascade')
    act_id = fields.Many2one('product.product', string='Acte', domain="[('is_medical_act', '=', True)]", required=True)

    amount = fields.Float(string='Montant', compute='_compute_amount', store=True)

    tax_amount = fields.Float(string='Montant taxe', compute='_compute_amount', store=True)


    rate_type = fields.Selection([
        ('Tarif Public', 'Tarif Public'),
        ('Tarif Convention ', 'Tarif Convention'),
    ], string='Type de Tarif', default="Tarif Public")

    tax = fields.Selection([
        ('HT', 'HT'),
        ('19%', '19%'),
        ('9%', '9%'),
    ], string='Taxe', default="HT")

    difference_amount = fields.Monetary(string='Difference', store=True, )

    doctor_id_dec = fields.Many2one('res.partner', string='Médecin', domain="[('doctor', '=', True)]",
                                    related='entry_id.doctor_id', store=True)

    date_dec = fields.Date(string='Date', related='entry_id.date', store=True)

    designation_dec = fields.Char(string='Désignation', related='act_id.name', store=True)

    patient_id_dec = fields.Many2one(related='entry_id.patient_id', string='Patient', store=True)

    family_id_dec = fields.Many2one(related='act_id.categ_id', string='Famille', store=True)

    n_bon_dec = fields.Char(related='entry_id.n_bon', string='N°Bon', store=True)

    cote_part = fields.Monetary(string='Cote Part ', readonly=False, compute='_compte_cote', store=True)

    per_cpart = fields.Float('% Cote Part', )


    @api.onchange('doctor_id_dec')
    def cote_value(self):
        for rec in self:
            percentge = rec.doctor_id_dec.percentage_cote_part
            if percentge > 0:
                rec.per_cpart = percentge
            else:
                rec.per_cpart = 0.0

    @api.depends('act_id', 'doctor_id_dec', 'doctor_id_dec.percentage_cote_part')
    def _compte_cote(self):
        for act in self:
            p = 0
            percentge = act.per_cpart

            p = p + (((act.act_id.list_price + act.difference_amount) * percentge) / 100)

            act.cote_part = p


    @api.depends('rate_type', 'act_id', 'tax', 'difference_amount')
    def _compute_amount(self):
        for line in self:
            price = 0.0

            if line.rate_type == 'Tarif Convention ' and line.entry_id.convention_dec:
                pricelist = line.entry_id.convention_dec.pricelist_id
                price = pricelist._get_product_price(line.act_id, 1.0)

            else:
                price = line.act_id.list_price

            price += line.difference_amount

            # taxes
            if line.tax == '19%':
                line.tax_amount = price * 0.19
            elif line.tax == '9%':
                line.tax_amount = price * 0.09
            else:
                line.tax_amount = 0.0

            line.amount = price


class CashExit(models.Model):
    _name = 'clinic.cash_exit'
    _description = 'Décaissement'
    _inherit = ['mail.thread']
    _order = 'date desc'

    n_bon = fields.Char(string='Référence', readonly=True, default=lambda self: _('Nouveau'))
    statement_id = fields.Many2one('clinic.cash_statement',
                                   string='Relevé de Caisse', required=True)
    partner_id = fields.Many2one('res.partner', string='Destinataire',
                                   required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    montant = fields.Monetary(string='Montant', required=True)
    motif = fields.Selection([
        ('Remboursement', "Remboursement"),
        ('Décaissement', "Décaissement"),
        ('Cote part', 'Cote part'),
        ('Achats', "Achats"),
        ('Autre', 'Autre'),
    ], string='Motif', default='Cote part', required=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    note = fields.Text(string='Notes')

    def print_bon_d(self):
        return self.env.ref('clinic.report_decaissement').report_action(self)

    @api.model
    def create(self, vals):
        if not vals.get('n_bon'):
            vals['n_bon'] = self.env['ir.sequence'].next_by_code('clinic.cash_exit') or _('Nouveau')
        return super(CashExit, self).create(vals)

