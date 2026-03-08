// Courses Page JavaScript

let coursesData = [];

// Initialize courses page
document.addEventListener('DOMContentLoaded', function() {
  initFilterTabs();
  initSearchBox();
  initEnrollFlow();
  loadCourses();
});

async function loadCourses() {
  try {
    const response = await fetch('/api/courses');
    const data = await response.json();
    coursesData = data.courses || [];
  } catch (error) {
    coursesData = [];
  }
  renderCourses('all');
  updateStats();
  handleOnboardingAutoOpen();
}

function handleOnboardingAutoOpen() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('onboarding') !== '1') return;
  if (!coursesData.length) return;

  openEnrollModal(coursesData[0]);
  params.delete('onboarding');
  const newQuery = params.toString();
  const newUrl = newQuery ? `${window.location.pathname}?${newQuery}` : window.location.pathname;
  window.history.replaceState({}, document.title, newUrl);
}

let currentEnrollCourse = null;
let selectedDomain = null;
let latestAssessment = null;

const domainOptions = [
  { id: 'ml', label: 'Machine Learning', description: 'Models, data pipelines, and evaluation', icon: '🧠' },
  { id: 'python', label: 'Python', description: 'Core language, automation, and scripting', icon: '🐍' },
  { id: 'flask', label: 'Flask', description: 'APIs, auth, and production-ready apps', icon: '🌶️' },
  { id: 'mern', label: 'Web Development (MERN)', description: 'Full-stack web apps with JS', icon: '🧩' }
];

const domainAssessments = {
  ml: [
    { question: 'How comfortable are you with data preprocessing and feature engineering?', concept: 'Feature engineering', options: [
      { label: 'I am new to this', score: 0 },
      { label: 'I have basic knowledge', score: 2 },
      { label: 'I work with it often', score: 4 }
    ]},
    { question: 'Which best describes your experience with model evaluation?', concept: 'Model evaluation', options: [
      { label: 'I have not evaluated models', score: 0 },
      { label: 'I use basic metrics', score: 2 },
      { label: 'I compare and tune models', score: 4 }
    ]},
    { question: 'How familiar are you with overfitting and regularization?', concept: 'Regularization', options: [
      { label: 'Very new', score: 0 },
      { label: 'I know the idea', score: 2 },
      { label: 'I use it in projects', score: 4 }
    ]},
    { question: 'Can you deploy or serve an ML model?', concept: 'Model deployment', options: [
      { label: 'Not yet', score: 0 },
      { label: 'I have tried once', score: 2 },
      { label: 'Yes, with confidence', score: 4 }
    ]}
  ],
  python: [
    { question: 'How comfortable are you with Python data structures?', concept: 'Data structures', options: [
      { label: 'I am new', score: 0 },
      { label: 'I use lists and dicts', score: 2 },
      { label: 'I use advanced patterns', score: 4 }
    ]},
    { question: 'How often do you write reusable functions and modules?', concept: 'Modular code', options: [
      { label: 'Rarely', score: 0 },
      { label: 'Sometimes', score: 2 },
      { label: 'Regularly', score: 4 }
    ]},
    { question: 'How confident are you with debugging and error handling?', concept: 'Debugging', options: [
      { label: 'Very new', score: 0 },
      { label: 'I can fix simple issues', score: 2 },
      { label: 'I debug complex issues', score: 4 }
    ]},
    { question: 'Have you automated tasks with files or APIs?', concept: 'Automation', options: [
      { label: 'Not yet', score: 0 },
      { label: 'A few scripts', score: 2 },
      { label: 'Yes, multiple projects', score: 4 }
    ]}
  ],
  flask: [
    { question: 'How familiar are you with routing and views in Flask?', concept: 'Routing', options: [
      { label: 'New to Flask', score: 0 },
      { label: 'I can build basic routes', score: 2 },
      { label: 'I build structured apps', score: 4 }
    ]},
    { question: 'How comfortable are you with APIs and JSON responses?', concept: 'API design', options: [
      { label: 'Very new', score: 0 },
      { label: 'I have built simple APIs', score: 2 },
      { label: 'I build robust APIs', score: 4 }
    ]},
    { question: 'How confident are you with auth and security basics?', concept: 'Authentication', options: [
      { label: 'I need guidance', score: 0 },
      { label: 'I know sessions and hashing', score: 2 },
      { label: 'I implement secure flows', score: 4 }
    ]},
    { question: 'Have you used a database with Flask?', concept: 'Database integration', options: [
      { label: 'Not yet', score: 0 },
      { label: 'I have tried SQLite', score: 2 },
      { label: 'Yes, with ORM', score: 4 }
    ]}
  ],
  mern: [
    { question: 'How comfortable are you with modern JavaScript?', concept: 'JavaScript basics', options: [
      { label: 'I am new', score: 0 },
      { label: 'I know the basics', score: 2 },
      { label: 'I build apps', score: 4 }
    ]},
    { question: 'How familiar are you with React components and state?', concept: 'React state', options: [
      { label: 'Very new', score: 0 },
      { label: 'I build simple components', score: 2 },
      { label: 'I build complex UIs', score: 4 }
    ]},
    { question: 'How confident are you with APIs and backend logic?', concept: 'API integration', options: [
      { label: 'Not yet', score: 0 },
      { label: 'I can call APIs', score: 2 },
      { label: 'I build REST APIs', score: 4 }
    ]},
    { question: 'Have you worked with databases like MongoDB?', concept: 'Database modeling', options: [
      { label: 'No', score: 0 },
      { label: 'I have basic experience', score: 2 },
      { label: 'Yes, I design schemas', score: 4 }
    ]}
  ],
  default: [
    { question: 'How comfortable are you with the fundamentals?', concept: 'Fundamentals', options: [
      { label: 'Very new', score: 0 },
      { label: 'I know the basics', score: 2 },
      { label: 'I am confident', score: 4 }
    ]},
    { question: 'Can you build a small project without a tutorial?', concept: 'Project building', options: [
      { label: 'Not yet', score: 0 },
      { label: 'Sometimes', score: 2 },
      { label: 'Yes, regularly', score: 4 }
    ]},
    { question: 'How familiar are you with debugging errors?', concept: 'Debugging', options: [
      { label: 'Very new', score: 0 },
      { label: 'I can fix simple issues', score: 2 },
      { label: 'I can debug confidently', score: 4 }
    ]},
    { question: 'How do you feel about advanced topics?', concept: 'Advanced topics', options: [
      { label: 'I prefer fundamentals first', score: 0 },
      { label: 'I can try some advanced topics', score: 2 },
      { label: 'I am ready for advanced topics', score: 4 }
    ]}
  ]
};

