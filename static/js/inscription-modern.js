/**
 * ===================================================
 * INSCRIPTION - MULTI-STEP FORM LOGIC
 * Dépend de inscription-modern.css
 * ===================================================
 */

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const form = document.getElementById('signupForm');
        if (!form) return;

        const steps = Array.from(form.querySelectorAll('.form-step'));
        const stepperItems = Array.from(document.querySelectorAll('.stepper-item'));
        const stepperLines = Array.from(document.querySelectorAll('.stepper-line'));
        const nextButtons = form.querySelectorAll('[data-action="next"]');
        const prevButtons = form.querySelectorAll('[data-action="prev"]');
        const togglePasswordBtn = document.getElementById('togglePassword');
        const passwordInput = document.getElementById('password');
        const strengthContainer = document.getElementById('passwordStrength');

        let currentStep = 1;
        const totalSteps = steps.length;

        // ==================== STEPPER NAVIGATION ====================

        function showStep(targetStep) {
            const currentEl = form.querySelector(`.form-step[data-step="${currentStep}"]`);
            const targetEl = form.querySelector(`.form-step[data-step="${targetStep}"]`);
            if (!targetEl) return;

            // Animation de sortie
            if (currentEl && currentEl !== targetEl) {
                currentEl.classList.add('exiting');
                setTimeout(() => {
                    currentEl.classList.remove('active', 'exiting');
                    targetEl.classList.add('active');
                    targetEl.querySelector('input')?.focus();
                }, 200);
            } else {
                targetEl.classList.add('active');
                targetEl.querySelector('input')?.focus();
            }

            currentStep = targetStep;
            updateStepper();
        }

        function updateStepper() {
            stepperItems.forEach((item) => {
                const stepNum = parseInt(item.dataset.step, 10);
                item.classList.remove('active', 'completed');

                if (stepNum === currentStep) {
                    item.classList.add('active');
                } else if (stepNum < currentStep) {
                    item.classList.add('completed');
                }
            });

            // Mise à jour des lignes entre les étapes
            stepperLines.forEach((line, index) => {
                const lineStep = index + 1; // line 0 relie step 1 et 2
                if (lineStep < currentStep) {
                    line.classList.add('completed');
                } else {
                    line.classList.remove('completed');
                }
            });
        }

        // ==================== VALIDATION ====================

        function validateField(input) {
            if (!input) return true;

            clearFieldError(input);

            // Vérifier si vide
            if (input.hasAttribute('required') && !input.value.trim()) {
                showFieldError(input, 'Ce champ est requis');
                return false;
            }

            // Vérifier longueur minimale
            if (input.minLength > 0 && input.value.length > 0 && input.value.length < input.minLength) {
                const label = input.dataset.minLengthMessage || `Minimum ${input.minLength} caractères`;
                showFieldError(input, label);
                return false;
            }

            // Vérifier pattern (regex)
            if (input.pattern && input.value) {
                const regex = new RegExp(input.pattern);
                if (!regex.test(input.value)) {
                    showFieldError(input, 'Format invalide');
                    return false;
                }
            }

            return true;
        }

        function showFieldError(input, message) {
            input.classList.add('error');
            const errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
            if (errorEl) {
                if (message) errorEl.textContent = message;
                errorEl.classList.add('visible');
            }
        }

        function clearFieldError(input) {
            input.classList.remove('error');
            const errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
            if (errorEl) {
                errorEl.classList.remove('visible');
            }
        }

        function validateCurrentStep() {
            const currentEl = form.querySelector(`.form-step[data-step="${currentStep}"]`);
            if (!currentEl) return true;

            const inputs = currentEl.querySelectorAll('input[required]');
            let allValid = true;

            inputs.forEach((input) => {
                if (!validateField(input)) {
                    allValid = false;
                }
            });

            return allValid;
        }

        // ==================== EVENT LISTENERS ====================

        // Boutons "Continuer"
        nextButtons.forEach((btn) => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                if (validateCurrentStep()) {
                    const nextStep = parseInt(this.dataset.next, 10);
                    showStep(nextStep);
                }
            });
        });

        // Boutons "Retour"
        prevButtons.forEach((btn) => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const prevStep = parseInt(this.dataset.prev, 10);
                showStep(prevStep);
            });
        });

        // Supprimer l'erreur dès que l'utilisateur tape
        form.querySelectorAll('.form-input').forEach((input) => {
            input.addEventListener('input', function () {
                clearFieldError(this);
                if (this.id === 'password') {
                    updatePasswordStrength(this.value);
                }
            });

            // Validation au blur
            input.addEventListener('blur', function () {
                if (this.value.trim()) {
                    validateField(this);
                }
            });
        });

        // Soumission du formulaire
        form.addEventListener('submit', function (e) {
            if (!validateCurrentStep()) {
                e.preventDefault();
                return;
            }

            // Animation de soumission
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
                submitBtn.querySelector('.btn-text').textContent = 'Création en cours...';
            }
        });

        // ==================== TOGGLE PASSWORD ====================

        if (togglePasswordBtn && passwordInput) {
            togglePasswordBtn.addEventListener('click', function () {
                const isPassword = passwordInput.type === 'password';
                passwordInput.type = isPassword ? 'text' : 'password';
                this.classList.toggle('active', isPassword);
                this.setAttribute(
                    'aria-label',
                    isPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'
                );
            });
        }

        // ==================== PASSWORD STRENGTH ====================

        function updatePasswordStrength(value) {
            if (!strengthContainer) return;

            const bars = strengthContainer.querySelectorAll('.strength-bar');
            const label = strengthContainer.querySelector('.strength-label');
            const score = calculatePasswordScore(value);

            // Réinitialiser
            bars.forEach((bar) => {
                bar.className = 'strength-bar';
            });
            label.className = 'strength-label';
            label.textContent = 'Trop court';

            if (value.length === 0) {
                return;
            }

            const levels = ['weak', 'fair', 'good', 'strong'];
            const labels = ['Faible', 'Moyen', 'Bon', 'Excellent'];
            const barClasses = ['active-weak', 'active-fair', 'active-good', 'active-strong'];

            for (let i = 0; i < score; i++) {
                if (bars[i]) {
                    bars[i].classList.add(barClasses[score - 1]);
                }
            }

            if (score > 0) {
                label.classList.add(levels[score - 1]);
                label.textContent = labels[score - 1];
            }
        }

        function calculatePasswordScore(password) {
            if (password.length < 8) return 1; // Faible mais visible

            let score = 1;
            if (password.length >= 8) score = 2;
            if (password.length >= 12) score = 3;
            if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score = Math.max(score, 3);
            if (/\d/.test(password)) score = Math.max(score, 3);
            if (/[^A-Za-z0-9]/.test(password) && password.length >= 12) score = 4;

            return score;
        }

        // ==================== NAVIGATION CLAVIER ====================

        form.addEventListener('keydown', function (e) {
            // Touche Entrée sur les inputs (sauf textarea) -> passer à l'étape suivante
            if (e.key === 'Enter' && e.target.tagName === 'INPUT' && e.target.type !== 'submit') {
                e.preventDefault();
                if (validateCurrentStep()) {
                    if (currentStep < totalSteps) {
                        const nextBtn = form.querySelector(
                            `.form-step[data-step="${currentStep}"] [data-action="next"]`
                        );
                        if (nextBtn) nextBtn.click();
                    } else {
                        form.submit();
                    }
                }
            }
        });

        // ==================== INITIAL STATE ====================

        updateStepper();
        // Focus initial sur le premier champ
        const firstInput = form.querySelector('.form-step.active input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    });
})();
