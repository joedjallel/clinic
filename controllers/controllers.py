# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json


class ClinicController(http.Controller):
    @http.route('/clinic/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, **kw):
        """API endpoint to get dashboard data for the encounter manager"""
        # Get encounters
        encounters = request.env['clinic.encounter'].search_read(
            [], 
            ['name', 'patient_id', 'appointment_id', 'service_id', 'room_id', 'start', 'end', 'type', 'state', 'doctor_id'],
            order='start desc'
        )
        
        # Get rooms
        rooms = request.env['clinic.consultation.room'].search_read(
            [], 
            ['name', 'service_id']
        )
        
        # Get services
        services = request.env['clinic.service'].search_read(
            [], 
            ['name']
        )
        
        # Get doctors
        doctors = request.env['res.partner'].search_read(
            [('doctor', '=', True)], 
            ['id', 'name']
        )
        
        return {
            'encounters': encounters,
            'rooms': rooms,
            'services': services,
            'doctors': doctors
        }
    
    @http.route('/clinic/encounter/update', type='json', auth='user')
    def update_encounter(self, encounter_id, values, **kw):
        """API endpoint to update an encounter"""
        encounter = request.env['clinic.encounter'].browse(int(encounter_id))
        if not encounter.exists():
            return {'success': False, 'error': 'Encounter not found'}
        
        try:
            # Handle prescriptions separately if provided
            prescriptions = values.pop('prescriptions', None)
            if prescriptions is not None:
                # Create a prescription record if not empty
                if prescriptions.strip():
                    request.env['clinic.prescription'].create({
                        'encounter_id': encounter.id,
                        'description': prescriptions,
                        'date': fields.Datetime.now(),
                    })
            
            # Update the encounter with remaining values
            if values:
                encounter.write(values)
                
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

