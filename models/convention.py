from odoo import models, fields, api, _


class Convention(models.Model):
    _name = 'clinic.convention'
    _description = 'Convention'
    _rec_name = 'name'

    def open_conv_patient(self):
        return {
            'name': 'Patient',
            'domain': [('convention_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'clinic.recipient',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    def open_conv_tarif(self):
        return {
            'name': 'Tarifs',
            'domain': [('convention_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'clinic.convention.tarif',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    name = fields.Char(string='Convention', store=True, copy=False)

    patients_ids = fields.One2many('res.partner', 'convention_id', string='Patients',
                                   domain="[('patient', '=', True)]")

    pricelist_id = fields.Many2one("product.pricelist", string="Grille tarifaire", required=True)

