// ===== Profile Page JavaScript =====

document.addEventListener('DOMContentLoaded', function() {
    initProfileTabs();
    initAvatarUpload();
    initSimpleAvatarUpload();
    initThemeSelector();
    initToggleSwitches();
    initNotificationEnhancements();
});

// Profile Settings Tabs
function initProfileTabs() {
    const tabs = document.querySelectorAll('.settings-tab');
    const panels = document.querySelectorAll('.settings-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetId = this.getAttribute('data-tab');
            
            // Remove active from all
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

// Avatar Upload Preview
function initAvatarUpload() {
    const avatarInput = document.getElementById('avatar-input');
    const editOverlay = document.getElementById('avatar-edit-overlay');
    const editTrigger = document.getElementById('avatar-edit-trigger');
    const editMenu = document.getElementById('avatar-edit-menu');
    const cancelMenuBtn = document.getElementById('cancel-menu-btn');
    const removeAvatarBtn = document.getElementById('remove-avatar-btn');
    const uploadSubmitBtn = document.getElementById('upload-submit-btn');
    const avatarForm = document.getElementById('avatar-form-section');
    
    // Show/hide edit menu
    if (editTrigger) {
        editTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            if (editMenu) {
                editMenu.classList.toggle('active');
            }
        });
    }

    if (editOverlay) {
        editOverlay.addEventListener('click', function(e) {
            e.preventDefault();
            if (editMenu) {
                editMenu.classList.toggle('active');
            }
        });
    }

    // Cancel menu
    if (cancelMenuBtn) {
        cancelMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (editMenu) {
                editMenu.classList.remove('active');
            }
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (editMenu && !editMenu.contains(e.target) && !editOverlay.contains(e.target)) {
            editMenu.classList.remove('active');
        }
    });

    // Avatar file input change handler
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    // Preview in current-avatar
                    const currentAvatar = document.getElementById('avatar-display');
                    if (currentAvatar) {
                        currentAvatar.innerHTML = `<img src="${event.target.result}" alt="avatar" />`;
                    }
                    
                    // Show upload button
                    if (uploadSubmitBtn) {
                        uploadSubmitBtn.style.display = 'block';
                    }
                    
                    // Close menu
                    if (editMenu) {
                        editMenu.classList.remove('active');
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Remove avatar handler
    if (removeAvatarBtn) {
        removeAvatarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to remove your profile picture?')) {
                // Create a form to send delete request
                const deleteForm = document.createElement('form');
                deleteForm.method = 'POST';
                deleteForm.action = '/api/remove-avatar';
                document.body.appendChild(deleteForm);
                deleteForm.submit();
            }
        });
    }
}

