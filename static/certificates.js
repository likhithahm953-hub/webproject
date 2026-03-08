// Certificates Page JavaScript

let certificatesData = [];

// Skills data
const skillsData = [
  { name: "Python", level: "Expert", progress: 95, certificates: 3 },
  { name: "JavaScript", level: "Advanced", progress: 88, certificates: 2 },
  { name: "SQL", level: "Advanced", progress: 85, certificates: 2 },
  { name: "React", level: "Intermediate", progress: 75, certificates: 1 },
  { name: "Machine Learning", level: "Intermediate", progress: 70, certificates: 1 },
  { name: "AWS", level: "Intermediate", progress: 72, certificates: 1 }
];

// Badges data
const badgesData = [
  { name: "Early Adopter", icon: "🚀", date: "Jan 2024" },
  { name: "Fast Learner", icon: "⚡", date: "Mar 2024" },
  { name: "Code Master", icon: "👨‍💻", date: "May 2024" },
  { name: "Team Player", icon: "🤝", date: "Jun 2024" },
  { name: "Problem Solver", icon: "🧩", date: "Jul 2024" },
  { name: "Top Performer", icon: "🏆", date: "Sep 2024" },
  { name: "Innovator", icon: "💡", date: "Oct 2024" },
  { name: "Mentor", icon: "🎓", date: "Dec 2024" }
];

// Initialize certificates page
document.addEventListener('DOMContentLoaded', function() {
  loadCertificates();
  renderSkills();
  renderBadges();
  applyStreakStatus();
  initShareButton();
});

function applyStreakStatus() {
  const streakBadge = document.querySelector('.badge-item.streak');

  if (!streakBadge) return;

  const missedDays = Number(streakBadge.dataset.streakMissed || '0');
  streakBadge.classList.remove('streak-warn', 'streak-bad');

  if (missedDays <= 0) return;

  if (missedDays === 1) {
    streakBadge.classList.add('streak-warn');
  } else {
    streakBadge.classList.add('streak-bad');
  }
}

async function loadCertificates() {
  try {
    const response = await fetch('/api/certificates');
    if (!response.ok) {
      throw new Error('Failed to load certificates');
    }
    const data = await response.json();
    certificatesData = data.certificates || [];
  } catch (error) {
    console.error('Error loading certificates:', error);
    certificatesData = [];
  }

  renderCertificates();
  updateSummaryStats();
}

// Render certificates
function renderCertificates() {
  const certificatesGrid = document.querySelector('.certificates-grid');
  
  if (!certificatesGrid) return;
  
  certificatesGrid.innerHTML = certificatesData.map(cert => createCertificateCard(cert)).join('');
  
  // Add download handlers
  document.querySelectorAll('.cert-download-btn').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      downloadCertificate(certificatesData[index]);
    });
  });
  
  // Add share handlers
  document.querySelectorAll('.cert-share-btn').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      shareCertificate(certificatesData[index]);
    });
  });
  
  // Add view handlers
  document.querySelectorAll('.cert-view-btn').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      viewCertificate(certificatesData[index]);
    });
  });
}

// Create certificate card HTML
function createCertificateCard(cert) {
  return `
    <div class="certificate-card">
      <div class="certificate-preview">
        <div class="certificate-header">
          <div class="certificate-badge">${cert.icon}</div>
          <h3 class="certificate-title-preview">${cert.title}</h3>
          <p class="certificate-date">Issued ${cert.date}</p>
          ${cert.isSample ? '<span class="certificate-sample">Sample</span>' : ''}
        </div>
        <div class="certificate-id">ID: ${cert.certificateId}</div>
      </div>
      <div class="certificate-details">
        <h4 class="certificate-course">${cert.domain}</h4>
        <p class="certificate-course-sub">${cert.course_title}</p>
        <div class="certificate-issuer">
          <i class="fa-solid fa-building"></i>
          <span>${cert.issuer}</span>
        </div>
        <div class="certificate-stats">
          <div class="cert-stat">
            <span class="cert-stat-label">Grade</span>
            <span class="cert-stat-value">${cert.grade}</span>
          </div>
          <div class="cert-stat">
            <span class="cert-stat-label">Score</span>
            <span class="cert-stat-value">${cert.score}%</span>
          </div>
          <div class="cert-stat">
            <span class="cert-stat-label">Duration</span>
            <span class="cert-stat-value">${cert.duration}</span>
          </div>
        </div>
        <div class="certificate-actions">
          <button class="cert-action-btn cert-view-btn primary">
            <i class="fa-solid fa-eye"></i>
            View
          </button>
          <button class="cert-action-btn cert-download-btn">
            <i class="fa-solid fa-download"></i>
            Download
          </button>
          <button class="cert-action-btn cert-share-btn">
            <i class="fa-solid fa-share-nodes"></i>
            Share
          </button>
        </div>
      </div>
    </div>
  `;
}

