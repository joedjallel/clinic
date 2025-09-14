/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useState, useEnv, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";

export class EncounterManager extends Component {
    setup() {
        this.env = useEnv();
        this.formRef = useRef("encounterForm");
        
        this.state = useState({
            encounters: [],
            rooms: [],
            services: [],
            doctors: [],
            selectedEncounter: null,
            isLoading: true,
            error: null,
            isSaving: false
        });

    
        this._fetchData();
    }

  
    get encountersByState() {
        const grouped = {};
        for (const encounter of this.state.encounters) {
            const state = encounter.state || "draft";
            if (!grouped[state]) {
                grouped[state] = [];
            }
            grouped[state].push(encounter);
        }
        return grouped;
    }

    async _fetchData() {
        try {
            this.state.isLoading = true;
            this.state.error = null;
            
            const result = await jsonrpc("/clinic/dashboard/data", {});
            
            // Validate and safely assign data to avoid XrayWrapper issues
            if (result && typeof result === "object") {
                // Use Object.assign to avoid XrayWrapper issues
                this.state.encounters = this._safeArrayCopy(result.encounters);
                this.state.rooms = this._safeArrayCopy(result.rooms);
                this.state.services = this._safeArrayCopy(result.services);
                this.state.doctors = this._safeArrayCopy(result.doctors);
            } else {
                throw new Error("Invalid response from server");
            }
            
            this._validateSelectedEncounter();

        } catch (error) {
            this.state.error = error.message || "Une erreur est survenue lors du chargement des données";
            console.error("Error fetching data:", error);
            
            if (this.env.services && this.env.services.notification) {
                this.env.services.notification.add(this.state.error, {
                    title: "Erreur de chargement",
                    type: "danger"
                });
            }
        } finally {
            this.state.isLoading = false;
        }
    }

    // Helper to safely copy arrays and avoid XrayWrapper issues
    _safeArrayCopy(source) {
        if (!Array.isArray(source)) {
            return [];
        }
        return source.map(item => {
            if (typeof item === "object" && item !== null) {
                return Object.assign({}, item);
            }
            return item;
        });
    }

    // Helper to safely copy objects
    _safeObjectCopy(source) {
        if (typeof source !== "object" || source === null) {
            return {};
        }
        return Object.assign({}, source);
    }

    _validateSelectedEncounter() {
        if (this.state.selectedEncounter) {
            const stillExists = this.state.encounters.find(e => e.id === this.state.selectedEncounter.id);
            if (stillExists) {
                this.state.selectedEncounter = this._safeObjectCopy(stillExists);
            } else {
                this.state.selectedEncounter = null;
            }
        }
    }
    
    async refreshData() {
        await this._fetchData();
        if (this.env.services && this.env.services.notification) {
            this.env.services.notification.add("Données actualisées", {
                title: "Information",
                type: "info"
            });
        }
    }

    selectEncounter(encounter) {
        if (!encounter || !encounter.id) {
            console.warn("Invalid encounter selected");
            return;
        }
        this.state.selectedEncounter = this._safeObjectCopy(encounter);
    }
    
    closeDetails() {
        this.state.selectedEncounter = null;
    }

    async updateState(encounterId, newState) {
        if (!encounterId || !newState) {
            console.error("Invalid parameters for state update");
            return;
        }

        const validStates = ["draft", "scheduled", "in_progress", "completed", "cancelled"];
        if (!validStates.includes(newState)) {
            if (this.env.services && this.env.services.notification) {
                this.env.services.notification.add("État invalide", {
                    title: "Erreur",
                    type: "danger"
                });
            }
            return;
        }

        try {
            const result = await jsonrpc("/clinic/encounter/update", {
                encounter_id: encounterId,
                values: { state: newState }
            });
            
            if (result && result.success) {
                this._updateLocalEncounter(encounterId, { state: newState });
                
                if (this.env.services && this.env.services.notification) {
                    this.env.services.notification.add("État mis à jour avec succès", {
                        title: "Succès",
                        type: "success"
                    });
                }
            } else {
                throw new Error((result && result.error) || "Erreur lors de la mise à jour de l'état");
            }
        } catch (error) {
            console.error("Error updating encounter state:", error);
            if (this.env.services && this.env.services.notification) {
                this.env.services.notification.add(error.message || "Impossible de mettre à jour l'état", {
                    title: "Erreur",
                    type: "danger"
                });
            }
        }
    }

