# -*- coding: utf-8 -*-
{
    'name': "Gestion pour Établissements de Santé",

    'summary': "Système d'Information Hospitalier complet pour la gestion des établissements de santé",

    'description': """
Système Avancé de Gestion pour Établissements de Santé

Fonctionnalités Principales:
- Gestion des Patients: Dossiers médicaux complets, historique médical et informations personnelles
- Gestion des Rendez-vous: Organisation des consultations avec intégration du calendrier et système de file d'attente
- Actes Médicaux & Facturation: Configuration des procédures médicales, tarification et gestion de la facturation
- Hospitalisation: Suivi des admissions, gestion des lits et séjours des patients
- Gestion du Bloc Opératoire: Planification et suivi des interventions chirurgicales
- Gestion des Médecins: Gestion des profils médicaux, spécialités et partage des revenus
- Gestion des Ordonnances: Rédaction et suivi des prescriptions numériques
- Gestion des Conventions: Support pour les conventions d'assurance et de santé
- Gestion Financière: Gestion des opérations de caisse, paiements et remboursements
- Rapports: Reporting complet sur les opérations cliniques et financières

Ce module fournit une solution complète pour:
- Cliniques Privées
- Centres Médicaux
- Établissements de Santé
- Services Hospitaliers

Caractéristiques Techniques:
- Intégration complète avec la comptabilité, les produits et les contacts Odoo
- Règles de sécurité et droits d'accès personnalisés
- Tableaux de bord interactifs et KPIs
- Gestion et suivi des documents
""",

    'author': "Yani Technology",
    'website': "https://yanitechnology.com",
    'category': 'Healthcare/Medical',
    'version': '1.0',

    'depends': ['base', 'mail', 'product', 'account', 'stock', 'web_timeline'],
    # always loaded
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/act_views.xml',
        'views/cash_views.xml',
        'views/convention_views.xml',
        'views/appointment_views.xml',
        'views/admission_views.xml',
        'views/hc_base_views.xml',
        'views/hospitalisation_views.xml',
        'views/operating_room_views.xml',
        # 'views/prescription_views.xml',
        'views/encounter_views.xml',
        'views/menus.xml',
        'reports/bon.xml',
        'data/sequences.xml',
        'data/queue_stage_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
            'clinic/static/src/js/encounter_manager.js',
            'clinic/static/src/xml/encounter_manager.xml',
            'clinic/static/src/css/encounter_manager.css',

            'clinic/static/src/css/dashboard.scss',
            'clinic/static/src/js/manager_dashboard.js',
            'clinic/static/src/xml/manager_dashboard.xml',

        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
}
