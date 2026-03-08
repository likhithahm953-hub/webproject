// UI Functions for Challenges Page

// Filter tabs (available/active/completed)
function initFilterTabs() {
  const filterTabs = document.querySelectorAll('.filter-tab');
  
  filterTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      filterTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');

      const filters = getActiveFilters();
      filters.statusFilter = this.getAttribute('data-filter') || 'all';
      renderChallenges(filters.statusFilter, filters.difficultyFilter, filters.topicFilter);
    });
  });
}

// Difficulty filters
function initDifficultyFilters() {
  const difficultyBtns = document.querySelectorAll('.difficulty-btn');
  
  difficultyBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      difficultyBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      const filters = getActiveFilters();
      filters.difficultyFilter = this.getAttribute('data-difficulty') || 'all';
      renderChallenges(filters.statusFilter, filters.difficultyFilter, filters.topicFilter);
    });
  });
}

function initTopicFilter() {
  const topicSelect = document.getElementById('topic-filter');
  if (!topicSelect) return;

  const topics = new Set();
  challengesData.forEach(challenge => {
    (challenge.tags || []).forEach(tag => topics.add(tag));
  });

  const sortedTopics = Array.from(topics).sort((a, b) => a.localeCompare(b));
  topicSelect.innerHTML = ['<option value="all">All Topics</option>']
    .concat(sortedTopics.map(tag => `<option value="${tag}">${tag}</option>`))
    .join('');

  topicSelect.addEventListener('change', () => {
    const filters = getActiveFilters();
    renderChallenges(filters.statusFilter, filters.difficultyFilter, filters.topicFilter);
  });
}

function getActiveFilters() {
  return {
    statusFilter: document.querySelector('.filter-tab.active')?.getAttribute('data-filter') || 'all',
    difficultyFilter: document.querySelector('.difficulty-btn.active')?.getAttribute('data-difficulty') || 'all',
    topicFilter: document.getElementById('topic-filter')?.value || 'all'
  };
}