    _updateLocalEncounter(encounterId, updates) {
        // Update in encounters list
        const encounterIndex = this.state.encounters.findIndex(e => e.id === encounterId);
        if (encounterIndex !== -1) {
            // Use Object.assign to safely update
            Object.assign(this.state.encounters[encounterIndex], updates);
        }
        
        // Update selected encounter if it matches
        if (this.state.selectedEncounter && this.state.selectedEncounter.id === encounterId) {
            Object.assign(this.state.selectedEncounter, updates);
        }
    }

    _validateEncounterData(encounter) {
        const errors = [];
        
        if (!encounter.type) {
            errors.push("Le type de consultation est requis");
        }
        
        if (!encounter.room_id) {
            errors.push("La salle est requise");
        }
        
        if (!encounter.service_id) {
            errors.push("Le service est requis");
        }
        
        return errors;
    }

    async saveEncounter() {
        if (!this.state.selectedEncounter) {
            console.warn("No encounter selected for saving");
            return;
        }
        
        if (this.state.isSaving) {
            return; // Prevent double-submission
        }
        
        try {
            this.state.isSaving = true;
            
            const validationErrors = this._validateEncounterData(this.state.selectedEncounter);
            if (validationErrors.length > 0) {
                if (this.env.services && this.env.services.notification) {
                    this.env.services.notification.add(validationErrors.join("\\n"), {
                        title: "Données invalides",
                        type: "warning"
                    });
                }
                return;
            }
            
            const values = {
                type: this.state.selectedEncounter.type,
                room_id: this.state.selectedEncounter.room_id,
                service_id: this.state.selectedEncounter.service_id,
                doctor_id: this.state.selectedEncounter.doctor_id || this.env.session.uid,
            };
            
            // Safely get prescriptions if doctor and form exists
            if (this.isDoctor && this.formRef.el) {
                const prescriptionsEl = this.formRef.el.querySelector(".o_encounter_prescriptions textarea");
                if (prescriptionsEl && prescriptionsEl.value && prescriptionsEl.value.trim()) {
                    values.prescriptions = prescriptionsEl.value.trim();
                }
            }
            
            const result = await jsonrpc("/clinic/encounter/update", {
                encounter_id: this.state.selectedEncounter.id,
                values: values
            });
            
            if (result && result.success) {
                if (this.env.services && this.env.services.notification) {
                    this.env.services.notification.add("Consultation mise à jour avec succès", {
                        title: "Succès",
                        type: "success"
                    });
                }
                
                if (result.encounter) {
                    this._updateLocalEncounter(this.state.selectedEncounter.id, this._safeObjectCopy(result.encounter));
                } else {
                    await this._fetchData();
                }
            } else {
                throw new Error((result && result.error) || "Erreur lors de la mise à jour");
            }
            
        } catch (error) {
            console.error("Error saving encounter:", error);
            if (this.env.services && this.env.services.notification) {
                this.env.services.notification.add(error.message || "Impossible de sauvegarder les modifications", {
                    title: "Erreur",
                    type: "danger"
                });
            }
        } finally {
            this.state.isSaving = false;
        }
    }

    getStateLabel(state) {
        const labels = {
            "draft": "Brouillon",
            "scheduled": "Programmé",
            "in_progress": "En cours",
            "completed": "Terminé",
            "cancelled": "Annulé"
        };
        return labels[state] || state;
    }

    getStateBadgeClass(state) {
        const classes = {
            "draft": "badge-secondary",
            "scheduled": "badge-primary",
            "in_progress": "badge-warning",
            "completed": "badge-success",
            "cancelled": "badge-danger"
        };
        return classes[state] || "badge-secondary";
    }
}

EncounterManager.template = "clinic.EncounterManagerTemplate";

// Register the component
registry.category("actions").add("clinic.encounter_manager", EncounterManager);