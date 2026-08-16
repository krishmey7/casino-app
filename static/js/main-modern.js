/**
 * Casino Platform - Main JavaScript
 * Modern Mobile-First Interactive Features
 */

// ==================== DOCUMENT READY ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeAuth();
    initializeMessages();
    initializeNavigation();
    initializeFormValidation();
    initializeScrollBehavior();
    initializeAnimations();
}

// ==================== AUTHENTICATION ====================
function initializeAuth() {
    // Form submission feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.6';
            }
        });
    });

    // Password toggle visibility
    const toggleButtons = document.querySelectorAll('.toggle-password');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.closest('.form-input-wrapper').querySelector('input[type="password"], input[type="text"]');
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
                this.classList.toggle('active');
            }
        });
    });
}

// ==================== MESSAGES ====================
function initializeMessages() {
    const messages = document.querySelectorAll('.auth-message, .message');
    messages.forEach((msg, index) => {
        // Auto-dismiss success messages after 5 seconds
        if (msg.classList.contains('success') || msg.classList.contains('auth-message-success')) {
            setTimeout(() => {
                dismissMessage(msg);
            }, 5000);
        }

        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'message-close';
        closeBtn.innerHTML = '×';
        closeBtn.addEventListener('click', () => dismissMessage(msg));
        msg.appendChild(closeBtn);
    });
}

function dismissMessage(msg) {
    msg.style.animation = 'slideInUp 0.3s ease reverse';
    setTimeout(() => {
        msg.remove();
    }, 300);
}

// ==================== NAVIGATION ====================
function initializeNavigation() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobileMenuClose = document.getElementById('mobileMenuClose');

    if (mobileMenuBtn && mobileMenuOverlay) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenuOverlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });

        mobileMenuClose?.addEventListener('click', closeMobileMenu);
        mobileMenuOverlay.addEventListener('click', (e) => {
            if (e.target === mobileMenuOverlay) {
                closeMobileMenu();
            }
        });
    }

    function closeMobileMenu() {
        if (mobileMenuOverlay) {
            mobileMenuOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    // Close mobile menu on link click
    const mobileMenuLinks = document.querySelectorAll('.mobile-menu-item');
    mobileMenuLinks.forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });
}

// ==================== FORM VALIDATION ====================
function initializeFormValidation() {
    const forms = document.querySelectorAll('.auth-form, form[novalidate]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');
        
        inputs.forEach(input => {
            // Validate on blur
            input.addEventListener('blur', function() {
                validateInput(this);
            });

            // Real-time validation for email
            if (this.type === 'email') {
                this.addEventListener('input', function() {
                    validateEmail(this);
                });
            }

            // Real-time validation for passwords
            if (this.type === 'password' && this.name === 'password') {
                this.addEventListener('input', function() {
                    validatePassword(this);
                });
            }
        });

        // Form submission validation
        form.addEventListener('submit', function(e) {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

function validateInput(input) {
    let isValid = true;

    if (input.hasAttribute('required') && !input.value.trim()) {
        markInvalid(input, 'Ce champ est requis');
        isValid = false;
    } else if (input.type === 'email' && input.value) {
        if (!isValidEmail(input.value)) {
            markInvalid(input, 'Email invalide');
            isValid = false;
        } else {
            markValid(input);
        }
    } else if (input.type === 'password' && input.name === 'password' && input.value) {
        const strength = checkPasswordStrength(input.value);
        if (strength.score < 2) {
            markInvalid(input, 'Le mot de passe est trop faible');
            isValid = false;
        } else {
            markValid(input);
        }
    } else if (input.value.trim()) {
        markValid(input);
    }

    return isValid;
}

function validateEmail(input) {
    if (isValidEmail(input.value)) {
        markValid(input);
    } else if (input.value.trim()) {
        markInvalid(input, 'Email invalide');
    }
}

function validatePassword(input) {
    const strength = checkPasswordStrength(input.value);
    const hint = input.closest('.form-group')?.querySelector('.field-hint');
    
    if (hint) {
        hint.style.color = strength.color;
        hint.textContent = strength.message;
    }
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function checkPasswordStrength(password) {
    let score = 0;
    let message = '';
    let color = 'var(--text-light)';

    if (password.length >= 8) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z\d]/.test(password)) score++;

    if (score <= 2) {
        message = '🔴 Mot de passe faible';
        color = '#ef4444';
    } else if (score <= 3) {
        message = '🟡 Mot de passe moyen';
        color = 'var(--gold)';
    } else {
        message = '🟢 Mot de passe fort';
        color = '#22c55e';
    }

    return { score, message, color };
}

function markValid(input) {
    input.classList.remove('input-error');
    input.classList.add('input-valid');
    const error = input.closest('.form-group')?.querySelector('.input-error-msg');
    if (error) error.remove();
}

function markInvalid(input, message) {
    input.classList.remove('input-valid');
    input.classList.add('input-error');
    
    let error = input.closest('.form-group')?.querySelector('.input-error-msg');
    if (!error) {
        error = document.createElement('div');
        error.className = 'input-error-msg';
        input.closest('.form-group')?.appendChild(error);
    }
    error.textContent = message;
}

// ==================== SCROLL BEHAVIOR ====================
function initializeScrollBehavior() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href)?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Navbar hide on scroll down, show on scroll up
    let lastScrollTop = 0;
    const navbar = document.querySelector('.main-header');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY;
        
        if (navbar) {
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            lastScrollTop = scrollTop;
        }
    }, { passive: true });
}

// ==================== ANIMATIONS ====================
function initializeAnimations() {
    // Intersection Observer for lazy animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'slideInUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Animate cards and elements
    document.querySelectorAll('.game-grid-card, .info-block, .testimonial-card').forEach(el => {
        observer.observe(el);
    });
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Format currency display
 */
function formatCurrency(amount, currency = 'CDF') {
    return new Intl.NumberFormat('fr-CD', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `notification notification-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInUp 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== EXPORTS FOR MODULES ====================
window.CasinoApp = {
    formatCurrency,
    showNotification,
    debounce,
    validateInput,
    checkPasswordStrength,
    isValidEmail
};
