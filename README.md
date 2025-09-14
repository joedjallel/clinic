🚩 Résumé

clinic est un ensemble de modules Odoo pour gérer un SIH : patients, admissions, consultations, prescriptions, pharmacie, laboratoire, bloc opératoire et facturation basique (tiers-payant prévu mais à implémenter/adapter).
Ce README décrit l’intention, l’organisation, l’installation rapide, les points critiques fonctionnels et la feuille de route priorisée.

✳️ Fonctionnalités principales (actuelles / prévues)

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

#Installation
##Prerequisites

  ###  A working Odoo 17 environment.

Steps

    Clone or place the module into your Odoo addons path.
    bash

git clone <your-repo-url> /path/to/odoo/addons/

    Restart your Odoo service.

    Update the Apps List: In your Odoo interface, go to Settings -> Apps -> Update Apps List.

    Install the Module: Search for "Clinic" in the Apps menu and click Install.

Configuration

After installation, a few steps are recommended:

    Load Demo Data (Optional): The module contains demo data. To use it, ensure your Odoo instance was started with the --load-demo-data flag or enable demo data during database creation.

    Configure Doctors:

        Go to Clinic -> Masters -> Doctors.

        Create a new doctor record.

        Crucial Step: Link the doctor to an existing Odoo user in the User field. This is necessary for access rights and functionality.

Usage Guide
1. Managing Patients

    Navigate to: Clinic -> Masters -> Patients

    Click New to create a new patient. Fill in details like Name, Date of Birth, Gender, and Phone.

    Use the smart button on a patient's form to quickly view all their associated appointments.

2. Scheduling an Appointment

    Navigate to: Clinic -> Operations -> Appointments

    Click New.

    Select a Patient and a Doctor. The system will automatically filter available doctors.

    Choose a Date and set the Start/End Time.

    Click Confirm to change the state from Draft to Confirmed. The system will check for scheduling conflicts automatically.

    After the appointment is completed, click Mark as Done.

3. Writing a Prescription

    Prescriptions can be created directly from a completed appointment (in Done state).

    In the appointment form, navigate to the Prescription tab.

    Enter the Diagnosis and the prescribed Medication with Dosage and Instructions.

    This information is saved and linked to the appointment and patient for historical tracking.

Troubleshooting

    "The doctor is not available" Error:
    This means the doctor already has a confirmed appointment in the selected time slot. Please choose a different time or a different doctor.

    Doctor does not appear in selection:
    Ensure the doctor record has been created and is linked to an active Odoo user in the User field.

Contributing

Contributions to improve the Clinic module are welcome. Please feel free to fork the repository, make your changes, and submit a pull request.

    Fork the Project

    Create your Feature Branch (git checkout -b feature/AmazingFeature)

    Commit your Changes (git commit -m 'Add some AmazingFeature')

    Push to the Branch (git push origin feature/AmazingFeature)

    Open a Pull Request

License

This project is licensed under the LGPL-3 License - see the LICENSE file for details.
