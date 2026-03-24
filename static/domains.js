// Domains Learning System - Frontend Logic

let allDomains = [];
let selectedDomain = null;
let selectedLevel = null;
let currentQuizData = null;

function hasServerRenderedDomains() {
  return !!document.querySelector('#domains-grid .domain-card');
}

function getInitialDomainsFallback() {
  if (!Array.isArray(window.__INITIAL_DOMAINS__)) {
    return [];
  }
  return window.__INITIAL_DOMAINS__;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  await loadDomains();
  initializeEventListeners();
});

async function loadDomains() {
  try {
    const response = await fetch('/api/domains');
    if (!response.ok) {
      throw new Error(`Failed to fetch domains (HTTP ${response.status})`);
    }

    const data = await response.json();
    allDomains = data.domains || [];

    if (!allDomains.length) {
      allDomains = getInitialDomainsFallback();
    }
    
    // Update domain counts
    const countElement = document.getElementById('domains-count');
    const totalCountElement = document.getElementById('total-domains-count');
    if (countElement) countElement.textContent = allDomains.length;
    if (totalCountElement) totalCountElement.textContent = allDomains.length;
    
    console.log(`Loaded ${allDomains.length} domains`);

    if (!allDomains.length && hasServerRenderedDomains()) {
      return;
    }

    renderDomains(allDomains);
  } catch (error) {
    console.error('Error loading domains:', error);
    allDomains = getInitialDomainsFallback();

    if (!allDomains.length && hasServerRenderedDomains()) {
      return;
    }

    renderDomains(allDomains);
  }
}

function renderDomains(domains) {
  const grid = document.getElementById('domains-grid');
  const emptyState = document.getElementById('empty-state');
  const searchInput = document.getElementById('domain-search');
  const searchTerm = (searchInput?.value || '').trim();

  if (!domains || domains.length === 0) {
    // Keep already-rendered cards visible if no active search term.
    if (!searchTerm && hasServerRenderedDomains()) {
      emptyState.style.display = 'none';
      return;
    }

    grid.innerHTML = '';
    emptyState.style.display = 'flex';
    return;
  }

  emptyState.style.display = 'none';
  grid.innerHTML = domains.map(domain => `
    <div class="course-card domain-card" data-domain-id="${domain.id}">
      <div class="course-thumbnail">
        <span class="domain-icon-large">${domain.icon}</span>
        <span class="course-badge">Domain</span>
      </div>
      <div class="course-content">
        <div class="course-header">
          <span class="course-category">Domain</span>
          <h3 class="course-title">${domain.name}</h3>
        </div>
        <p class="course-description">${domain.description}</p>
        <div class="course-footer domain-footer">
          <div class="course-rating">
            <span class="stars">
              <i class="fa-solid fa-star"></i>
              <i class="fa-solid fa-star"></i>
              <i class="fa-solid fa-star"></i>
              <i class="fa-solid fa-star"></i>
              <i class="fa-solid fa-star-half-stroke"></i>
            </span>
            <span class="rating-value">4.8</span>
            <span class="rating-count">(120)</span>
          </div>
          <button class="course-action-btn btn-start">
            <i class="fa-solid fa-play"></i> Start
          </button>
        </div>
      </div>
    </div>
  `).join('');

  // Add click listeners
  grid.querySelectorAll('.domain-card').forEach(card => {
    card.querySelector('.btn-start').addEventListener('click', () => {
      const domainId = card.getAttribute('data-domain-id');
      const domain = domains.find(d => d.id == domainId);
      openLevelModal(domain);
    });
  });
}

