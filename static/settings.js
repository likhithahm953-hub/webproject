// Settings Page JavaScript

// Modal functions
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    // Reset form
    const form = modal.querySelector('form');
    if (form) form.reset();
  }
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal')) {
    e.target.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
});

// Initialize settings page
document.addEventListener('DOMContentLoaded', function() {
  applySavedTheme();
  initSettingsCategories();
  initThemeOptions();
  initColorPicker();
  initToggleSwitches();
  initCopyButton();
  initAccountForms();
});

function applySavedTheme() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  const root = document.documentElement;
  const body = document.body;
  const themeToggle = document.getElementById('theme-toggle');
  const themeOptions = document.querySelectorAll('.theme-option');

  let isLight = false;
  if (savedTheme === 'light') {
    isLight = true;
  } else if (savedTheme === 'auto') {
    isLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
  }

  body.classList.toggle('light', isLight);
  root.classList.toggle('light', isLight);

  themeOptions.forEach(opt => opt.classList.remove('active'));
  const activeOption = Array.from(themeOptions).find(opt => opt.getAttribute('data-theme') === savedTheme);
  if (activeOption) activeOption.classList.add('active');

  if (themeToggle) themeToggle.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
}

// Initialize account update forms
function initAccountForms() {
  // Change Email Form
  const emailForm = document.getElementById('changeEmailForm');
  if (emailForm) {
    emailForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      
      try {
        const response = await fetch('/update-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            newEmail: formData.get('newEmail'),
            password: formData.get('password')
          })
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showToast(data.message || 'Email updated successfully', 'success');
          closeModal('changeEmailModal');
          setTimeout(() => window.location.reload(), 1500);
        } else {
          showToast(data.error || 'Failed to update email', 'error');
        }
      } catch (error) {
        showToast('An error occurred. Please try again.', 'error');
      }
    });
  }
  
  // Change Password Form
  const passwordForm = document.getElementById('changePasswordForm');
  if (passwordForm) {
    passwordForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const newPassword = formData.get('newPassword');
      const confirmPassword = formData.get('confirmPassword');
      
      if (newPassword !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
      }
      
      try {
        const response = await fetch('/update-password', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            currentPassword: formData.get('currentPassword'),
            newPassword: newPassword
          })
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showToast(data.message || 'Password updated successfully', 'success');
          closeModal('changePasswordModal');
        } else {
          showToast(data.error || 'Failed to update password', 'error');
        }
      } catch (error) {
        showToast('An error occurred. Please try again.', 'error');
      }
    });
  }
  
  // Change Username Form
  const usernameForm = document.getElementById('changeUsernameForm');
  if (usernameForm) {
    usernameForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      
      try {
        const response = await fetch('/update-username', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            newUsername: formData.get('newUsername'),
            password: formData.get('password')
          })
        });
        
        const data = await response.json();
        
        if (response.ok) {
          showToast(data.message || 'Username updated successfully', 'success');
          closeModal('changeUsernameModal');
          setTimeout(() => window.location.reload(), 1500);
        } else {
          showToast(data.error || 'Failed to update username', 'error');
        }
      } catch (error) {
        showToast('An error occurred. Please try again.', 'error');
      }
    });
  }
}

