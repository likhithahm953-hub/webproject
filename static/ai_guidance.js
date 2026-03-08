// AI Guidance Page JavaScript

// Learning paths data
const learningPaths = [
  {
    id: 1,
    title: "Full-Stack Web Developer",
    level: "Intermediate to Advanced",
    description: "Master both frontend and backend development with modern frameworks and tools.",
    duration: "6 months",
    courses: 8,
    projects: 12,
    progress: 45,
    coursesList: [
      "HTML & CSS Mastery",
      "JavaScript Advanced",
      "React & Redux",
      "Node.js & Express",
      "MongoDB Database",
      "RESTful API Design",
      "Authentication & Security",
      "Deployment & DevOps"
    ]
  },
  {
    id: 2,
    title: "Machine Learning Engineer",
    level: "Advanced",
    description: "Deep dive into ML algorithms, neural networks, and production ML systems.",
    duration: "8 months",
    courses: 10,
    projects: 15,
    progress: 20,
    coursesList: [
      "Python for Data Science",
      "Statistics & Probability",
      "Machine Learning Basics",
      "Deep Learning",
      "Computer Vision",
      "NLP Fundamentals",
      "MLOps & Deployment",
      "Model Optimization"
    ]
  },
  {
    id: 3,
    title: "Cloud Solutions Architect",
    level: "Intermediate",
    description: "Design and implement scalable cloud infrastructure across multiple platforms.",
    duration: "5 months",
    courses: 7,
    projects: 10,
    progress: 0,
    coursesList: [
      "Cloud Computing Basics",
      "AWS Services Deep Dive",
      "Azure Fundamentals",
      "Containerization with Docker",
      "Kubernetes Orchestration",
      "Infrastructure as Code",
      "Cloud Security"
    ]
  }
];

// Recommended courses
const recommendedCourses = [
  {
    title: "System Design Fundamentals",
    reason: "Builds on your Data Structures knowledge and prepares you for senior roles",
    matchScore: 95,
    duration: "6 weeks",
    difficulty: "Advanced"
  },
  {
    title: "Microservices Architecture",
    reason: "Natural progression from your web development skills",
    matchScore: 92,
    duration: "8 weeks",
    difficulty: "Advanced"
  },
  {
    title: "DevOps Engineering",
    reason: "Complements your cloud computing knowledge",
    matchScore: 88,
    duration: "7 weeks",
    difficulty: "Intermediate"
  },
  {
    title: "GraphQL API Development",
    reason: "Enhances your backend development capabilities",
    matchScore: 85,
    duration: "4 weeks",
    difficulty: "Intermediate"
  },
  {
    title: "Docker & Kubernetes",
    reason: "Essential for modern application deployment",
    matchScore: 90,
    duration: "6 weeks",
    difficulty: "Intermediate"
  },
  {
    title: "React Native Development",
    reason: "Expands your frontend skills to mobile platforms",
    matchScore: 87,
    duration: "8 weeks",
    difficulty: "Intermediate"
  }
];

// Skills gap data
const skillsGapData = {
  labels: ['Frontend', 'Backend', 'Database', 'DevOps', 'Cloud', 'Security'],
  currentLevel: [85, 75, 80, 45, 60, 50],
  targetLevel: [90, 90, 85, 80, 85, 75]
};

// Improvement areas
const improvementAreas = [
  {
    skill: "DevOps",
    priority: "high",
    suggestion: "Complete CI/CD pipeline course and practice with Jenkins/GitHub Actions"
  },
  {
    skill: "Cloud Security",
    priority: "high",
    suggestion: "Focus on IAM, encryption, and security best practices for AWS/Azure"
  },
  {
    skill: "System Design",
    priority: "medium",
    suggestion: "Study scalability patterns and distributed systems architecture"
  },
  {
    skill: "Testing",
    priority: "medium",
    suggestion: "Learn unit testing, integration testing, and TDD practices"
  },
  {
    skill: "Performance Optimization",
    priority: "low",
    suggestion: "Study caching strategies, database indexing, and profiling tools"
  }
];

// Initialize AI guidance page
document.addEventListener('DOMContentLoaded', function() {
  renderLearningPaths();
  renderRecommendedCourses();
  renderImprovementAreas();
  initRadarChart();
  initInsightActions();
});

// Render learning paths
function renderLearningPaths() {
  const pathsGrid = document.querySelector('.paths-grid');
  
  if (!pathsGrid) return;
  
  pathsGrid.innerHTML = learningPaths.map(path => createPathCard(path)).join('');
  
  // Add click handlers
  document.querySelectorAll('.path-action-btn').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      startLearningPath(learningPaths[index]);
    });
  });
}