const domainPaths = {
  ml: {
    Beginner: [
      'Python data stack (NumPy, pandas)',
      'Supervised learning fundamentals',
      'Model evaluation + validation',
      'Mini project: Predictive model'
    ],
    Intermediate: [
      'Feature engineering strategies',
      'Model selection + tuning',
      'Intro to MLOps pipelines',
      'Project: Deploy a model API'
    ],
    Expert: [
      'Advanced optimization + interpretability',
      'Production monitoring + drift',
      'Distributed training basics',
      'Capstone: End-to-end ML system'
    ]
  },
  python: {
    Beginner: [
      'Core syntax + data structures',
      'Functions + modules',
      'File handling + APIs',
      'Mini project: Automation script'
    ],
    Intermediate: [
      'OOP + design patterns',
      'Testing + debugging workflows',
      'Performance + async basics',
      'Project: Data processing pipeline'
    ],
    Expert: [
      'Advanced async + concurrency',
      'Packaging + tooling',
      'Architecture for large apps',
      'Capstone: Production-ready app'
    ]
  },
  flask: {
    Beginner: [
      'Flask routing + templates',
      'Forms + validation',
      'Database basics with ORM',
      'Mini project: CRUD app'
    ],
    Intermediate: [
      'REST API design',
      'Auth + security basics',
      'Caching + background jobs',
      'Project: API + dashboard'
    ],
    Expert: [
      'Blueprint architecture',
      'Scalability + performance',
      'Deployment pipelines',
      'Capstone: Multi-tenant platform'
    ]
  },
  mern: {
    Beginner: [
      'JavaScript + React fundamentals',
      'React state + hooks',
      'Node + Express basics',
      'Mini project: Full-stack CRUD'
    ],
    Intermediate: [
      'API integration + auth',
      'State management patterns',
      'Database modeling (MongoDB)',
      'Project: Real-time app'
    ],
    Expert: [
      'Performance optimization',
      'Scalable backend design',
      'CI/CD + deployment',
      'Capstone: SaaS product'
    ]
  }
};

