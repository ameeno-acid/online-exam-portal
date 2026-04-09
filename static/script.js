let currentRole = 'student'; // 'student' or 'admin'
let currentAction = 'login'; // 'login' or 'register'

function switchRole(role) {
    if (currentRole === role) return;
    
    currentRole = role;
    const roleToggle = document.querySelector('.role-toggle');
    const body = document.body;
    
    // Update toggle UI
    roleToggle.setAttribute('data-role', role);
    document.getElementById('btn-student').classList.remove('active');
    document.getElementById('btn-admin').classList.remove('active');
    document.getElementById(`btn-${role}`).classList.add('active');

    if (role === 'admin') {
        body.classList.add('admin-mode');
        updateUI('Admin Login', 'Secure access for administrators.', 'form-admin-login');
    } else {
        body.classList.remove('admin-mode');
        if (currentAction === 'login') {
            updateUI('Student Login', 'Welcome back! Please enter your details.', 'form-student-login');
        } else {
            updateUI('Student Sign Up', 'Create an account to access exams.', 'form-student-register');
        }
    }
}

function switchAction(action) {
    if (currentAction === action) return; 
    
    currentAction = action;
    
    if (currentRole === 'admin') {
        if (action === 'admin-register') {
            updateUI('Admin Sign Up', 'Create a new administrative account.', 'form-admin-register');
        } else {
            updateUI('Admin Login', 'Secure access for administrators.', 'form-admin-login');
        }
    } else {
        if (action === 'register') {
            updateUI('Student Sign Up', 'Create an account to access exams.', 'form-student-register');
        } else {
            updateUI('Student Login', 'Welcome back! Please enter your details.', 'form-student-login');
        }
    }
}

function updateUI(title, subtitle, formId) {
    // Update texts with fade effect
    const titleEl = document.getElementById('auth-title');
    const subtitleEl = document.getElementById('auth-subtitle');
    
    titleEl.style.opacity = '0';
    subtitleEl.style.opacity = '0';
    
    setTimeout(() => {
        titleEl.textContent = title;
        subtitleEl.textContent = subtitle;
        titleEl.style.opacity = '1';
        subtitleEl.style.opacity = '1';
    }, 200);

    // Switch forms
    document.querySelectorAll('.form').forEach(form => {
        form.classList.remove('active-form');
        form.classList.add('hidden-form');
    });
    
    const activeForm = document.getElementById(formId);
    activeForm.classList.remove('hidden-form');
    activeForm.classList.add('active-form');
}

// Button loading simulation
function startLoading(btn) {
    btn.classList.add('loading');
    setTimeout(() => {
        btn.classList.remove('loading');
    }, 5000); // 5 seconds or until response
}

function stopLoading(btn) {
    btn.classList.remove('loading');
}

document.addEventListener('DOMContentLoaded', () => {
    // Student Register
    document.getElementById('form-student-register').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        
        startLoading(btn);
        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();
            if (res.ok) {
                alert('Registration successful! Please login.');
                switchAction('login');
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred. Please try again.');
        } finally {
            stopLoading(btn);
        }
    });

    // Student Login
    document.getElementById('form-student-login').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const email = document.getElementById('student-email').value;
        const password = document.getElementById('student-password').value;
        
        startLoading(btn);
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, role: 'student' })
            });
            const data = await res.json();
            if (res.ok) {
                window.location.href = data.redirect;
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred. Please try again.');
        } finally {
            stopLoading(btn);
        }
    });

    // Admin Login
    document.getElementById('form-admin-login').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const email = document.getElementById('admin-login-email').value;
        const password = document.getElementById('admin-login-password').value;
        
        startLoading(btn);
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, role: 'admin' })
            });
            const data = await res.json();
            if (res.ok) {
                window.location.href = data.redirect;
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred. Please try again.');
        } finally {
            stopLoading(btn);
        }
    });

    // Admin Register
    document.getElementById('form-admin-register').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const name = document.getElementById('reg-admin-name').value;
        const email = document.getElementById('reg-admin-email').value;
        const password = document.getElementById('reg-admin-password').value;
        
        startLoading(btn);
        try {
            const res = await fetch('/api/admin/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();
            if (res.ok) {
                alert('Registration successful! Please login.');
                switchAction('login');
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert('An error occurred. Please try again.');
        } finally {
            stopLoading(btn);
        }
    });
});
