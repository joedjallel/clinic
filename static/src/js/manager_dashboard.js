/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";

class ManagerDashboard extends Component {
    static template = "clinic.ManagerDashboard";

    setup() {
        this.state = useState({
            total_patients: 0,
            total_doctors: 0,
            total_admissions: 0,
            avg_payment_delay: 0,
            appointments_data: [],
            consultations_data: [],
            cash_entry_data: [],
            cash_statement_data: [],
            revenue_by_service: [],
            error: null,
            loading: true
        });

        this.appointmentsChartRef = useRef('appointmentsChart');
        this.consultationsChartRef = useRef('consultationsChart');
        this.cashEntryChartRef = useRef('cashEntryChart');
        this.cashStatementChartRef = useRef('cashStatementChart');
        this.revenueByServiceChartRef = useRef('revenueByServiceChart');
        this.orOccupationChartRef = useRef('orOccupationChart'); // ADD THIS LINE

        this.charts = {};

        onWillStart(async () => {
            await this.fetchData();
        });

        // Move chart rendering to onMounted to ensure DOM elements are available
        onMounted(() => {
            if (!this.state.loading && !this.state.error) {
                this.renderCharts();
            }
        });
    }

    async fetchData() {
        try {
            this.state.loading = true;
            const result = await jsonrpc("/manager/dashboard/data", {});

            console.log(result);
            this.state.total_patients = result.total_patients || 0;
            this.state.total_doctors = result.total_doctors || 0;
            this.state.total_admissions = result.total_admissions || 0;
            this.state.avg_payment_delay = result.avg_payment_delay || 0;
            this.state.appointments_data = result.appointments_data || [];
            this.state.consultations_data = result.consultations_data || [];
            this.state.cash_entry_data = result.cash_entry_data || [];
            this.state.cash_statement_data = result.cash_statement_data || [];
            this.state.revenue_by_service = result.revenue_by_service || [];
            this.state.operation_data = result.operation_data || [];
            this.state.or_occupation = result.or_occupation || [];

            this.state.error = null;
            this.state.loading = false;

            // Only render charts if component is already mounted
            if (this.appointmentsChartRef.el) {
                this.renderCharts();
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des données du tableau de bord:', error);
            this.state.error = _t('Impossible de charger les données du tableau de bord. Veuillez réessayer plus tard.');
            this.state.loading = false;
        }
    }

    destroyExistingCharts() {
        // Destroy existing charts before creating new ones
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                this.charts[key].destroy();
                delete this.charts[key];
            }
        });
    }

    renderCharts() {
        console.log('renderCharts() called');

        // Destroy existing charts first
        this.destroyExistingCharts();

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded. Make sure to include Chart.js library.');
            return;
        }

        console.log('Chart.js is available, version:', Chart.version);

        // Debug: Check if DOM elements exist
        console.log('DOM References:', {
            appointments: this.appointmentsChartRef?.el,
            consultations: this.consultationsChartRef?.el,
            cashEntry: this.cashEntryChartRef?.el,
            cashStatement: this.cashStatementChartRef?.el,
            revenueByService: this.revenueByServiceChartRef?.el,
            orOccupation: this.orOccupationChartRef?.el
        });

        // Bar Chart: Appointments per Day
        if (this.appointmentsChartRef?.el && this.state.appointments_data?.length > 0) {
            try {
                console.log('Creating appointments chart with data:', this.state.appointments_data);
                this.charts.appointments = new Chart(this.appointmentsChartRef.el, {
                    type: 'bar',
                    data: {
                        labels: this.state.appointments_data.map(d => d.date),
                        datasets: [{
                            label: _t('Nombre de rendez-vous'),
                            data: this.state.appointments_data.map(d => d.count),
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
                console.log('Appointments chart created successfully');
            } catch (error) {
                console.error('Error creating appointments chart:', error);
            }
        } else {
            console.log('Skipping appointments chart - element:', !!this.appointmentsChartRef?.el, 'data length:', this.state.appointments_data?.length);
        }

        // Bar Chart: Consultations by Type
        if (this.consultationsChartRef?.el && this.state.consultations_data?.length > 0) {
            try {
                console.log('Creating consultations chart with data:', this.state.consultations_data);
                this.charts.consultations = new Chart(this.consultationsChartRef.el, {
                    type: 'bar',
                    data: {
                        labels: this.state.consultations_data.map(d => d.type),
                        datasets: [{
                            label: _t('Nombre de consultations'),
                            data: this.state.consultations_data.map(d => d.count),
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.6)',
                                'rgba(54, 162, 235, 0.6)',
                                'rgba(255, 206, 86, 0.6)',
                                'rgba(75, 192, 192, 0.6)',
                                'rgba(153, 102, 255, 0.6)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
                console.log('Consultations chart created successfully');
            } catch (error) {
                console.error('Error creating consultations chart:', error);
            }
        } else {
            console.log('Skipping consultations chart - element:', !!this.consultationsChartRef?.el, 'data length:', this.state.consultations_data?.length);
        }

        // Pie Chart: Cash Entries by Payment State
        if (this.cashEntryChartRef?.el && this.state.cash_entry_data?.length > 0) {
            try {
                console.log('Creating cash entry chart with data:', this.state.cash_entry_data);
                this.charts.cashEntry = new Chart(this.cashEntryChartRef.el, {
                    type: 'pie',
                    data: {
                        labels: this.state.cash_entry_data.map(d => d.state),
                        datasets: [{
                            label: _t('Encaissements'),
                            data: this.state.cash_entry_data.map(d => d.count),
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.6)',
                                'rgba(54, 162, 235, 0.6)',
                                'rgba(255, 206, 86, 0.6)',
                                'rgba(75, 192, 192, 0.6)',
                                'rgba(153, 102, 255, 0.6)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                console.log('Cash entry chart created successfully');
            } catch (error) {
                console.error('Error creating cash entry chart:', error);
            }
        } else {
            console.log('Skipping cash entry chart - element:', !!this.cashEntryChartRef?.el, 'data length:', this.state.cash_entry_data?.length);
        }

        // Pie Chart: Revenue by Service
        if (this.revenueByServiceChartRef?.el && this.state.revenue_by_service?.length > 0) {
            try {
                console.log('Creating revenue by service chart with data:', this.state.revenue_by_service);
                this.charts.revenueByService = new Chart(this.revenueByServiceChartRef.el, {
                    type: 'pie',
                    data: {
                        labels: this.state.revenue_by_service.map(d => d.service),
                        datasets: [{
                            label: _t('Revenus'),
                            data: this.state.revenue_by_service.map(d => d.total),
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.6)',
                                'rgba(54, 162, 235, 0.6)',
                                'rgba(255, 206, 86, 0.6)',
                                'rgba(75, 192, 192, 0.6)',
                                'rgba(153, 102, 255, 0.6)',
                                'rgba(255, 159, 64, 0.6)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)',
                                'rgba(255, 159, 64, 1)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                console.log('Revenue by service chart created successfully');
            } catch (error) {
                console.error('Error creating revenue by service chart:', error);
            }
        } else {
            console.log('Skipping revenue by service chart - element:', !!this.revenueByServiceChartRef?.el, 'data length:', this.state.revenue_by_service?.length);
        }

        // Line Chart: Cash Statement Balances
        if (this.cashStatementChartRef?.el && this.state.cash_statement_data?.length > 0) {
            try {
                console.log('Creating cash statement chart with data:', this.state.cash_statement_data);
                this.charts.cashStatement = new Chart(this.cashStatementChartRef.el, {
                    type: 'line',
                    data: {
                        labels: this.state.cash_statement_data.map(d => d.date),
                        datasets: [{
                            label: _t('Solde'),
                            data: this.state.cash_statement_data.map(d => d.balance),
                            fill: false,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2,
                        animation: {
                            duration: 0
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                console.log('Cash statement chart created successfully');
            } catch (error) {
                console.error('Error creating cash statement chart:', error);
            }
        } else {
            console.log('Skipping cash statement chart - element:', !!this.cashStatementChartRef?.el, 'data length:', this.state.cash_statement_data?.length);
        }

        // Line Chart: OR Occupation Rate
        if (this.orOccupationChartRef?.el && this.state.or_occupation?.length > 0) {
            try {
                console.log('Creating OR occupation chart with data:', this.state.or_occupation);
                this.charts.orOccupation = new Chart(this.orOccupationChartRef.el, {
                    type: 'line',
                    data: {
                        labels: this.state.or_occupation.map(d => d.day),
                        datasets: [{
                            label: _t('Taux occupation salle (%)'),
                            data: this.state.or_occupation.map(d => d.occupation_rate_percent),
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.1,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
                console.log('OR occupation chart created successfully');
            } catch (error) {
                console.error('Error creating OR occupation chart:', error);
            }
        } else {
            console.log('Skipping OR occupation chart - element:', !!this.orOccupationChartRef?.el, 'data length:', this.state.or_occupation?.length);
        }

        console.log('renderCharts() completed. Created charts:', Object.keys(this.charts));
    }

    // Method to refresh data and charts
    async refreshDashboard() {
        await this.fetchData();
    }

    // Clean up charts when component is destroyed
    willDestroy() {
        this.destroyExistingCharts();
    }
}

registry.category("actions").add("clinic.manager_dashboard", ManagerDashboard);