// Render challenges
function renderChallenges(statusFilter = 'all', difficultyFilter = 'all', topicFilter = 'all') {
  const challengesGrid = document.querySelector('.challenges-grid');
  
  if (!challengesGrid) return;
  
  // Filter challenges
  let filtered = challengesData;
  
  if (statusFilter !== 'all') {
    filtered = filtered.filter(c => c.status === statusFilter);
  }
  
  if (difficultyFilter !== 'all') {
    filtered = filtered.filter(c => c.difficulty === difficultyFilter);
  }

  if (topicFilter !== 'all') {
    filtered = filtered.filter(c => (c.tags || []).includes(topicFilter));
  }
  
  // Render
  if (filtered.length === 0) {
    challengesGrid.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-code"></i>
        <h3>No challenges found</h3>
        <p>Try adjusting your filters</p>
      </div>
    `;
    return;
  }
  
  challengesGrid.innerHTML = filtered.map(challenge => createChallengeCard(challenge)).join('');
  
  // Add click handlers
  document.querySelectorAll('.challenge-action').forEach((btn, index) => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const challenge = filtered[index];
      if (challenge.status === 'completed') {
        // Show solution
        showChallengeDetails(challenge);
      } else {
        showChallengeDetails(challenge);
      }
    });
  });
  
  document.querySelectorAll('.challenge-card').forEach((card, index) => {
    card.addEventListener('click', function(e) {
      if (!e.target.closest('.challenge-action')) {
        showChallengeDetails(filtered[index]);
      }
    });
  });
}

// Create challenge card HTML
function createChallengeCard(challenge) {
  const statusIcons = {
    'completed': '<i class="fa-solid fa-circle-check"></i>',
    'active': '<i class="fa-solid fa-circle-dot"></i>',
    'available': ''
  };
  
  const statusLabels = {
    'completed': 'Completed',
    'active': 'In Progress',
    'available': ''
  };
  
  const actionButtons = {
    'completed': 'View Solution',
    'active': 'Continue',
    'available': 'Start Challenge'
  };
  
  return `
    <div class="challenge-card" data-challenge-id="${challenge.id}">
      <div class="challenge-header">
        <span class="challenge-difficulty ${challenge.difficulty}">${challenge.difficulty}</span>
        ${challenge.status !== 'available' ? `
          <span class="challenge-status ${challenge.status}">
            ${statusIcons[challenge.status]}
            ${statusLabels[challenge.status]}
          </span>
        ` : ''}
      </div>
      
      <h3 class="challenge-title">${challenge.title}</h3>
      <p class="challenge-description">${challenge.description}</p>
      
      <div class="challenge-tags">
        ${challenge.tags.map(tag => `<span class="challenge-tag">${tag}</span>`).join('')}
      </div>
      
      <div class="challenge-meta">
        <div class="meta-item">
          <span class="meta-label">Points</span>
          <span class="meta-value">
            <i class="fa-solid fa-trophy"></i>
            ${challenge.points}
          </span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Solvers</span>
          <span class="meta-value">
            <i class="fa-solid fa-users"></i>
            ${challenge.solvers.toLocaleString()}
          </span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Time Limit</span>
          <span class="meta-value">
            <i class="fa-solid fa-clock"></i>
            ${challenge.timeLimit}
          </span>
        </div>
      </div>
      
      <div class="challenge-footer">
        <div class="success-rate">
          <span>Success:</span>
          <div class="rate-bar">
            <div class="rate-fill" style="width: ${challenge.successRate}%"></div>
          </div>
          <span class="rate-percentage">${challenge.successRate}%</span>
        </div>
        <button class="challenge-action ${challenge.status === 'completed' ? 'completed-btn' : ''}">
          ${actionButtons[challenge.status]}
        </button>
      </div>
    </div>
  `;
}

// Update stats
function updateStats() {
  const completed = challengesData.filter(c => c.status === 'completed').length;
  const active = challengesData.filter(c => c.status === 'active').length;
  const totalPoints = challengesData
    .filter(c => c.status === 'completed')
    .reduce((sum, c) => sum + c.points, 0);
  const streak = 15; // Mock streak
  
  const statCards = document.querySelectorAll('.stat-card-small h3');
  if (statCards.length >= 4) {
    animateValue(statCards[0], 0, completed, 1000);
    animateValue(statCards[1], 0, active, 1000);
    animateValue(statCards[2], 0, totalPoints, 1000);
    animateValue(statCards[3], 0, streak, 1000);
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

// Show challenge details
function showChallengeDetails(challenge) {
  const modal = document.getElementById('challenge-modal');
  const title = document.getElementById('challenge-modal-title');
  const difficulty = document.getElementById('challenge-modal-difficulty');
  const tags = document.getElementById('challenge-modal-tags');
  const body = document.getElementById('challenge-modal-body');
  const startBtn = document.getElementById('challenge-start-btn');

  if (!modal || !title || !difficulty || !tags || !body || !startBtn) return;

  title.textContent = challenge.title;
  difficulty.textContent = challenge.difficulty;
  difficulty.className = `modal-difficulty ${challenge.difficulty}`;
  tags.innerHTML = challenge.tags.map(tag => `<span class="challenge-tag">${tag}</span>`).join('');

  const constraints = challenge.constraints.map(item => `<li>${item}</li>`).join('');
  const examples = challenge.examples.map(example => `
    <div class="example-block">
      <div class="example-row"><strong>Input:</strong> ${example.input}</div>
      <div class="example-row"><strong>Output:</strong> ${example.output}</div>
      ${example.explanation ? `<div class="example-row"><strong>Explanation:</strong> ${example.explanation}</div>` : ''}
    </div>
  `).join('');

  const tests = challenge.testCases.map((test, idx) => `
    <div class="testcase">
      <div class="testcase-title">Test Case ${idx + 1}</div>
      <div class="testcase-row"><strong>Input:</strong> ${test.input}</div>
      <div class="testcase-row"><strong>Expected Output:</strong> ${test.output}</div>
    </div>
  `).join('');

  body.innerHTML = `
    <section class="modal-section">
      <h3>Problem Statement</h3>
      <p>${challenge.problemStatement}</p>
    </section>
    <section class="modal-section">
      <h3>Input Format</h3>
      <p>${challenge.inputFormat}</p>
    </section>
    <section class="modal-section">
      <h3>Output Format</h3>
      <p>${challenge.outputFormat}</p>
    </section>
    <section class="modal-section">
      <h3>Constraints</h3>
      <ul>${constraints}</ul>
    </section>
    <section class="modal-section">
      <h3>Examples</h3>
      ${examples}
    </section>
    <section class="modal-section">
      <h3>Public Test Cases</h3>
      ${tests}
    </section>
    <section class="modal-section editor-section">
      <div class="editor-header">
        <h3>Code Workspace</h3>
        <div class="editor-controls">
          <label for="challenge-language">Language</label>
          <select id="challenge-language">
            <option value="javascript">JavaScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
          </select>
        </div>
      </div>
      <p class="editor-note">Sample runner only. Use the public test cases above to validate your solution locally.</p>
      <textarea id="challenge-code" class="code-input" rows="10" placeholder="Write your solution here..."></textarea>
      <div class="editor-actions">
        <button class="challenge-action" id="run-tests-btn">Run Tests</button>
        <button class="challenge-action secondary-btn" id="view-solution-btn">View Solution</button>
        <div class="test-status" id="challenge-status"></div>
      </div>
      <div class="test-results" id="challenge-results"></div>
    </section>
  `;

  const codeArea = body.querySelector('#challenge-code');
  const languageSelect = body.querySelector('#challenge-language');
  const runBtn = body.querySelector('#run-tests-btn');
  const viewSolutionBtn = body.querySelector('#view-solution-btn');
  const results = body.querySelector('#challenge-results');
  const status = body.querySelector('#challenge-status');
  const editorSection = body.querySelector('.editor-section');

  if (startBtn && editorSection) {
    startBtn.onclick = () => editorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const starterTemplates = {
    javascript: `function solve(input) {\n  // TODO: implement\n  return input;\n}\n`,
    python: `def solve(input):\n    # TODO: implement\n    return input\n`,
    java: `class Solution {\n    public Object solve(Object input) {\n        // TODO: implement\n        return input;\n    }\n}\n`,
    c: `#include <stdio.h>\n#include <stdlib.h>\n\nint solve(int input) {\n    // TODO: implement\n    return input;\n}\n`,
    cpp: `#include <iostream>\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int solve(int input) {\n        // TODO: implement\n        return input;\n    }\n};\n`
  };

  if (codeArea) {
    codeArea.value = starterTemplates.javascript;
  }

  if (languageSelect && codeArea) {
    languageSelect.addEventListener('change', () => {
      const lang = languageSelect.value;
      codeArea.value = starterTemplates[lang] || '';
    });
  }

  // View Solution button handler
  if (viewSolutionBtn && codeArea && languageSelect) {
    viewSolutionBtn.addEventListener('click', () => {
      const lang = languageSelect.value;
      if (challenge.solutions && challenge.solutions[lang]) {
        codeArea.value = challenge.solutions[lang];
        if (status) {
          status.textContent = `Solution loaded for ${lang.toUpperCase()}`;
          status.className = 'test-status pass';
        }
        if (results) {
          results.innerHTML = '';
        }
      } else {
        if (status) {
          status.textContent = 'Solution not available for this language.';
          status.className = 'test-status fail';
        }
      }
    });
  }

  if (runBtn && results && status) {
    runBtn.addEventListener('click', () => {
      const code = codeArea ? codeArea.value.trim() : '';
      if (!code) {
        status.textContent = 'Add a solution before running tests.';
        status.className = 'test-status fail';
        results.innerHTML = '';
        return;
      }

      const passesAll = code.length > 20;
      status.textContent = passesAll ? 'Mock run: All tests passed.' : 'Mock run: Some tests failed.';
      status.className = `test-status ${passesAll ? 'pass' : 'fail'}`;

      results.innerHTML = challenge.testCases.map((test, idx) => {
        const passed = passesAll;
        return `
          <div class="test-result ${passed ? 'pass' : 'fail'}">
            <div class="test-result-title">Test Case ${idx + 1} - ${passed ? 'Passed' : 'Failed'}</div>
            <div class="test-result-row"><strong>Input:</strong> ${test.input}</div>
            <div class="test-result-row"><strong>Expected:</strong> ${test.output}</div>
          </div>
        `;
      }).join('');
    });
  }

  startBtn.textContent = 'Start Challenge';
  modal.setAttribute('aria-hidden', 'false');
  modal.classList.add('open');
}

// Close modal
document.addEventListener('click', (event) => {
  const modal = document.getElementById('challenge-modal');
  if (!modal) return;
  const shouldClose = event.target.closest('[data-close="true"]');
  if (shouldClose) {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }
});

function renderBreakdown() {
  const difficultyContainer = document.getElementById('difficulty-breakdown');
  const topicContainer = document.getElementById('topic-breakdown');

  if (difficultyContainer) {
    const easyCount = challengesData.filter(c => c.difficulty === 'easy').length;
    const mediumCount = challengesData.filter(c => c.difficulty === 'medium').length;
    const hardCount = challengesData.filter(c => c.difficulty === 'hard').length;
    const total = Math.max(easyCount + mediumCount + hardCount, 1);

    const easyPct = Math.round((easyCount / total) * 100);
    const mediumPct = Math.round((mediumCount / total) * 100);
    const hardPct = Math.round((hardCount / total) * 100);

    difficultyContainer.innerHTML = `
      <div class="breakdown-row">
        <span>Easy</span>
        <div class="breakdown-bar"><span class="breakdown-fill easy" style="width: ${easyPct}%"></span></div>
        <span>${easyCount}</span>
      </div>
      <div class="breakdown-row">
        <span>Medium</span>
        <div class="breakdown-bar"><span class="breakdown-fill medium" style="width: ${mediumPct}%"></span></div>
        <span>${mediumCount}</span>
      </div>
      <div class="breakdown-row">
        <span>Hard</span>
        <div class="breakdown-bar"><span class="breakdown-fill hard" style="width: ${hardPct}%"></span></div>
        <span>${hardCount}</span>
      </div>
    `;
  }

  if (topicContainer) {
    const counts = {};
    challengesData.forEach(challenge => {
      challenge.tags.forEach(tag => {
        counts[tag] = (counts[tag] || 0) + 1;
      });
    });

    const priorityTags = ["Linked List", "Stack", "Queue"];
    const sortedTags = Object.entries(counts)
      .sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]));

    const selected = [];
    const selectedSet = new Set();

    priorityTags.forEach(tag => {
      if (counts[tag] !== undefined && !selectedSet.has(tag)) {
        selected.push([tag, counts[tag]]);
        selectedSet.add(tag);
      }
    });

    for (const [tag, count] of sortedTags) {
      if (selected.length >= 6) break;
      if (!selectedSet.has(tag)) {
        selected.push([tag, count]);
        selectedSet.add(tag);
      }
    }

    topicContainer.innerHTML = selected
      .map(([tag, count]) => `<span class="topic-pill">${tag} (${count})</span>`)
      .join('');
  }
}

function initShuffleButton() {
  const shuffleBtn = document.getElementById('shuffle-btn');
  if (!shuffleBtn) return;

  shuffleBtn.addEventListener('click', () => {
    for (let i = challengesData.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [challengesData[i], challengesData[j]] = [challengesData[j], challengesData[i]];
    }
    const filters = getActiveFilters();
    renderChallenges(filters.statusFilter, filters.difficultyFilter, filters.topicFilter);
  });
}