const domainGigs = {
  ml: [
    { title: 'Build a churn prediction model', company: 'RetailSense', level: 'Intermediate' },
    { title: 'Data cleanup pipeline for logs', company: 'LogiAI', level: 'Beginner' },
    { title: 'Deploy inference API', company: 'VisionOps', level: 'Expert' }
  ],
  python: [
    { title: 'Automate weekly reports', company: 'FinanceFlow', level: 'Beginner' },
    { title: 'ETL script for CSV imports', company: 'DataDock', level: 'Intermediate' },
    { title: 'Build CLI productivity tool', company: 'OpsForge', level: 'Expert' }
  ],
  flask: [
    { title: 'Create REST API for inventory', company: 'SupplyHive', level: 'Beginner' },
    { title: 'Auth + role system', company: 'SecureStack', level: 'Intermediate' },
    { title: 'Optimize API latency', company: 'EdgeWare', level: 'Expert' }
  ],
  mern: [
    { title: 'Landing page + signup flow', company: 'LaunchPad', level: 'Beginner' },
    { title: 'Realtime chat feature', company: 'TeamWave', level: 'Intermediate' },
    { title: 'Performance audit + fixes', company: 'ScaleLab', level: 'Expert' }
  ]
};

// Filter tabs
function initFilterTabs() {
  const filterTabs = document.querySelectorAll('.filter-tab');
  
  filterTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      // Update active tab
      filterTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      
      // Filter courses
      const filter = this.getAttribute('data-filter');
      renderCourses(filter);
    });
  });
}

// Search box
function initSearchBox() {
  const searchInput = document.querySelector('.search-box input');
  
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const activeFilter = document.querySelector('.filter-tab.active').getAttribute('data-filter');
      renderCourses(activeFilter, searchTerm);
    });
  }
}

// Sort dropdown
const sortDropdown = document.querySelector('.sort-dropdown');
if (sortDropdown) {
  sortDropdown.addEventListener('change', function() {
    const activeFilter = document.querySelector('.filter-tab.active').getAttribute('data-filter');
    const searchTerm = document.querySelector('.search-box input')?.value.toLowerCase() || '';
    renderCourses(activeFilter, searchTerm, this.value);
  });
}