function initializeEventListeners() {
  const grid = document.getElementById('domains-grid');
  if (grid) {
    grid.addEventListener('click', (e) => {
      const startBtn = e.target.closest('.btn-start');
      if (!startBtn) return;

      const card = e.target.closest('.domain-card');
      if (!card) return;

      const domainId = Number(card.getAttribute('data-domain-id'));
      if (!allDomains.length) {
        allDomains = getInitialDomainsFallback();
      }

      const domain = allDomains.find(d => Number(d.id) === domainId);
      if (domain) {
        openLevelModal(domain);
      }
    });
  }

  // Search
  const searchInput = document.getElementById('domain-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      const filtered = allDomains.filter(d => 
        (d.name || '').toLowerCase().includes(term) ||
        (d.description || '').toLowerCase().includes(term) ||
        (d.keywords || '').toLowerCase().includes(term)
      );
      renderDomains(filtered);
    });
  }

  // Level Modal
  const levelModal = document.getElementById('level-modal');
  const levelClose = document.getElementById('level-close');
  const levelCancel = document.getElementById('level-cancel');
  const levelConfirm = document.getElementById('level-confirm');
  const levelCards = document.getElementById('level-cards');

  if (levelClose) levelClose.addEventListener('click', closeLevelModal);
  if (levelCancel) levelCancel.addEventListener('click', closeLevelModal);
  
  if (levelCards) {
    levelCards.querySelectorAll('.level-card').forEach(card => {
      card.addEventListener('click', () => {
        levelCards.querySelectorAll('.level-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedLevel = card.getAttribute('data-level');
        console.log('DEBUG: Selected level:', selectedLevel);
        if (levelConfirm) levelConfirm.disabled = false;
      });
    });
  }

  if (levelConfirm) {
    levelConfirm.addEventListener('click', proceedToAssessment);
  }

  if (levelModal) {
    levelModal.addEventListener('click', (e) => {
      if (e.target === levelModal) closeLevelModal();
    });
  }

  // Assessment Modal
  const assessmentModal = document.getElementById('assessment-modal');
  const assessmentClose = document.getElementById('assessment-close');
  const assessmentBack = document.getElementById('assessment-back');
  const assessmentSubmit = document.getElementById('assessment-submit');

  if (assessmentClose) assessmentClose.addEventListener('click', closeAssessmentModal);
  if (assessmentBack) assessmentBack.addEventListener('click', () => {
    closeAssessmentModal();
    if (selectedDomain) {
      openLevelModal(selectedDomain);
    }
  });
  if (assessmentSubmit) assessmentSubmit.addEventListener('click', submitAssessment);

  if (assessmentModal) {
    assessmentModal.addEventListener('click', (e) => {
      if (e.target === assessmentModal) closeAssessmentModal();
    });
  }

  // Results Modal
  const resultsModal = document.getElementById('results-modal');
  const resultsClose = document.getElementById('results-close');
  const resultsRestart = document.getElementById('results-restart');
  const resultsStart = document.getElementById('results-start');

  if (resultsClose) resultsClose.addEventListener('click', closeResultsModal);
  if (resultsRestart) resultsRestart.addEventListener('click', closeResultsModal);
  if (resultsStart) resultsStart.addEventListener('click', startLearning);

  if (resultsModal) {
    resultsModal.addEventListener('click', (e) => {
      if (e.target === resultsModal) closeResultsModal();
    });
  }
}

function openLevelModal(domain) {
  selectedDomain = domain;
  selectedLevel = null;
  document.getElementById('modal-domain-name').textContent = domain.name;
  
  const levelCards = document.getElementById('level-cards');
  levelCards.querySelectorAll('.level-card').forEach(card => card.classList.remove('selected'));
  
  const levelConfirm = document.getElementById('level-confirm');
  if (levelConfirm) levelConfirm.disabled = true;
  
  const modal = document.getElementById('level-modal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
}

function closeLevelModal() {
  const modal = document.getElementById('level-modal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  selectedLevel = null;
}

async function proceedToAssessment() {
  if (!selectedDomain || !selectedLevel) {
    console.error('DEBUG: Missing domain or level', { selectedDomain, selectedLevel });
    return;
  }

  // Save level before closing modal (which clears selectedLevel)
  const levelToEnroll = selectedLevel;
  const domainToEnroll = selectedDomain;
  
  console.log('DEBUG: Proceeding to assessment with level:', levelToEnroll);
  closeLevelModal();

  // Enroll in domain
  try {
    console.log('DEBUG: Enrolling with:', { level: levelToEnroll });
    const enrollResponse = await fetch(`/api/domain/${domainToEnroll.id}/enroll`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level: levelToEnroll })
    });

    if (!enrollResponse.ok) {
      const enrollError = await enrollResponse.json().catch(() => ({}));
      const enrollMessage = enrollError.error || 'Enrollment failed';
      throw new Error(enrollMessage);
    }

    // Get assessment
    const assessmentResponse = await fetch(`/api/domain/${domainToEnroll.id}/level-quiz`);
    if (!assessmentResponse.ok) {
      const assessmentError = await assessmentResponse.json().catch(() => ({}));
      const assessmentMessage = assessmentError.error || 'Unable to load assessment';
      throw new Error(assessmentMessage);
    }

    const assessmentData = await assessmentResponse.json();
    currentQuizData = assessmentData;

    renderAssessment(assessmentData);
    openAssessmentModal();
  } catch (error) {
    console.error('Error:', error);
    alert(error.message || 'Something went wrong. Please try again.');
  }
}

