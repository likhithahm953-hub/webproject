// ===== Professional Dashboard JavaScript =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initSidebar();
    initThemeToggle();
    initTabs();
    initNotifications();
    initProfileMenu();
    initNavigation();
    renderDashboardContent();
    animateCounters();
});

// Sidebar Toggle
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    
    if (toggle) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            // Save state to localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }
    
    // Restore sidebar state
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }
}

// Theme Toggle
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const root = document.documentElement;
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        body.classList.add('light');
        root.classList.add('light');
        themeToggle?.setAttribute('aria-pressed', 'true');
    } else if (savedTheme === 'auto') {
        const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
        body.classList.toggle('light', prefersLight);
        root.classList.toggle('light', prefersLight);
    }
    
    themeToggle?.addEventListener('click', function() {
        const isLight = body.classList.toggle('light');
        root.classList.toggle('light', isLight);
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        this.setAttribute('aria-pressed', isLight);
        
        // Add rotation animation
        this.style.transform = 'rotate(360deg)';
        setTimeout(() => {
            this.style.transform = '';
        }, 300);
    });
}

// Tab System
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetId = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and panels
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked tab and target panel
            this.classList.add('active');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add('active');
                
                // Trigger animation
                targetPanel.style.animation = 'none';
                setTimeout(() => {
                    targetPanel.style.animation = '';
                }, 10);
            }
        });
    });
}

// Notifications
function initNotifications() {
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationPopup = document.getElementById('notification-popup');
    const closeBtn = document.getElementById('close-notifications');
    const badge = document.querySelector('.notification-btn .badge');

    // Hide badge if notifications already viewed
    const seenKey = 'notificationsSeen';
    if (localStorage.getItem(seenKey) === 'true' && badge) {
        badge.style.display = 'none';
    }
    
    notificationBtn?.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationPopup.classList.toggle('show');

        if (notificationPopup.classList.contains('show')) {
            localStorage.setItem(seenKey, 'true');
            if (badge) {
                badge.style.display = 'none';
            }
        }
    });
    
    closeBtn?.addEventListener('click', function() {
        notificationPopup.classList.remove('show');
        localStorage.setItem(seenKey, 'true');
        if (badge) {
            badge.style.display = 'none';
        }
    });
    
    // Close on outside click
    document.addEventListener('click', function(e) {
        if (!notificationPopup.contains(e.target) && !notificationBtn.contains(e.target)) {
            notificationPopup.classList.remove('show');
        }
    });
}

// Profile Menu
function initProfileMenu() {
    const profileAvatar = document.getElementById('profile-avatar');
    const dropdown = document.getElementById('profile-dropdown');
    
    if (profileAvatar && dropdown) {
        profileAvatar.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.style.opacity = dropdown.style.opacity === '1' ? '0' : '1';
            dropdown.style.visibility = dropdown.style.visibility === 'visible' ? 'hidden' : 'visible';
        });
    }
}

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item[data-section]');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active from all
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active to clicked
            this.classList.add('active');
            
            const section = this.getAttribute('data-section');
            console.log('Navigating to:', section);
            
            // You can add logic here to show/hide different sections
        });
    });
}

