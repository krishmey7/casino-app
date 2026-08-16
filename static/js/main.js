// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    
    if (mobileMenuBtn && mobileMenuOverlay) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            mobileMenuOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (mobileMenuClose) {
        mobileMenuClose.addEventListener('click', function() {
            mobileMenuOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function(e) {
            if (e.target === mobileMenuOverlay) {
                mobileMenuOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
    
    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenuOverlay && mobileMenuOverlay.classList.contains('active')) {
            mobileMenuOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });

    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.animation = 'slideDown 0.3s ease-out reverse';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // fetch and update wallet balance elements
    async function fetchAndUpdateBalances() {
        try {
            const resp = await fetch('/wallet/', {credentials:'same-origin'});
            if (!resp.ok) return;
            const data = await resp.json();
            if (data && data.balance !== undefined) {
                document.querySelectorAll('[data-wallet-balance]').forEach(el => {
                    const prev = el.textContent && el.textContent.trim();
                    const newVal = String(data.balance);
                    el.textContent = newVal;
                    // animate badge if value changed
                    const badge = el.closest('.balance-badge');
                    if (badge && prev && prev !== newVal) {
                        const prevNum = Number(prev.replace(',','.'));
                        const newNum = Number(newVal.replace(',','.'));
                        // remove previous state classes
                        badge.classList.remove('balance-updated','balance-gain','balance-loss');
                        // force reflow to restart animation
                        void badge.offsetWidth;
                        if (!isNaN(prevNum) && !isNaN(newNum)) {
                            if (newNum > prevNum) {
                                badge.classList.add('balance-gain');
                            } else if (newNum < prevNum) {
                                badge.classList.add('balance-loss');
                            }
                        }
                        badge.classList.add('balance-updated');
                        // ensure classes removed after animation
                        setTimeout(()=> badge.classList.remove('balance-updated','balance-gain','balance-loss'), 1200);
                    }
                });
                const balanceId = document.getElementById('balance');
                if (balanceId) {
                    const prev = balanceId.textContent && balanceId.textContent.trim();
                    balanceId.textContent = data.balance;
                    if (prev && prev !== String(data.balance)) {
                        const badge = document.getElementById('header-balance')?.closest('.balance-badge');
                        if (badge) {
                            badge.classList.remove('balance-updated');
                            void badge.offsetWidth;
                            badge.classList.add('balance-updated');
                            setTimeout(()=> badge.classList.remove('balance-updated'), 950);
                        }
                    }
                }
            }
        } catch (e) {
            // silent fail
        }
    }

    // expose legacy name used in templates
    window.fetchBalance = fetchAndUpdateBalances;
    window.fetchAndUpdateBalances = fetchAndUpdateBalances;

    // Toast helper
    window.showToast = function(type, message, timeout = 4500) {
        try {
            let container = document.querySelector('.toast-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }

            const toast = document.createElement('div');
            toast.className = 'toast toast-' + (type || 'info');
            toast.setAttribute('role', 'status');
            toast.setAttribute('aria-live', 'polite');

            const icon = document.createElement('span');
            icon.className = 'icon';
            icon.innerHTML = (type === 'success') ? '✅' : (type === 'error') ? '⚠️' : 'ℹ️';

            const text = document.createElement('div');
            text.textContent = message;

            toast.appendChild(icon);
            toast.appendChild(text);
            container.appendChild(toast);

            setTimeout(()=>{
                // fade out then remove
                toast.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-6px) scale(0.98)';
                setTimeout(()=> toast.remove(), 300);
            }, timeout);
        } catch (e) {
            // ignore errors
            console.warn('showToast failed', e);
        }
    };

    // call once on load
    fetchAndUpdateBalances();
});