function renderAssessment(assessmentData) {
  const container = document.getElementById('assessment-container');
  
  // Update modal title based on type
  const titleElement = document.querySelector('#assessment-modal .modal-header h3');
  if (titleElement) {
    titleElement.textContent = assessmentData.title;
  }
  
  const descElement = document.querySelector('#assessment-modal .modal-header p');
  if (descElement) {
    descElement.textContent = assessmentData.description;
  }
  
  container.innerHTML = assessmentData.questions.map((q, idx) => `
    <div class="assessment-question-block">
      <h5>${q.id}. ${q.question}</h5>
      <div class="assessment-options">
        ${q.options.map(opt => `
          <label class="assessment-option">
            <input type="radio" name="q${idx}" value="${opt.value}">
            <span>${opt.label}</span>
          </label>
        `).join('')}
      </div>
    </div>
  `).join('');

  // Add change listeners
  container.querySelectorAll('input[type="radio"]').forEach(input => {
    input.addEventListener('change', () => {
      const totalAnswered = container.querySelectorAll('input[type="radio"]:checked').length;
      const assessmentSubmit = document.getElementById('assessment-submit');
      if (assessmentSubmit) assessmentSubmit.disabled = totalAnswered < assessmentData.questions.length;
    });
  });
}

function openAssessmentModal() {
  const modal = document.getElementById('assessment-modal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
}

function closeAssessmentModal() {
  const modal = document.getElementById('assessment-modal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
}

async function submitAssessment() {
  if (!selectedDomain || !currentQuizData) {
    alert('Error: Domain or quiz data missing');
    return;
  }

  const container = document.getElementById('assessment-container');
  const answers = [];
  
  container.querySelectorAll('input[type="radio"]:checked').forEach(input => {
    answers.push({
      value: input.value
    });
  });

  // Validate all questions answered
  if (answers.length !== currentQuizData.questions.length) {
    alert(`Please answer all ${currentQuizData.questions.length} questions before submitting`);
    return;
  }

  console.log('Submitting assessment with answers:', answers);
  console.log('Domain ID:', selectedDomain.id);

  try {
    const response = await fetch(`/api/domain/${selectedDomain.id}/submit-level-quiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });

    console.log('Response status:', response.status);
    console.log('Response ok:', response.ok);

    if (!response.ok) {
      const submitError = await response.json().catch(() => ({ error: 'Unknown error' }));
      console.error('Server error:', submitError);
      throw new Error(submitError.error || `HTTP Error ${response.status}`);
    }

    const result = await response.json();
    console.log('Assessment result:', result);

    if (result.success || result.assessed_level) {
      closeAssessmentModal();
      displayResults(result);
      openResultsModal();
    } else {
      throw new Error('No success flag in response');
    }
  } catch (error) {
    console.error('Error submitting assessment:', error);
    alert('Error: ' + (error.message || 'Unable to submit assessment'));
  }
}

function displayResults(result) {
  const resultContainer = document.getElementById('assessment-result');
  resultContainer.innerHTML = `
    <div class="result-header">
      <h4>Assessment Complete!</h4>
      <p>Your assessed level: <strong>${result.assessed_level}</strong></p>
      <p>Based on your assessment, we've curated the top 10 courses for your learning journey (including both free and paid options).</p>
    </div>
  `;

  const coursesContainer = document.getElementById('top-courses');
  coursesContainer.innerHTML = '<h5 style="margin-bottom: 16px;">Top 10 Courses (Free & Paid)</h5>' + 
    result.top_courses.map((course, idx) => {
      const isFree = course.price === 'Free' || !course.price;
      const priceClass = isFree ? 'price-free' : 'price-paid';
      const priceIcon = isFree ? '✓' : '$';
      return `
      <div class="course-link-card">
        <div class="course-rank">#${idx + 1}</div>
        <div class="course-info">
          <h6>${course.title}</h6>
          <div class="course-meta">
            <span class="source-badge">${course.source}</span>
            <span class="rating">⭐ ${course.rating}</span>
            <span class="price-badge ${priceClass}">
              <span class="price-icon">${priceIcon}</span>
              ${course.price || 'Free'}
            </span>
          </div>
        </div>
        <a href="${course.url}" target="_blank" class="course-link-btn">
          <i class="fa-solid fa-arrow-up-right-from-square"></i>
        </a>
      </div>
    `}).join('');
}

function openResultsModal() {
  const modal = document.getElementById('results-modal');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
}

function closeResultsModal() {
  const modal = document.getElementById('results-modal');
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  location.reload();
}

function startLearning() {
  if (selectedDomain) {
    window.location.href = `/dashboard?domain=${selectedDomain.id}`;
  }
}