// Render courses
function renderCourses(filter = 'all', searchTerm = '', sortBy = 'recent') {
  const coursesGrid = document.querySelector('.courses-grid');
  
  if (!coursesGrid) return;
  
  // Filter courses
  let filteredCourses = coursesData;
  
  if (filter !== 'all') {
    filteredCourses = coursesData.filter(course => course.status === filter);
  }
  
  // Search filter
  if (searchTerm) {
    filteredCourses = filteredCourses.filter(course => 
      course.title.toLowerCase().includes(searchTerm) ||
      course.category.toLowerCase().includes(searchTerm) ||
      course.instructor.toLowerCase().includes(searchTerm)
    );
  }
  
  // Sort courses
  if (sortBy === 'title') {
    filteredCourses.sort((a, b) => a.title.localeCompare(b.title));
  } else if (sortBy === 'progress') {
    filteredCourses.sort((a, b) => b.progress - a.progress);
  } else if (sortBy === 'rating') {
    filteredCourses.sort((a, b) => b.rating - a.rating);
  }
  
  // Render
  if (filteredCourses.length === 0) {
    coursesGrid.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fa-solid fa-book-open"></i>
        <h3>No courses found</h3>
        <p>Try adjusting your filters or search terms</p>
      </div>
    `;
    return;
  }
  
  coursesGrid.innerHTML = filteredCourses.map(course => createCourseCard(course)).join('');
  
  // Add click handlers
  document.querySelectorAll('.course-card').forEach((card, index) => {
    card.addEventListener('click', function(e) {
      if (!e.target.closest('.course-action-btn')) {
        showCourseDetails(filteredCourses[index]);
      }
    });
  });
  
  // Action button handlers
  document.querySelectorAll('.course-action-btn').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const course = filteredCourses[index];
      if (course.status === 'completed') {
        window.location.href = `/certificates?course=${course.id}`;
      } else if (course.status === 'bookmarked' || course.progress === 0) {
        openEnrollModal(course);
      } else {
        window.location.href = `/learn/${course.id}`;
      }
    });
  });
}

// Create course card HTML
function createCourseCard(course) {
  const statusBadges = {
    'in-progress': 'In Progress',
    'completed': 'Completed',
    'bookmarked': 'Bookmarked'
  };
  
  const actionButtons = {
    'in-progress': 'Continue',
    'completed': 'View Certificate',
    'bookmarked': 'Enroll Free'
  };
  
  return `
    <div class="course-card" data-course-id="${course.id}">
      <div class="course-thumbnail">
        <span>${course.thumbnail}</span>
        ${course.status ? `<span class="course-badge">${statusBadges[course.status]}</span>` : ''}
      </div>
      <div class="course-content">
        <div class="course-header">
          <span class="course-category">${course.category}</span>
          <h3 class="course-title">${course.title}</h3>
          <div class="course-instructor">
            <i class="fa-solid fa-user"></i>
            <span>${course.instructor}</span>
          </div>
        </div>
        <p class="course-description">${course.description}</p>
        ${course.progress > 0 ? `
          <div class="course-progress">
            <div class="progress-header">
              <span class="progress-label">Progress</span>
              <span class="progress-percentage">${course.progress}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${course.progress}%"></div>
            </div>
          </div>
        ` : ''}
        <div class="course-meta">
          <div class="meta-item">
            <i class="fa-solid fa-clock"></i>
            <span>${course.duration}</span>
          </div>
          <div class="meta-item">
            <i class="fa-solid fa-book"></i>
            <span>${course.lessons} lessons</span>
          </div>
          <div class="meta-item">
            <i class="fa-solid fa-users"></i>
            <span>${course.students.toLocaleString()}</span>
          </div>
        </div>
      </div>
      <div class="course-footer">
        <div class="course-rating">
          <div class="stars">
            ${generateStars(course.rating)}
          </div>
          <span class="rating-value">${course.rating}</span>
          <span class="rating-count">(${course.reviews})</span>
        </div>
        <button class="course-action-btn">${actionButtons[course.status] || 'Start Course'}</button>
      </div>
    </div>
  `;
}

// Generate star rating HTML
function generateStars(rating) {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  let stars = '';
  
  for (let i = 0; i < fullStars; i++) {
    stars += '<i class="fa-solid fa-star"></i>';
  }
  
  if (hasHalfStar) {
    stars += '<i class="fa-solid fa-star-half-stroke"></i>';
  }
  
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
  for (let i = 0; i < emptyStars; i++) {
    stars += '<i class="fa-regular fa-star"></i>';
  }
  
  return stars;
}

// Update stats
function updateStats() {
  const inProgress = coursesData.filter(c => c.status === 'in-progress').length;
  const completed = coursesData.filter(c => c.status === 'completed').length;
  const totalHours = coursesData.reduce((sum, c) => sum + parseInt(c.duration), 0);
  const avgRating = (coursesData.reduce((sum, c) => sum + c.rating, 0) / coursesData.length).toFixed(1);
  
  const statCards = document.querySelectorAll('.stat-card .stat-value');
  if (statCards.length >= 4) {
    animateValue(statCards[0], 0, inProgress, 1000);
    animateValue(statCards[1], 0, completed, 1000);
    animateValue(statCards[2], 0, totalHours, 1000);
    statCards[3].textContent = avgRating;
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

// Show course details (mock)
function showCourseDetails(course) {
  console.log('Course details:', course);
  // In a real app, this would open a modal or navigate to course details page
}

function initEnrollFlow() {
  const modal = document.getElementById('enroll-modal');
  const closeBtn = document.getElementById('enroll-close');
  const domainNextBtn = document.getElementById('domain-next-btn');
  const assessmentBackBtn = document.getElementById('assessment-back-btn');
  const assessmentSubmitBtn = document.getElementById('assessment-submit-btn');
  const restartBtn = document.getElementById('restart-quiz-btn');
  const startCourseBtn = document.getElementById('start-course-btn');

  if (!modal) return;

  closeBtn?.addEventListener('click', () => closeEnrollModal());
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeEnrollModal();
  });

  domainNextBtn?.addEventListener('click', () => {
    showEnrollStep('assessment');
  });

  assessmentBackBtn?.addEventListener('click', () => {
    showEnrollStep('domain');
  });

  assessmentSubmitBtn?.addEventListener('click', () => {
    const assessment = calculateAssessment();
    latestAssessment = assessment;
    renderAssessmentResult(assessment);
    showEnrollStep('result');
  });

  restartBtn?.addEventListener('click', () => {
    showEnrollStep('level');
    resetEnrollFlow();
  });

  startCourseBtn?.addEventListener('click', async () => {
    if (currentEnrollCourse) {
      const assessment = latestAssessment || calculateAssessment();
      
      // Save enrollment to database
      try {
        const response = await fetch('/api/enroll', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            course_id: currentEnrollCourse.id,
            level_assessed: assessment.level,
            recommended_lesson_id: assessment.lesson_id || 1
          })
        });
        
        if (response.ok) {
          window.location.href = `/learn/${currentEnrollCourse.id}`;
        }
      } catch (error) {
        console.error('Enrollment error:', error);
        window.location.href = `/learn/${currentEnrollCourse.id}`;
      }
    }
  });
}

function openEnrollModal(course) {
  currentEnrollCourse = course;
  const modal = document.getElementById('enroll-modal');
  const title = document.getElementById('enroll-course-title');
  const subtitle = document.getElementById('enroll-course-subtitle');

  if (!modal) return;

  title.textContent = `Enroll for Free: ${course.title}`;
  subtitle.textContent = 'Pick a domain, complete the assessment, and get a custom learning path.';
  resetEnrollFlow();
  renderDomainOptions();
  showEnrollStep('domain');
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
}

function closeEnrollModal() {
  const modal = document.getElementById('enroll-modal');
  if (!modal) return;
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
  currentEnrollCourse = null;
}

function showEnrollStep(step) {
  const domainStep = document.getElementById('enroll-step-domain');
  const assessmentStep = document.getElementById('enroll-step-assessment');
  const resultStep = document.getElementById('enroll-step-result');

  if (!domainStep || !assessmentStep || !resultStep) return;

  domainStep.hidden = step !== 'domain';
  assessmentStep.hidden = step !== 'assessment';
  resultStep.hidden = step !== 'result';
}

function resetEnrollFlow() {
  const domainInputs = document.querySelectorAll('input[name="domain"]');
  const domainNextBtn = document.getElementById('domain-next-btn');
  const assessmentSubmitBtn = document.getElementById('assessment-submit-btn');
  const assessmentContainer = document.getElementById('assessment-questions');
  const gapsList = document.getElementById('assessment-gaps');
  const pathList = document.getElementById('path-list');
  const gigList = document.getElementById('gig-list');
  const levelBadge = document.getElementById('assessment-level');
  const domainBadge = document.getElementById('assessment-domain');
  const recommendationBox = document.getElementById('recommendation-box');

  selectedDomain = null;
  latestAssessment = null;

  domainInputs.forEach(input => {
    input.checked = false;
  });

  if (domainNextBtn) domainNextBtn.disabled = true;
  if (assessmentSubmitBtn) assessmentSubmitBtn.disabled = true;
  if (assessmentContainer) assessmentContainer.innerHTML = '';
  if (recommendationBox) recommendationBox.innerHTML = '';
  if (gapsList) gapsList.innerHTML = '';
  if (pathList) pathList.innerHTML = '';
  if (gigList) gigList.innerHTML = '';
  if (levelBadge) levelBadge.textContent = '';
  if (domainBadge) domainBadge.textContent = '';
}

function renderDomainOptions() {
  const container = document.getElementById('domain-options');
  if (!container) return;

  container.innerHTML = domainOptions.map(option => `
    <label class="domain-card">
      <input type="radio" name="domain" value="${option.id}">
      <div class="domain-icon">${option.icon}</div>
      <div class="domain-info">
        <strong>${option.label}</strong>
        <span>${option.description}</span>
      </div>
    </label>
  `).join('');

  container.querySelectorAll('input[name="domain"]').forEach(input => {
    input.addEventListener('change', () => {
      selectedDomain = input.value;
      const domainNextBtn = document.getElementById('domain-next-btn');
      if (domainNextBtn) domainNextBtn.disabled = false;
      container.querySelectorAll('.domain-card').forEach(card => card.classList.remove('selected'));
      const selectedCard = input.closest('.domain-card');
      if (selectedCard) selectedCard.classList.add('selected');
      renderAssessmentQuestions(selectedDomain);
    });
  });
}

function renderAssessmentQuestions(domainId) {
  const assessmentContainer = document.getElementById('assessment-questions');
  const assessmentSubmitBtn = document.getElementById('assessment-submit-btn');
  if (!assessmentContainer) return;

  const questions = domainAssessments[domainId] || domainAssessments.default;

  assessmentContainer.innerHTML = questions.map((q, index) => {
    const optionsHtml = q.options.map((opt) => `
      <label class="quiz-option">
        <input type="radio" name="assessment-q${index}" value="${opt.score}" data-concept="${q.concept}">
        ${opt.label}
      </label>
    `).join('');

    return `
      <div class="quiz-question">
        <h5>${index + 1}. ${q.question}</h5>
        <div class="quiz-options">${optionsHtml}</div>
      </div>
    `;
  }).join('');

  assessmentContainer.querySelectorAll('input[type="radio"]').forEach(input => {
    input.addEventListener('change', () => {
      const totalAnswered = assessmentContainer.querySelectorAll('input[type="radio"]:checked').length;
      if (assessmentSubmitBtn) assessmentSubmitBtn.disabled = totalAnswered < questions.length;
    });
  });
}

function calculateAssessment() {
  const domainId = selectedDomain || domainOptions[0].id;
  const questions = domainAssessments[domainId] || domainAssessments.default;
  let total = 0;
  const gaps = new Set();

  questions.forEach((q, index) => {
    const selected = document.querySelector(`input[name="assessment-q${index}"]:checked`);
    if (selected) {
      const score = Number(selected.value);
      total += score;
      if (score <= 1) {
        gaps.add(q.concept);
      }
    } else {
      gaps.add(q.concept);
    }
  });

  let level = 'Beginner';
  if (total > 10) level = 'Expert';
  else if (total > 6) level = 'Intermediate';

  const path = (domainPaths[domainId] && domainPaths[domainId][level]) || [];
  const gigs = domainGigs[domainId] || [];

  return {
    domainId,
    domainLabel: domainOptions.find(option => option.id === domainId)?.label || 'Your Domain',
    level,
    gaps: gaps.size ? Array.from(gaps) : ['No critical gaps detected'],
    path,
    gigs
  };
}

function renderAssessmentResult(assessment) {
  const levelBadge = document.getElementById('assessment-level');
  const domainBadge = document.getElementById('assessment-domain');
  const gapsList = document.getElementById('assessment-gaps');
  const pathList = document.getElementById('path-list');
  const gigList = document.getElementById('gig-list');

  if (levelBadge) levelBadge.textContent = `Level: ${assessment.level}`;
  if (domainBadge) domainBadge.textContent = assessment.domainLabel;

  if (gapsList) {
    gapsList.innerHTML = assessment.gaps.map(item => `<li>${item}</li>`).join('');
  }

  if (pathList) {
    pathList.innerHTML = assessment.path.map(step => `<li>${step}</li>`).join('');
  }

  if (gigList) {
    gigList.innerHTML = assessment.gigs.map(gig => `
      <div class="gig-card">
        <h6>${gig.title}</h6>
        <p>${gig.company}</p>
        <span class="gig-pill">${gig.level}</span>
      </div>
    `).join('');
  }
}
}