// Header Avatar Simple Upload
function initSimpleAvatarUpload() {
    const mainCameraBtn = document.getElementById('main-camera-btn');
    const mainEditMenu = document.getElementById('main-edit-menu');
    const mainAvatarInput = document.getElementById('main-avatar-input');
    const mainCancelBtn = document.getElementById('main-cancel-btn');
    const mainRemoveBtn = document.getElementById('main-remove-btn');
    const mainAvatarForm = document.getElementById('main-avatar-form');
    const mainAvatarDisplay = document.getElementById('main-avatar-display');
    const avatarLightbox = document.getElementById('avatar-lightbox');
    
    // Toggle menu when clicking camera button
    if (mainCameraBtn) {
        mainCameraBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            if (mainEditMenu) {
                mainEditMenu.classList.toggle('active');
            }
        });
    }

    // Close menu when clicking cancel
    if (mainCancelBtn) {
        mainCancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (mainEditMenu) {
                mainEditMenu.classList.remove('active');
            }
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (mainEditMenu && !mainEditMenu.contains(e.target) && !mainCameraBtn.contains(e.target)) {
            mainEditMenu.classList.remove('active');
        }
    });

    // Handle file selection
    if (mainAvatarInput) {
        mainAvatarInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                if (mainAvatarForm) {
                    mainAvatarForm.submit();
                }
            }
        });
    }

    // Handle remove photo
    if (mainRemoveBtn) {
        mainRemoveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to remove your profile picture?')) {
                const deleteForm = document.createElement('form');
                deleteForm.method = 'POST';
                deleteForm.action = '/api/remove-avatar';
                document.body.appendChild(deleteForm);
                deleteForm.submit();
            }
        });
    }

    // Show lightbox when clicking on avatar image (only if actual image exists)
    if (mainAvatarDisplay) {
        mainAvatarDisplay.addEventListener('click', function(e) {
            // Don't open lightbox if clicking on camera button
            // Only open lightbox if there's an actual image (not just initials)
            const hasImage = mainAvatarDisplay.tagName === 'IMG' || mainAvatarDisplay.querySelector('img');
            if (!e.target.closest('.profile-edit-btn') && !e.target.closest('button') && hasImage) {
                if (avatarLightbox) {
                    avatarLightbox.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
            }
        });
    }

    // Close lightbox when clicking on background
    if (avatarLightbox) {
        avatarLightbox.addEventListener('click', function(e) {
            if (e.target === avatarLightbox) {
                avatarLightbox.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
}

// Theme Selector
function initThemeSelector() {
    const themeOptions = document.querySelectorAll('.theme-option');
    
    themeOptions.forEach(option => {
        option.addEventListener('click', function() {
            const theme = this.getAttribute('data-theme');
            
            // Remove active from all
            themeOptions.forEach(opt => opt.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            
            // Apply theme
            const body = document.body;
            const root = document.documentElement;
            if (theme === 'light') {
                body.classList.add('light');
                root.classList.add('light');
                localStorage.setItem('theme', 'light');
            } else if (theme === 'dark') {
                body.classList.remove('light');
                root.classList.remove('light');
                localStorage.setItem('theme', 'dark');
            } else {
                // Auto mode - check system preference
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (prefersDark) {
                    body.classList.remove('light');
                    root.classList.remove('light');
                } else {
                    body.classList.add('light');
                    root.classList.add('light');
                }
                localStorage.setItem('theme', 'auto');
            }
        });
    });
}

// Toggle Switches
function initToggleSwitches() {
    const toggles = document.querySelectorAll('.toggle-switch input');
    
    toggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const parentItem = this.closest('.notification-item, .privacy-item');
            if (parentItem) {
                const title = parentItem.querySelector('h4').textContent;
                const isChecked = this.checked;
                
                // Show toast notification
                showToast(`${title}: ${isChecked ? 'Enabled' : 'Disabled'}`, isChecked ? 'success' : 'info');
                
                // Save preference (you can add API call here)
                console.log(`Toggle ${title}: ${isChecked}`);
            }
        });
    });
}

// Enhanced Notifications
function initNotificationEnhancements() {
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationPopup = document.getElementById('notification-popup');
    const closeBtn = document.getElementById('close-notifications');
    const markAllReadBtn = document.getElementById('mark-all-read');
    const notificationList = document.getElementById('notification-list');
    
    // Load notifications
    loadNotifications();
    
    // Toggle popup
    notificationBtn?.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationPopup.classList.toggle('show');
    });
    
    // Close popup
    closeBtn?.addEventListener('click', function() {
        notificationPopup.classList.remove('show');
    });
    
    // Mark all as read
    markAllReadBtn?.addEventListener('click', function() {
        const unreadItems = notificationList.querySelectorAll('.notification-item.unread');
        unreadItems.forEach(item => {
            item.classList.remove('unread');
        });
        
        // Update badge
        updateNotificationBadge(0);
        showToast('All notifications marked as read', 'success');
    });
    
    // Close on outside click
    document.addEventListener('click', function(e) {
        if (!notificationPopup.contains(e.target) && !notificationBtn.contains(e.target)) {
            notificationPopup.classList.remove('show');
        }
    });
}

