/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DoctorEncounterForm extends Component {
    static template = "clinic.EncounterManagerTemplate";

    setup() {
        this.user = useService("user");
        this.state = useState({
            encounterId: null,
            encounter: {},
            patient: {},
            observations: [],
            prescriptions: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadDoctorEncounter();
        });
    }

    /* ----------  LOAD  ---------- */
    async loadDoctorEncounter() {
        try {
            // 1. Check if current user is linked to a doctor partner
            if (!this.user.userId) {
                this.state.loading = false;
                return;
            }

            const doctorId = await jsonrpc("/clinic/user/doctor_id", {});
            if (!doctorId) {
                console.log("No doctor found for current user");
                this.state.loading = false;
                return;
            }

            const enc = await jsonrpc("/clinic/doctor/today_encounter", {
                doctor_id: doctorId,
            });
            if (!enc || !enc.id) {
                console.log("No encounter found for today");
                this.state.loading = false;
                return;
            }

            this.state.encounterId = enc.id;

            // 4. Load encounter data (simplified - may need to implement these endpoints)
            // For now, let's use basic Odoo model methods
            const encounter = await jsonrpc("/web/dataset/call_kw", {
                model: "clinic.encounter",
                method: "read",
                args: [[enc.id], ["name", "state", "chief_complaint", "diagnosis", "treatment_plan", "follow_up"]],
                kwargs: {}
            });

            const patient = await jsonrpc("/web/dataset/call_kw", {
                model: "res.partner",
                method: "read",
                args: [[enc.patient_id], ["name", "age", "gender", "phone"]],
                kwargs: {}
            });

            // Initialize with safe defaults
            this.state.encounter = encounter && encounter[0] ? encounter[0] : {
                name: "N/A",
                state: "draft",
                chief_complaint: "",
                diagnosis: "",
                treatment_plan: "",
                follow_up: ""
            };

            this.state.patient = patient && patient[0] ? patient[0] : {
                name: "Unknown Patient",
                age: "",
                gender: "",
                phone: "",
            };

            // Initialize empty arrays for now
            this.state.observations = [];
            this.state.prescriptions = [];

            this.state.loading = false;
            console.log("Loaded encounter data:", this.state);

        } catch (error) {
            console.error("Error loading doctor encounter:", error);
            // Set safe defaults on error
            this.state.encounterId = null;
            this.state.encounter = {
                name: "Error",
                state: "draft",
                chief_complaint: "",
                diagnosis: "",
                treatment_plan: "",
                follow_up: ""
            };
            this.state.patient = {
                name: "Error loading patient",
                age: "",
                gender: "",
                phone: "",
                allergies: ""
            };
            this.state.observations = [];
            this.state.prescriptions = [];
            this.state.loading = false;
        }
    }

    /* ----------  SAVE  ---------- */
    async saveField(field) {
        if (!this.state.encounterId) return;
        try {
            await jsonrpc("/web/dataset/call_kw", {
                model: "clinic.encounter",
                method: "write",
                args: [[this.state.encounterId], { [field]: this.state.encounter[field] }],
                kwargs: {}
            });
            console.log(`Saved field ${field}`);
        } catch (error) {
            console.error(`Error saving field ${field}:`, error);
        }
    }

    async toggleStatus() {
        if (!this.state.encounterId) return;

        const MAP = {
            draft: "in_progress",
            in_progress: "done",
            done: "done" // Prevent further changes when done
        };
        const currentState = this.state.encounter.state;
        const nextState = MAP[currentState];

        if (!nextState || nextState === currentState) return;

        try {
            await jsonrpc("/web/dataset/call_kw", {
                model: "clinic.encounter",
                method: "write",
                args: [[this.state.encounterId], { state: nextState }],
                kwargs: {}
            });
            this.state.encounter.state = nextState;
            console.log(`Status updated to: ${nextState}`);
        } catch (error) {
            console.error("Error updating status:", error);
        }
    }

    /* ----------  OBSERVATIONS  ---------- */
    async addObs() {
        if (!this.state.encounterId) return;

        try {
            const obs = await jsonrpc("/clinic/observation/create", {
                encounter_id: this.state.encounterId,
                code: "NEW",
                value_float: 0,
                value_unit: "",
            });
            this.state.observations.push(obs);
        } catch (error) {
            console.error("Error adding observation:", error);
        }
    }

    async removeObs(id) {
        try {
            await jsonrpc("/clinic/observation/unlink", { id });
            this.state.observations = this.state.observations.filter(o => o.id !== id);
        } catch (error) {
            console.error("Error removing observation:", error);
        }
    }

    async saveObservation(obs) {
        try {
            await jsonrpc("/clinic/observation/update", {
                id: obs.id,
                vals: {
                    code: obs.code,
                    value_float: obs.value_float,
                    value_unit: obs.value_unit,
                },
            });
        } catch (error) {
            console.error("Error saving observation:", error);
        }
    }

    /* ----------  PRESCRIPTIONS  ---------- */
    async addRx() {
        if (!this.state.encounterId) return;

        try {
            const rx = await jsonrpc("/clinic/prescription/create", {
                encounter_id: this.state.encounterId,
                name: "Nouveau médicament",
            });
            this.state.prescriptions.push(rx);
        } catch (error) {
            console.error("Error adding prescription:", error);
        }
    }

    async removeRx(id) {
        try {
            await jsonrpc("/clinic/prescription/unlink", { id });
            this.state.prescriptions = this.state.prescriptions.filter(r => r.id !== id);
        } catch (error) {
            console.error("Error removing prescription:", error);
        }
    }

    async savePrescription(rx) {
        try {
            await jsonrpc("/clinic/prescription/update", {
                id: rx.id,
                vals: {
                    name: rx.name,
                },
            });
        } catch (error) {
            console.error("Error saving prescription:", error);
        }
    }

    /* ----------  UTILITY METHODS  ---------- */
    getStatusLabel(state) {
        const labels = {
            draft: "Brouillon",
            in_progress: "En cours",
            done: "Terminé",
            cancelled: "Annulé"
        };
        return labels[state] || state;
    }

    getStatusClass(state) {
        const classes = {
            draft: "btn-secondary",
            in_progress: "btn-warning",
            done: "btn-success",
            cancelled: "btn-danger"
        };
        return classes[state] || "btn-secondary";
    }
}

// Register the component
registry.category("actions").add("clinic.encounter_manager", DoctorEncounterForm);