// Animate Counters
function animateCounters() {
    const counters = document.querySelectorAll('.card-content h3');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        if (isNaN(target)) return;
        
        const duration = 1500;
        const increment = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        // Start animation when element is visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// Render Dashboard Content
function renderDashboardContent() {
    loadDashboardStats();
    renderDomains();
    renderChallenges();
    renderRecommendations();
    renderActivity();
}

// Load actual dashboard statistics from API
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/user/dashboard-stats');
        if (!response.ok) {
            console.error('Failed to load dashboard stats');
            return;
        }
        
        const data = await response.json();
        
        // Update the stat cards with real data
        const domainsElement = document.getElementById('courses-enrolled');
        const challengesElement = document.getElementById('challenges-completed');
        const certsElement = document.getElementById('certs-earned');
        const aiRecsElement = document.getElementById('ai-recs');
        
        if (domainsElement) domainsElement.textContent = data.domains_enrolled;
        if (challengesElement) challengesElement.textContent = data.challenges_completed;
        if (certsElement) certsElement.textContent = data.certificates_earned;
        if (aiRecsElement) aiRecsElement.textContent = data.ai_recommendations;
        
        // Update domains trend (this month)
        const domainsCard = document.querySelector('[data-stat="domains"]');
        if (domainsCard) {
            const trendSpan = domainsCard.querySelector('.trend span');
            if (trendSpan) {
                trendSpan.textContent = `${data.domains_this_month} this month`;
            }
        }
        
        // Update challenges progress bar and percentage
        const challengesCard = document.querySelector('[data-stat="challenges"]');
        if (challengesCard) {
            const progressBar = challengesCard.querySelector('.mini-progress-bar');
            if (progressBar) {
                progressBar.style.width = `${data.completion_percent}%`;
            }
            const trendSpan = challengesCard.querySelector('.trend');
            if (trendSpan) {
                trendSpan.textContent = `${data.completion_percent}% completion`;
            }
        }
        
        // Re-animate counters with new values
        animateCounters();
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Mock Data
const mockData = {
    domains: [
        {
            id: 1,
            title: 'Python Programming',
            thumb: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=400&h=300&fit=crop',
            progress: 72,
            duration: '12 weeks',
            topics: 48,
            badge: 'In Progress'
        },
        {
            id: 2,
            title: 'Data Science',
            thumb: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=300&fit=crop',
            progress: 44,
            duration: '10 weeks',
            topics: 36,
            badge: 'In Progress'
        },
        {
            id: 3,
            title: 'Machine Learning',
            thumb: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400&h=300&fit=crop',
            progress: 21,
            duration: '8 weeks',
            topics: 28,
            badge: 'New'
        }
    ],
    challenges: [
        {
            id: 1,
            title: 'Array Algorithms Challenge',
            description: 'Master sorting, searching, and manipulation of arrays with real-world problems.',
            difficulty: 'medium',
            due: '2d 3h',
            icon: 'fa-code'
        },
        {
            id: 2,
            title: 'REST API Development',
            description: 'Build a complete REST API with authentication and database integration.',
            difficulty: 'hard',
            due: '5d 1h',
            icon: 'fa-server'
        },
        {
            id: 3,
            title: 'CSS Layout Mastery',
            description: 'Create responsive layouts using Flexbox and Grid.',
            difficulty: 'easy',
            due: '1d 12h',
            icon: 'fa-palette'
        }
    ],
    recommendations: [
        {
            id: 1,
            title: 'Deep Learning Specialization',
            description: 'Advanced neural networks and deep learning techniques',
            icon: 'fa-brain',
            match: '95%'
        },
        {
            id: 2,
            title: 'Web Development Mastery',
            description: 'Complete web development from frontend to backend',
            icon: 'fa-globe',
            match: '88%'
        },
        {
            id: 3,
            title: 'Cloud Architecture Path',
            description: 'Learn AWS, Azure, and cloud-native development',
            icon: 'fa-cloud',
            match: '82%'
        }
    ],
    activity: [
        {
            type: 'course',
            title: 'Completed lesson: "Advanced Python Functions"',
            time: '2 hours ago',
            icon: 'fa-book'
        },
        {
            type: 'challenge',
            title: 'Started challenge: "Array Algorithms"',
            time: '5 hours ago',
            icon: 'fa-bolt'
        },
        {
            type: 'certificate',
            title: 'Earned certificate in "Python Basics"',
            time: '1 day ago',
            icon: 'fa-trophy'
        },
        {
            type: 'domain',
            title: 'Enrolled in "Machine Learning" domain',
            time: '2 days ago',
            icon: 'fa-graduation-cap'
        }
    ]
};

// Render Domains - Fetch real data from API
async function renderDomains() {
    const grid = document.getElementById('courses-grid');
    if (!grid) return;
    
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; opacity: 0.7;"><i class="fa-solid fa-spinner fa-spin"></i> Loading domains...</div>';
    
    try {
        const response = await fetch('/api/user/enrolled-domains');
        if (!response.ok) {
            console.error('Failed to load enrolled domains');
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; opacity: 0.7;">No domains enrolled yet</div>';
            return;
        }
        
        const data = await response.json();
        const domains = data.domains || [];
        
        grid.innerHTML = '';
        
        if (domains.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; opacity: 0.7;"><p>No domains enrolled yet. <a href="/domains">Browse domains</a></p></div>';
            return;
        }
        
        domains.forEach(domain => {
            const card = document.createElement('div');
            card.className = 'course-card';
            
            // Get domain thumbnail (using placeholder with domain initial)
            const initial = domain.domain_name.charAt(0).toUpperCase();
            const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];
            const colorIndex = domain.domain_id % colors.length;
            const bgColor = colors[colorIndex];
            
            // Get badge based on progress
            let badge = 'In Progress';
            if (domain.progress >= 100) {
                badge = 'Complete';
            } else if (domain.progress === 0) {
                badge = 'Just Started';
            }
            
            // Build course info - if course link exists, use it
            const courseTitle = domain.course_link 
                ? domain.course_link.title 
                : 'Select a course to start';
            const courseDuration = '12 weeks'; // Default, should come from course link
            const courseTopics = 48; // Default, should come from course link
            
            card.innerHTML = `
                <div class="course-thumb" style="background: linear-gradient(135deg, ${bgColor}, ${bgColor}cc); display: flex; align-items: center; justify-content: center; font-size: 3rem; font-weight: bold; color: white;">
                    ${initial}
                </div>
                <div class="course-content">
                    <h3 class="course-title">${domain.domain_name}</h3>
                    <div class="course-meta">
                        <span><i class="fa-solid fa-clock"></i> ${courseDuration}</span>
                        <span><i class="fa-solid fa-book-open"></i> ~${courseTopics} topics</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-label">
                            <span>Progress</span>
                            <span>${domain.progress}%</span>
                        </div>
                        <div class="progress-bar-wrapper">
                            <div class="progress-bar" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="course-actions">
                        <a href="/domain/${domain.domain_id}/learn" class="btn-capsule primary">
                            <i class="fa-solid fa-play"></i> Continue
                        </a>
                        <a href="/domain/${domain.domain_id}" class="btn-capsule">
                            <i class="fa-solid fa-info-circle"></i> Details
                        </a>
                    </div>
                </div>
            `;
            
            grid.appendChild(card);
            
            // Animate progress bar
            setTimeout(() => {
                const progressBar = card.querySelector('.progress-bar');
                progressBar.style.width = domain.progress + '%';
            }, 100);
        });
    } catch (error) {
        console.error('Error rendering domains:', error);
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; opacity: 0.7; color: #ef4444;"><p>Error loading domains</p></div>';
    }
}