// Load Notifications
function loadNotifications() {
    const notificationList = document.getElementById('notification-list');
    if (!notificationList) return;
    
    const notifications = [
        {
            id: 1,
            icon: 'fa-trophy',
            title: 'You earned a certificate!',
            message: 'Congratulations on completing "Python Basics"',
            time: '2 hours ago',
            unread: true,
            type: 'achievement'
        },
        {
            id: 2,
            icon: 'fa-bolt',
            title: 'New challenge available',
            message: 'Try the "Array Algorithms" challenge',
            time: '5 hours ago',
            unread: true,
            type: 'challenge'
        },
        {
            id: 3,
            icon: 'fa-robot',
            title: 'AI recommendations ready',
            message: '3 new learning paths recommended for you',
            time: '1 day ago',
            unread: true,
            type: 'ai'
        },
        {
            id: 4,
            icon: 'fa-graduation-cap',
            title: 'New lesson added',
            message: 'Check out the new lesson in "Web Development"',
            time: '2 days ago',
            unread: false,
            type: 'course'
        },
        {
            id: 5,
            icon: 'fa-star',
            title: 'Achievement unlocked',
            message: 'You\'ve completed 10 challenges!',
            time: '3 days ago',
            unread: false,
            type: 'achievement'
        }
    ];
    
    notificationList.innerHTML = '';
    
    notifications.forEach(notif => {
        const item = document.createElement('div');
        item.className = `notification-item ${notif.unread ? 'unread' : ''}`;
        item.dataset.notificationId = notif.id;
        
        item.innerHTML = `
            <i class="fa-solid ${notif.icon}"></i>
            <div class="notification-content">
                <p><strong>${notif.title}</strong><br>${notif.message}</p>
                <span class="time">${notif.time}</span>
            </div>
            <button class="btn-icon-small mark-read-btn" title="Mark as read">
                <i class="fa-solid fa-check"></i>
            </button>
        `;
        
        notificationList.appendChild(item);
        
        // Add click handler to mark as read
        const markReadBtn = item.querySelector('.mark-read-btn');
        markReadBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            item.classList.remove('unread');
            updateNotificationBadge();
            showToast('Notification marked as read', 'success');
        });
        
        // Click on notification item
        item.addEventListener('click', function() {
            this.classList.remove('unread');
            updateNotificationBadge();
            
            // Navigate based on type
            switch(notif.type) {
                case 'course':
                    window.location.href = '/courses';
                    break;
                case 'challenge':
                    window.location.href = '/challenges';
                    break;
                case 'achievement':
                case 'certificate':
                    window.location.href = '/certificates';
                    break;
                case 'ai':
                    window.location.href = '/ai-guidance';
                    break;
            }
        });
    });
    
    // Update badge count
    updateNotificationBadge();
}

// Update Notification Badge
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-btn .badge');
    if (!badge) return;
    
    if (count === undefined) {
        // Count unread notifications
        count = document.querySelectorAll('.notification-item.unread').length;
    }
    
    badge.textContent = count;
    badge.style.display = count > 0 ? 'block' : 'none';
}

// Toast Notification System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fa-solid ${getToastIcon(type)}"></i>
        <span>${message}</span>
    `;
    
    // Add styles if not already present
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: var(--bg-card);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 16px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
                z-index: 10000;
                animation: slideInRight 0.3s ease;
                min-width: 280px;
            }
            .toast-success {
                border-left: 4px solid var(--success);
            }
            .toast-info {
                border-left: 4px solid var(--accent-primary);
            }
            .toast-warning {
                border-left: 4px solid var(--warning);
            }
            .toast-error {
                border-left: 4px solid var(--danger);
            }
            .toast i {
                font-size: 1.2rem;
            }
            .toast-success i { color: var(--success); }
            .toast-info i { color: var(--accent-primary); }
            .toast-warning i { color: var(--warning); }
            .toast-error i { color: var(--danger); }
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    switch(type) {
        case 'success': return 'fa-circle-check';
        case 'error': return 'fa-circle-exclamation';
        case 'warning': return 'fa-triangle-exclamation';
        default: return 'fa-circle-info';
    }
}

// Form Submission Handlers
const forms = document.querySelectorAll('.settings-form');
forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Simulate form submission
        const formName = this.closest('.settings-section').querySelector('.section-title').textContent;
        showToast(`${formName} updated successfully!`, 'success');
        
        // Here you would normally send data to server
        console.log('Form submitted:', new FormData(this));
    });
});

// Device revoke buttons
document.querySelectorAll('.activity-entry .btn-icon').forEach(btn => {
    btn.addEventListener('click', function() {
        const entry = this.closest('.activity-entry');
        const deviceName = entry.querySelector('h4').textContent;
        
        if (confirm(`Are you sure you want to revoke access for ${deviceName}?`)) {
            entry.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => entry.remove(), 300);
            showToast(`Device "${deviceName}" revoked successfully`, 'success');
        }
    });
});

// 2FA Enable button
document.querySelector('.security-feature .btn-capsule')?.addEventListener('click', function() {
    showToast('2FA setup will be implemented soon!', 'info');
    // Here you would open a modal with 2FA setup instructions
});

// Delete Account button
document.querySelector('[style*="danger"]')?.addEventListener('click', function() {
    if (confirm('Are you absolutely sure you want to delete your account? This action cannot be undone.')) {
        if (confirm('Please confirm again: DELETE MY ACCOUNT PERMANENTLY')) {
            showToast('Account deletion initiated. You will receive a confirmation email.', 'warning');
            // API call to initiate account deletion
        }
    }
});

// Download Data button
document.querySelector('.data-actions .btn-capsule:first-child')?.addEventListener('click', function() {
    showToast('Preparing your data export... This may take a few minutes.', 'info');
    // API call to generate data export
    setTimeout(() => {
        showToast('Your data is ready for download!', 'success');
    }, 3000);
});

console.log('✅ Profile page initialized successfully!');