// Render skills
function renderSkills() {
  const skillsGrid = document.querySelector('.skills-grid');
  
  if (!skillsGrid) return;
  
  skillsGrid.innerHTML = skillsData.map(skill => `
    <div class="skill-card">
      <div class="skill-header">
        <span class="skill-name">${skill.name}</span>
        <span class="skill-level">${skill.level}</span>
      </div>
      <div class="skill-progress">
        <div class="skill-progress-bar">
          <div class="skill-progress-fill" style="width: ${skill.progress}%"></div>
        </div>
      </div>
      <div class="skill-certificates">
        <i class="fa-solid fa-certificate"></i>
        <span>${skill.certificates} certificate${skill.certificates !== 1 ? 's' : ''}</span>
      </div>
    </div>
  `).join('');
  
  // Animate progress bars
  setTimeout(() => {
    document.querySelectorAll('.skill-progress-fill').forEach(fill => {
      fill.style.width = fill.style.width;
    });
  }, 100);
}

// Render badges
function renderBadges() {
  const badgesContainer = document.querySelector('.badges-container');
  
  if (!badgesContainer) return;
  
  badgesContainer.innerHTML = badgesData.map(badge => `
    <div class="badge-item">
      <div class="badge-icon">${badge.icon}</div>
      <span class="badge-name">${badge.name}</span>
      <span class="badge-date">${badge.date}</span>
    </div>
  `).join('');
}

// Update summary stats
function updateSummaryStats() {
  const totalCerts = certificatesData.length;
  const avgScore = Math.round(certificatesData.reduce((sum, c) => sum + c.score, 0) / totalCerts);
  
  // Top 15% is mock data
  const statValues = document.querySelectorAll('.summary-stat-value');
  if (statValues.length >= 2) {
    animateValue(statValues[0], 0, totalCerts, 1000);
    statValues[1].textContent = '15%';
  }
}

// Animate counter
function animateValue(element, start, end, duration) {
  const range = end - start;
  const increment = range / (duration / 16);
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    if (current >= end) {
      element.textContent = Math.round(end);
      clearInterval(timer);
    } else {
      element.textContent = Math.round(current);
    }
  }, 16);
}

// Download certificate
function downloadCertificate(cert) {
  if (!cert || !cert.id) {
    showToast('Unable to download certificate.');
    return;
  }

  const certLabel = cert.course_title || cert.domain || 'this certificate';
  showToast(`Downloading certificate for ${certLabel}...`);

  // Trigger the Flask download route using an anchor for better browser compatibility.
  const link = document.createElement('a');
  link.href = `${window.location.origin}/certificates/${encodeURIComponent(cert.id)}/download`;
  link.target = '_blank';
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// Share certificate
function shareCertificate(cert) {
  if (navigator.share) {
    navigator.share({
      title: `${cert.title} - ${cert.course}`,
      text: `I just earned a certificate in ${cert.course}!`,
      url: window.location.href
    }).then(() => {
      showToast('Certificate shared successfully!');
    }).catch(() => {
      copyShareLink(cert);
    });
  } else {
    copyShareLink(cert);
  }
}

// Copy share link
function copyShareLink(cert) {
  const link = `${window.location.origin}/certificates/${cert.id}`;
  navigator.clipboard.writeText(link).then(() => {
    showToast('Certificate link copied to clipboard!');
  });
}

// View certificate
function viewCertificate(cert) {
  // In a real app, this would open a modal or new page with the full certificate
  window.open(`/certificates/${cert.id}/view`, '_blank');
}

// Share profile button
function initShareButton() {
  const shareBtn = document.querySelector('.share-profile-btn');
  
  if (shareBtn) {
    shareBtn.addEventListener('click', function() {
      if (navigator.share) {
        navigator.share({
          title: 'My SkillForge Profile',
          text: 'Check out my learning achievements!',
          url: window.location.origin + '/profile'
        }).then(() => {
          showToast('Profile shared successfully!');
        }).catch(() => {
          copyProfileLink();
        });
      } else {
        copyProfileLink();
      }
    });
  }
}

// Copy profile link
function copyProfileLink() {
  const link = `${window.location.origin}/profile`;
  navigator.clipboard.writeText(link).then(() => {
    showToast('Profile link copied to clipboard!');
  });
}

// Toast notification
function showToast(message) {
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }
  
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.innerHTML = `
    <i class="fa-solid fa-check-circle"></i>
    <span>${message}</span>
  `;
  
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add('show'), 10);
  
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
