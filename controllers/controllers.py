# -*- coding: utf-8 -*-
from datetime import date

from odoo import http, fields
from odoo.http import request, _logger
import json


class ClinicController(http.Controller):

    @http.route('/clinic/user/doctor_id', type='json', auth='user')
    def user_doctor_id(self):
        """Return partner_id of current user if he is a doctor else None."""
        user = request.env.user
        doctor = request.env['res.partner'].sudo().search([
            ('user_ids', 'in', [user.id]),
            ('doctor', '=', True)
        ], limit=1)
        return doctor.id if doctor else None

    @http.route('/clinic/doctor/today_encounter', type='json', auth='user')
    def doctor_today_encounter(self, doctor_id):
        print(doctor_id)
        today_start = date.today()
        enc = request.env['clinic.encounter'].sudo().search([
            ('doctor_id', '=', int(doctor_id)),
            # ('start', '>=', fields.Datetime.to_datetime(today_start)),
            # ('state', 'in', ['draft', 'in_progress']),
        ], limit=1)
        print(enc)
        return {'id': enc.id, 'patient_id': enc.patient_id.id} if enc else None


    @http.route('/clinic/patient/data', type='json', auth='user')
    def patient_data(self, patient_id):
        print(patient_id)
        pat = request.env['res.partner'].sudo().browse(int(patient_id))
        return {
            'name': pat.name,
            'age': pat.age or '',
            'gender': pat.gender or '',
            'phone': pat.phone or '',
        }
