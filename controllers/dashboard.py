from odoo import http, fields
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class DashboardController(http.Controller):
    @http.route('/manager/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """Fetch data for the manager dashboard with error handling."""
        try:
            today = datetime.today().date()
            week_ago = today - relativedelta(days=7)

            # Total patients and doctors
            total_patients = request.env['res.partner'].search_count([('patient', '=', True)])
            total_doctors = request.env['res.partner'].search_count([('doctor', '=', True)])

            # Total current admissions
            total_admissions = 0
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.admission')]):
                total_admissions = request.env['clinic.admission'].search_count([('state', '=', 'admitted')])

            # Average payment delay for cash entries
            avg_payment_delay = 0
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.cash_entry')]):
                cash_entries = request.env['clinic.cash_entry'].search([
                    ('payment_state', 'in', ['Non payé', 'Partiellement payé']),
                    ('date', '>=', week_ago)
                ])
                total_delay = 0
                count_delay = 0
                for entry in cash_entries:
                    if entry.amount_residual > 0:
                        delay = (today - entry.date).days
                        total_delay += delay
                        count_delay += 1
                avg_payment_delay = total_delay / count_delay if count_delay > 0 else 0

            # Appointments data (last 7 days)
            appointments_data = []
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.appointment')]):
                appointments = request.env['clinic.appointment'].read_group(
                    [('date_rdv', '>=', week_ago), ('date_rdv', '<=', today)],
                    ['date_rdv'],
                    ['date_rdv:day'],
                    orderby='date_rdv:day'
                )
                appointments_data = [{'date': group['date_rdv:day'], 'count': group['date_rdv_count']} for group in
                                     appointments]

            # Consultations by type (last 7 days)
            consultations_data = []
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.encounter')]):
                consultations = request.env['clinic.encounter'].read_group(
                    [('start', '>=', week_ago), ('start', '<=', today)],
                    ['type'],
                    ['type']
                )
                consultations_data = [{'type': group['type'], 'count': group['type_count']} for group in consultations]

            # Cash entries by payment state
            cash_entry_data = []
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.cash_entry')]):
                cash_entries_state = request.env['clinic.cash_entry'].read_group(
                    [('date', '>=', week_ago)],
                    ['payment_state'],
                    ['payment_state']
                )
                cash_entry_data = [{'state': group['payment_state'], 'count': group['payment_state_count']} for group in
                                   cash_entries_state]

            # Cash statement balances
            cash_statement_data = []
            if request.env['ir.model'].sudo().search([('model', '=', 'clinic.cash_statement')]):
                cash_statements = request.env['clinic.cash_statement'].search(
                    [('date', '>=', week_ago)],
                    order='date asc'
                )
                cash_statement_data = [{'date': str(st.date), 'balance': st.total_cash_entry} for st in cash_statements]

            # Revenue by service - commented out as it was causing issues
            revenue_by_service_data = []
            # if request.env['ir.model'].sudo().search([('model', '=', 'clinic.service')]):
            #     revenue_by_service = request.env['clinic.cash_entry'].read_group(
            #         [('date', '>=', week_ago), ('service_id', '!=', False)],
            #         ['service_id', 'amount_total:sum'],
            #         ['service_id']
            #     )
            #     revenue_by_service_data = [
            #         {
            #             'service': request.env['clinic.service'].browse(group['service_id'][0]).name,
            #             'total': group['amount_total_sum']
            #         }
            #         for group in revenue_by_service
            #     ]

            # Operations data with proper error handling
            operation_data = []
            operation_count = 0
            try:
                if request.env['ir.model'].sudo().search([('model', '=', 'clinic.operation')]):
                    operation_data = request.env['clinic.operation'].read_group(
                        [('start_datetime', '>=', fields.Datetime.to_string(week_ago)),
                         ('start_datetime', '<=', fields.Datetime.to_string(today))],
                        ['state'],
                        ['state']
                    )
                    operation_data = [{'state': r['state'], 'count': r['state_count']} for r in operation_data]

                    # Fixed operation count calculation
                    operation_count = request.env['clinic.operation'].search_count([
                        ('start_datetime', '>=', fields.Datetime.to_string(week_ago)),
                        ('start_datetime', '<=', fields.Datetime.to_string(today))
                    ])
            except Exception as e:
                _logger.warning("Error fetching operation data: %s", str(e))
                operation_data = []
                operation_count = 0

            # OR occupation data with error handling
            or_occupation = []
            try:
                if request.env['ir.model'].sudo().search([('model', '=', 'clinic.kpi.or.occupation')]):
                    or_occupation = request.env['clinic.kpi.or.occupation'].search_read(
                        [('day', '>=', week_ago), ('day', '<=', today)],
                        ['day', 'occupation_rate_percent']
                    )
                    # Convert day to string for JSON serialization
                    for item in or_occupation:
                        if 'day' in item:
                            item['day'] = str(item['day'])
            except Exception as e:
                _logger.warning("Error fetching OR occupation data: %s", str(e))
                or_occupation = []

            # Today's OR interventions with error handling
            or_today = []
            try:
                if request.env['ir.model'].sudo().search([('model', '=', 'clinic.operation')]):
                    now = fields.Datetime.now()
                    day_start = now.replace(hour=0, minute=0, second=0)
                    day_end = now.replace(hour=23, minute=59, second=59)

                    or_today = request.env['clinic.operation'].search_read(
                        [('start_datetime', '>=', day_start),
                         ('start_datetime', '<=', day_end),
                         ('state', '!=', 'cancel')],
                        ['id', 'name', 'room_id', 'start_datetime', 'duration_minutes',
                         'patient_id', 'surgeon_id', 'state']
                    )
            except Exception as e:
                _logger.warning("Error fetching today's OR interventions: %s", str(e))
                or_today = []

            # Live admissions with error handling
            admissions_live = []
            try:
                if request.env['ir.model'].sudo().search([('model', '=', 'clinic.admission')]):
                    admissions_live = request.env['clinic.admission'].search_read(
                        [('state', 'in', ['admitted', 'pre_admit'])],
                        ['id', 'name', 'patient_id', 'service_id', 'bed_id', 'state']
                    )
            except Exception as e:
                _logger.warning("Error fetching live admissions: %s", str(e))
                admissions_live = []

            # Bed occupancy with error handling
            bed_occupancy = {}
            try:
                if request.env['ir.model'].sudo().search([('model', '=', 'clinic.bed')]):
                    beds = request.env['clinic.bed'].read_group(
                        [], ['service_id', 'state'], ['service_id', 'state']
                    )
                    # reshape to dict {service_id: {free: n, occupied: n, cleaning: n}}
                    for b in beds:
                        svc = b['service_id'][0] if b['service_id'] else 0
                        if svc not in bed_occupancy:
                            bed_occupancy[svc] = {}
                        bed_occupancy[svc][b['state']] = b['service_id_count']
            except Exception as e:
                _logger.warning("Error fetching bed occupancy: %s", str(e))
                bed_occupancy = {}

            return {
                'total_patients': total_patients,
                'total_doctors': total_doctors,
                'total_admissions': total_admissions,
                'avg_payment_delay': avg_payment_delay,
                'appointments_data': appointments_data,
                'consultations_data': consultations_data,
                'cash_entry_data': cash_entry_data,
                'cash_statement_data': cash_statement_data,
                'revenue_by_service': revenue_by_service_data,
                'operation_count': operation_count,
                'operation_data': operation_data,
                'or_occupation': or_occupation,
                'or_today': or_today,
                'admissions_live': admissions_live,
                'bed_occupancy': bed_occupancy,
            }
        except Exception as e:
            _logger.error("Error in get_dashboard_data: %s", str(e), exc_info=True)
            return {
                'error': "Erreur lors de la récupération des données du tableau de bord: %s" % str(e)
            }