// Render Challenges
function renderChallenges() {
    const grid = document.getElementById('challenges-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    mockData.challenges.forEach(challenge => {
        const card = document.createElement('div');
        card.className = 'challenge-card';
        card.innerHTML = `
            <div class="challenge-header">
                <div class="challenge-icon">
                    <i class="fa-solid ${challenge.icon}"></i>
                </div>
                <span class="challenge-difficulty ${challenge.difficulty}">${challenge.difficulty}</span>
            </div>
            <h3 class="challenge-title">${challenge.title}</h3>
            <p class="challenge-desc">${challenge.description}</p>
            <div class="challenge-timer">
                <i class="fa-solid fa-hourglass-half"></i>
                <span>Due in ${challenge.due}</span>
            </div>
            <a href="#" class="btn-capsule primary">
                <i class="fa-solid fa-rocket"></i> Start Now
            </a>
        `;
        grid.appendChild(card);
    });
}

// Render Recommendations
function renderRecommendations() {
    const grid = document.getElementById('recs-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    mockData.recommendations.forEach(rec => {
        const card = document.createElement('div');
        card.className = 'course-card';
        card.innerHTML = `
            <div class="course-content" style="padding: 32px 20px;">
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                    <div class="challenge-icon" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));">
                        <i class="fa-solid ${rec.icon}" style="color: #8b5cf6;"></i>
                    </div>
                    <div>
                        <h3 class="course-title" style="margin: 0;">${rec.title}</h3>
                        <span style="color: var(--success); font-size: 0.85rem; font-weight: 600;">
                            <i class="fa-solid fa-check-circle"></i> ${rec.match} match
                        </span>
                    </div>
                </div>
                <p style="color: var(--text-secondary); margin-bottom: 20px; line-height: 1.6;">
                    ${rec.description}
                </p>
                <a href="#" class="btn-capsule primary" style="width: 100%;">
                    <i class="fa-solid fa-compass"></i> Explore Path
                </a>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Render Activity Feed
function renderActivity() {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    
    feed.innerHTML = '';
    
    mockData.activity.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.innerHTML = `
            <div class="activity-icon ${activity.type}">
                <i class="fa-solid ${activity.icon}"></i>
            </div>
            <div class="activity-content">
                <p class="activity-title">${activity.title}</p>
                <span class="activity-time">${activity.time}</span>
            </div>
        `;
        feed.appendChild(item);
    });
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add hover effects with particles (optional enhancement)
function addParticleEffect(element) {
    element.addEventListener('mouseenter', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.3), transparent);
            transform: translate(-50%, -50%) scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
}

// Apply particle effects to cards
document.querySelectorAll('.stat-card, .course-card, .challenge-card').forEach(card => {
    addParticleEffect(card);
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: translate(-50%, -50%) scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

console.log('🎨 Dashboard initialized successfully!');