// Create path card HTML
function createPathCard(path) {
  return `
    <div class="path-card">
      <div class="path-header">
        <span class="path-badge">${path.level}</span>
        <h3 class="path-title">${path.title}</h3>
        <p class="path-description">${path.description}</p>
      </div>
      <div class="path-content">
        <div class="path-stats">
          <div class="path-stat">
            <span class="path-stat-label">Duration</span>
            <span class="path-stat-value">${path.duration}</span>
          </div>
          <div class="path-stat">
            <span class="path-stat-label">Courses</span>
            <span class="path-stat-value">${path.courses}</span>
          </div>
          <div class="path-stat">
            <span class="path-stat-label">Projects</span>
            <span class="path-stat-value">${path.projects}</span>
          </div>
        </div>
        
        <div class="path-courses">
          <h4 class="path-courses-title">Included Courses</h4>
          <div class="courses-list">
            ${path.coursesList.slice(0, 4).map(course => `
              <div class="course-item">
                <i class="fa-solid fa-book"></i>
                <span>${course}</span>
              </div>
            `).join('')}
            ${path.coursesList.length > 4 ? `
              <div class="course-item">
                <i class="fa-solid fa-ellipsis"></i>
                <span>+${path.coursesList.length - 4} more courses</span>
              </div>
            ` : ''}
          </div>
        </div>
        
        ${path.progress > 0 ? `
          <div class="path-progress">
            <div class="path-progress-label">
              <span class="progress-text">Your Progress</span>
              <span class="progress-percentage">${path.progress}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${path.progress}%"></div>
            </div>
          </div>
        ` : ''}
        
        <button class="path-action-btn">
          <i class="fa-solid fa-rocket"></i>
          ${path.progress > 0 ? 'Continue Path' : 'Start Learning Path'}
        </button>
      </div>
    </div>
  `;
}

// Render recommended courses
function renderRecommendedCourses() {
  const recommendationsGrid = document.querySelector('.recommendations-grid');
  
  if (!recommendationsGrid) return;
  
  recommendationsGrid.innerHTML = recommendedCourses.map(course => `
    <div class="recommendation-card">
      <div class="recommendation-header">
        <div class="match-score">
          <i class="fa-solid fa-fire"></i>
          ${course.matchScore}% Match
        </div>
      </div>
      <h4 class="recommendation-title">${course.title}</h4>
      <p class="recommendation-reason">"${course.reason}"</p>
      <div class="recommendation-meta">
        <span><i class="fa-solid fa-clock"></i> ${course.duration}</span>
        <span><i class="fa-solid fa-signal"></i> ${course.difficulty}</span>
      </div>
    </div>
  `).join('');
}

// Render improvement areas
function renderImprovementAreas() {
  const improvementsList = document.querySelector('.improvements-list');
  
  if (!improvementsList) return;
  
  const itemsHTML = improvementAreas.map(area => `
    <div class="improvement-item">
      <div class="improvement-header">
        <span class="improvement-skill">${area.skill}</span>
        <span class="priority-badge ${area.priority}">${area.priority.toUpperCase()}</span>
      </div>
      <p class="improvement-suggestion">${area.suggestion}</p>
    </div>
  `).join('');
  
  improvementsList.innerHTML = `
    <h4>Focus Areas</h4>
    ${itemsHTML}
  `;
}

// Initialize radar chart
function initRadarChart() {
  const canvas = document.getElementById('skillsRadarChart');
  
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: skillsGapData.labels,
      datasets: [
        {
          label: 'Current Level',
          data: skillsGapData.currentLevel,
          fill: true,
          backgroundColor: 'rgba(99, 102, 241, 0.2)',
          borderColor: 'rgb(99, 102, 241)',
          pointBackgroundColor: 'rgb(99, 102, 241)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgb(99, 102, 241)'
        },
        {
          label: 'Target Level',
          data: skillsGapData.targetLevel,
          fill: true,
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderColor: 'rgb(16, 185, 129)',
          pointBackgroundColor: 'rgb(16, 185, 129)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgb(16, 185, 129)'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          min: 0,
          max: 100,
          beginAtZero: true,
          ticks: {
            stepSize: 20,
            color: 'rgba(255, 255, 255, 0.5)'
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          pointLabels: {
            color: 'rgba(255, 255, 255, 0.8)',
            font: {
              size: 12,
              weight: 600
            }
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            color: 'rgba(255, 255, 255, 0.8)',
            font: {
              size: 12
            }
          }
        }
      }
    }
  });
}

// Initialize insight actions
function initInsightActions() {
  document.querySelectorAll('.insight-action').forEach(action => {
    action.addEventListener('click', function() {
      const actionType = this.textContent.trim();
      
      if (actionType.includes('View')) {
        window.location.href = '/ai-guidance/recommendations';
      } else if (actionType.includes('Analyze')) {
        window.location.href = '/ai-guidance/performance';
      }
    });
  });
}

// Start learning path
function startLearningPath(path) {
  console.log('Starting learning path:', path);
  showToast(`Starting ${path.title} learning path!`);
  // In a real app, this would navigate to the learning path or enroll the user
  setTimeout(() => {
    window.location.href = `/learning-paths/${path.id}`;
  }, 1000);
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
