// Background images: prefer server-injected list `window.landingImages` (from template)
const defaultImages = [
    '/static/bg1.jpeg',
    '/static/bg2.jpeg',
    '/static/bg3.jpeg'
];

let images = (window.landingImages && window.landingImages.length) ? window.landingImages.slice(0,3) : defaultImages.slice();
let currentIndex = 0; 

// Preload images robustly and keep only successfully loaded images
function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => { console.debug('Preloaded background:', src); resolve(src); };
        img.onerror = () => { console.warn('Background failed to load:', src); reject(src); };
        img.src = src;
    });
}

async function prepareImages() {
    const results = await Promise.allSettled(images.map(loadImage));
    const good = results.filter(r => r.status === 'fulfilled').map(r => r.value);
    if (good.length === 0) {
        console.warn('No background images loaded; falling back to default images.');
        images = defaultImages.slice(0,3);
    } else {
        // keep only the first three successful images
        images = good.slice(0,3);
        console.info('Background images set (limited to 3):', images);
    }
}

function changeBackground() {
    const landing = document.querySelector('.landing-page');
    if (!landing) {
        console.debug('Landing element not found, will retry on next interval');
        return;
    }
    // compute the next index but don't change current until transition completes
    const nextIndex = (currentIndex + 1) % images.length;

    // Create a new background layer and fade it in, then remove the old ones
    const newLayer = document.createElement('div');
    newLayer.className = 'bg-layer';
    newLayer.style.backgroundImage = `url('${encodeURI(images[nextIndex])}')`;
    newLayer.style.opacity = '0';
    landing.insertBefore(newLayer, landing.firstChild);
    // force reflow then start fade
    void newLayer.offsetWidth;
    newLayer.style.opacity = '1';
    console.debug('Background changed to:', images[nextIndex]);
    // remove previous bg-layer elements after transition and then update currentIndex
    setTimeout(() => {
        const layers = landing.querySelectorAll('.bg-layer');
        layers.forEach(layer => {
            if (layer !== newLayer) layer.remove();
        });
        currentIndex = nextIndex;
    }, 1100);
}

let rotatorInterval = null;
function startRotator() {
    // set initial background to the first image if the placeholder layer exists
    const landing = document.querySelector('.landing-page');
    if (landing) {
        const initialLayer = landing.querySelector('.bg-layer');
        if (initialLayer && (!initialLayer.style.backgroundImage || initialLayer.style.backgroundImage === '')) {
            initialLayer.style.backgroundImage = `url('${encodeURI(images[0])}')`;
            console.debug('Initial background set to:', images[0]);
            currentIndex = 0;
        }
    }
    // ensure only one interval is running
    if (rotatorInterval) clearInterval(rotatorInterval);
    rotatorInterval = setInterval(changeBackground, 3000);
    // rotation runs every 3 seconds (first change will occur after the first interval)
    console.info('Background rotator initialized (switching every 3s)');
}

// Start rotator only after images are prepared and the DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => { await prepareImages(); startRotator(); });
} else {
    (async () => { await prepareImages(); startRotator(); })();
}
// Gentle smooth scroll + pop-up About section
document.querySelectorAll('.scroll-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        const targetPosition = target.offsetTop;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const duration = 2000; // 2 seconds gentle scroll
            const run = easeInOutQuad(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
            else target.classList.add('visible'); // pop-up effect when reached
        }

        function easeInOutQuad(t, b, c, d) {
            t /= d/2;
            if (t < 1) return c/2*t*t + b;
            t--;
            return -c/2 * (t*(t-2) - 1) + b;
        }

        requestAnimationFrame(animation);
    });
});