// Toast notification
function showToast(message, type = 'info') {
  // Remove existing toast
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }
  
  const toast = document.createElement('div');
  toast.className = `toast-notification toast-${type}`;
  toast.innerHTML = `
    <i class="fa-solid fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.classList.add('show'), 100);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Settings category navigation
function initSettingsCategories() {
  const categories = document.querySelectorAll('.settings-category');
  const sections = document.querySelectorAll('.settings-section');
  
  categories.forEach(category => {
    category.addEventListener('click', function() {
      const targetCategory = this.getAttribute('data-category');
      
      // Update active category
      categories.forEach(cat => cat.classList.remove('active'));
      this.classList.add('active');
      
      // Show corresponding section
      sections.forEach(section => section.classList.remove('active'));
      const targetSection = document.getElementById(targetCategory + '-section');
      if (targetSection) {
        targetSection.classList.add('active');
      }
    });
  });
}

// Theme options
function initThemeOptions() {
  const themeOptions = document.querySelectorAll('.theme-option');
  const themeToggle = document.getElementById('theme-toggle');
  const root = document.documentElement;
  const body = document.body;
  
  themeOptions.forEach(option => {
    option.addEventListener('click', function() {
      const theme = this.getAttribute('data-theme');
      
      // Update active state
      themeOptions.forEach(opt => opt.classList.remove('active'));
      this.classList.add('active');
      
      // Apply theme
      if (theme === 'dark') {
        body.classList.remove('light');
        root.classList.remove('light');
        localStorage.setItem('theme', 'dark');
        if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
      } else if (theme === 'light') {
        body.classList.add('light');
        root.classList.add('light');
        localStorage.setItem('theme', 'light');
        if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
      } else if (theme === 'auto') {
        // Auto theme based on system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
          body.classList.remove('light');
          root.classList.remove('light');
          if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
        } else {
          body.classList.add('light');
          root.classList.add('light');
          if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
        }
        localStorage.setItem('theme', 'auto');
      }
      
      showToast('Theme updated successfully');
    });
  });
}

// Color picker
function initColorPicker() {
  const colorOptions = document.querySelectorAll('.color-option');
  
  colorOptions.forEach(option => {
    option.addEventListener('click', function() {
      const color = this.style.background;
      
      // Update active state
      colorOptions.forEach(opt => opt.classList.remove('active'));
      this.classList.add('active');
      
      // Apply accent color (would need CSS variable update)
      document.documentElement.style.setProperty('--accent-primary', color);
      localStorage.setItem('accentColor', color);
      
      showToast('Accent color updated');
    });
  });
}

// Toggle switches
function initToggleSwitches() {
  const toggles = document.querySelectorAll('.toggle-switch input[type="checkbox"]');
  
  toggles.forEach(toggle => {
    toggle.addEventListener('change', function() {
      const label = this.closest('.settings-group').querySelector('.settings-label').textContent;
      
      if (this.checked) {
        showToast(`${label} enabled`);
      } else {
        showToast(`${label} disabled`);
      }
    });
  });
}

// Copy API key button
function initCopyButton() {
  const copyBtn = document.querySelector('.copy-btn');
  
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      const apiKeyInput = document.querySelector('.api-key-box input');
      
      if (apiKeyInput) {
        apiKeyInput.select();
        document.execCommand('copy');
        
        // Update button
        this.innerHTML = '<i class="fa-solid fa-check"></i>';
        showToast('API key copied to clipboard');
        
        setTimeout(() => {
          this.innerHTML = '<i class="fa-solid fa-copy"></i>';
        }, 2000);
      }
    });
  }
}

// Toast notification
function showToast(message) {
  // Remove existing toast
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }
  
  // Create toast
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.innerHTML = `
    <i class="fa-solid fa-check-circle"></i>
    <span>${message}</span>
  `;
  
  document.body.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Session revoke buttons
document.querySelectorAll('.session-revoke').forEach(btn => {
  btn.addEventListener('click', function() {
    if (this.textContent === 'Current') {
      showToast('Cannot revoke current session');
    } else {
      const sessionItem = this.closest('.session-item');
      sessionItem.style.opacity = '0.5';
      this.textContent = 'Revoking...';
      
      setTimeout(() => {
        sessionItem.remove();
        showToast('Session revoked successfully');
      }, 1000);
    }
  });
});

// Delete account button
const deleteAccountBtn = document.querySelector('.settings-btn-danger');
if (deleteAccountBtn) {
  deleteAccountBtn.addEventListener('click', function() {
    const confirmed = confirm('Are you sure you want to delete your account? This action cannot be undone.');
    if (confirmed) {
      showToast('Account deletion initiated. Check your email for confirmation.');
    }
  });
}

// Update username button
const updateUsernameBtn = document.querySelector('.settings-group .settings-btn-primary');
if (updateUsernameBtn) {
  updateUsernameBtn.addEventListener('click', function() {
    const usernameInput = this.previousElementSibling;
    const newUsername = usernameInput.value;
    
    if (newUsername && newUsername.length >= 3) {
      this.textContent = 'Updating...';
      
      setTimeout(() => {
        this.textContent = 'Update Username';
        showToast('Username updated successfully');
      }, 1000);
    } else {
      showToast('Username must be at least 3 characters');
    }
  });
}

// Download invoice buttons
document.querySelectorAll('.download-invoice').forEach(btn => {
  btn.addEventListener('click', function() {
    showToast('Invoice download started');
  });
});

// Export data button
const exportDataBtn = document.querySelector('.settings-group .settings-btn-primary:last-child');
if (exportDataBtn && exportDataBtn.textContent.includes('Export')) {
  exportDataBtn.addEventListener('click', function() {
    this.textContent = 'Preparing export...';
    
    setTimeout(() => {
      this.textContent = 'Export Data';
      showToast('Data export ready for download');
    }, 2000);
  });
}

// Integration connect buttons
document.querySelectorAll('.integration-item .settings-btn-primary').forEach(btn => {
  btn.addEventListener('click', function() {
    const integrationName = this.closest('.integration-item').querySelector('h4').textContent;
    
    this.textContent = 'Connecting...';
    
    setTimeout(() => {
      this.textContent = 'Connected';
      this.classList.add('connected');
      this.style.background = 'rgba(16, 185, 129, 0.1)';
      this.style.color = '#10b981';
      showToast(`${integrationName} connected successfully`);
    }, 1500);
  });
});