// Form enhancements for signup/login pages
document.addEventListener('DOMContentLoaded', function() {
    // Password show/hide toggles with SVG eye icons
    const eyeOpen = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                  + '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>'
                  + '<circle cx="12" cy="12" r="3" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></circle></svg>';
    const eyeClosed = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
                    + '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-6 0-10-7-10-7 1.73-3.04 4.59-5.47 8-6.54" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>'
                    + '<path d="M1 1l22 22" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>';

    document.querySelectorAll('.toggle-password').forEach(btn => {
        // ensure icon is present initially when page loads
        if (!btn.innerHTML.trim()) btn.innerHTML = eyeOpen;
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const el = document.getElementById(targetId);
            if (!el) return;
            const isHidden = el.type === 'password';
            if (isHidden) {
                el.type = 'text';
                this.setAttribute('aria-pressed','true');
                this.setAttribute('aria-label','Hide password');
                this.innerHTML = eyeClosed;
            } else {
                el.type = 'password';
                this.setAttribute('aria-pressed','false');
                this.setAttribute('aria-label','Show password');
                this.innerHTML = eyeOpen;
            }
        });
    });

    // Password strength and email validation (Signup form)
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const strengthBar = document.querySelector('.strength-bar');
        const strengthText = document.querySelector('.strength-text');
        const inlineErrors = document.getElementById('inline-errors');
        const pwInlineErrors = document.getElementById('pw-inline-errors');
        const confirmInlineErrors = document.getElementById('confirm-inline-errors');

        function scorePassword(pw) {
            let score = 0;
            if (pw.length >= 8) score += 1;
            if (/[A-Z]/.test(pw)) score += 1;
            if (/\d/.test(pw)) score += 1;
            if (/[^A-Za-z0-9]/.test(pw)) score += 1;
            return score;
        }

        function getPasswordProblems(pw) {
            const problems = [];
            if (pw.length < 8) problems.push('rule-length');
            if (!/[A-Z]/.test(pw)) problems.push('rule-upper');
            if (!/[a-z]/.test(pw)) problems.push('rule-lower');
            if (!/\d/.test(pw)) problems.push('rule-digit');
            if (!/[^A-Za-z0-9]/.test(pw)) problems.push('rule-symbol');
            return problems;
        }

        function updateStrength(pw) {
            const sc = scorePassword(pw);
            const pct = (sc / 4) * 100;
            if (!strengthBar.firstElementChild) {
                const fill = document.createElement('div');
                fill.style.height = '100%';
                fill.style.width = pct + '%';
                fill.style.background = sc >= 3 ? '#50fa7b' : sc === 2 ? '#ffb86b' : '#ff4d4d';
                fill.style.borderRadius = '6px';
                strengthBar.appendChild(fill);
            } else {
                const fill = strengthBar.firstElementChild;
                fill.style.width = pct + '%';
                fill.style.background = sc >= 3 ? '#50fa7b' : sc === 2 ? '#ffb86b' : '#ff4d4d';
            }
            const txt = sc === 4 ? 'Very strong' : sc === 3 ? 'Good' : sc === 2 ? 'Weak' : 'Very weak';
            strengthText.textContent = txt;
        }

        passwordInput.addEventListener('input', function() {
            updateStrength(this.value);
            // show rule list while typing, update live
            const problems = getPasswordProblems(this.value);
            const rulesBox = document.getElementById('pw-rules');
            // add visible class to animate in
            rulesBox.classList.add('visible');
            ['rule-length','rule-upper','rule-lower','rule-digit','rule-symbol'].forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                el.classList.toggle('valid', !problems.includes(id));
            });
            // hide immediately if all rules satisfied
            if (problems.length === 0) {
                rulesBox.classList.remove('visible');
                // clear any password inline messages as soon as valid
                pwInlineErrors.textContent = '';
            }
            // clear confirm mismatch while typing
            if (confirmInlineErrors) confirmInlineErrors.textContent = '';
        });

        // Show rules as soon as user focuses the password field
        passwordInput.addEventListener('focus', function() {
            const rulesBox = document.getElementById('pw-rules');
            rulesBox.classList.add('visible');
            const problems = getPasswordProblems(this.value);
            ['rule-length','rule-upper','rule-lower','rule-digit','rule-symbol'].forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                const isValid = !problems.includes(id);
                el.classList.toggle('valid', isValid);
                const icon = el.querySelector('.rule-icon');
                if (icon) icon.textContent = isValid ? '✔' : '✖';
            });
        });

        // Hide rules on blur only if password satisfies all rules
        passwordInput.addEventListener('blur', function() {
            const problems = getPasswordProblems(this.value);
            const rulesBox = document.getElementById('pw-rules');
            if (problems.length === 0) {
                // hide immediately on blur if valid
                rulesBox.classList.remove('visible');
            }
        });

        if (emailInput) {
            emailInput.addEventListener('input', function() {
                const re = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;
                const hint = document.getElementById('email-hint');
                if (!hint) return;
                if (!this.value) { hint.textContent = ''; hint.classList.remove('valid','invalid'); }
                else if (re.test(this.value)) { hint.textContent = ''; hint.classList.add('valid'); hint.classList.remove('invalid'); }
                else { hint.textContent = 'Enter a correct email like name@example.com'; hint.classList.add('invalid'); hint.classList.remove('valid'); }
            });
        }

        function validateForm() {
            inlineErrors.textContent = '';
            if (passwordInput.value !== confirmInput.value) {
                // show message right below confirm
                if (confirmInlineErrors) confirmInlineErrors.textContent = 'Passwords do not match.';
                // show rules as well
                document.getElementById('pw-rules').classList.add('visible');
                return false;
            }
            const problems = getPasswordProblems(passwordInput.value);
            if (problems.length) {
                pwInlineErrors.textContent = 'Password requirements missing: ' + problems.join(', ');
                document.getElementById('pw-rules').classList.add('visible');
                ['rule-length','rule-upper','rule-lower','rule-digit','rule-symbol'].forEach(id => {
                    const el = document.getElementById(id);
                    if (!el) return;
                    const isValid = !problems.includes(id);
                    el.classList.toggle('valid', isValid);
                    const icon = el.querySelector('.rule-icon');
                    if (icon) icon.textContent = isValid ? '✔' : '✖';
                });
                return false;
            }
            // clear pw-specific messages when everything OK
            pwInlineErrors.textContent = '';
            if (confirmInlineErrors) confirmInlineErrors.textContent = '';

            const emailOk = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/.test(emailInput.value);
            if (!emailOk) {
                inlineErrors.textContent = 'Enter a correct email like name@example.com';
                return false;
            }
            return true;
        }

        signupForm.addEventListener('submit', function(e) {
            if (!validateForm()) { e.preventDefault(); }
        });
    }

    // Auto-hide flash messages after 5s
    document.querySelectorAll('.flash').forEach(f => { setTimeout(() => { f.style.opacity = '0'; f.style.transition = 'opacity 0.6s'; setTimeout(() => f.remove(), 700); }, 5000); });
});