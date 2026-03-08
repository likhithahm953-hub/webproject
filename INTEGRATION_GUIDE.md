# Integration Guide: Connecting Quiz & Certificate System to Existing Pages

## Overview
This guide shows how to integrate the newly implemented Quiz & Certificate System into your existing SkillForge application pages (domains.html, courses.html, etc.).

---

## 1. Domain Assessment → Course Selection

### Location: `templates/domains.html` (Assessment Results Modal)

After user completes domain assessment and receives assessed_level, show course selection:

```html
<!-- In your assessment results modal -->
<div id="assessmentResultsModal">
    <h2>Assessment Complete!</h2>
    <p>Your Assessed Level: <span id="assessedLevel">Intermediate</span></p>
    
    <!-- List top 10 courses for this domain -->
    <div id="coursesForDomain">
        <!-- Populated by JavaScript -->
    </div>
    
    <button onclick="selectCourseAndStartLearning()">Start Learning Path</button>
</div>
```

### JavaScript Code to Add (domains.html):

```javascript
// After assessment completion
async function completeAssessment(domainId, score, level) {
    try {
        // Save assessment result
        const response = await fetch(`/api/domain/${domainId}/assess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                score: score, 
                assessed_level: level 
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Fetch and display courses for this domain
            const coursesResponse = await fetch(`/api/domain/${domainId}/courses`);
            const { courses } = await coursesResponse.json();
            
            // Render course selection UI
            const coursesDiv = document.getElementById('coursesForDomain');
            coursesDiv.innerHTML = courses.map(course => `
                <div class="course-card" onclick="selectCourse(${domainId}, ${course.course_link_id}, '${course.title}')">
                    <h3>${course.title}</h3>
                    <p>${course.description}</p>
                    <button>Select This Course</button>
                </div>
            `).join('');
            
            // Show modal
            showModal('assessmentResultsModal');
        }
    } catch (error) {
        console.error('Assessment error:', error);
    }
}

// When user selects a course
function selectCourse(domainId, courseLinkId, courseTitle) {
    // Navigate to course page with progress tracker
    window.location.href = `/courses/${courseLinkId}?domain=${domainId}`;
}
```

---

## 2. Course Page: Tutorial + Progress Tracking

### Location: `templates/learn.html` or `templates/courses.html`

Add a progress tracker and tutorial video player:

```html
<!-- Tutorial Video Section -->
<div class="course-container">
    <!-- Video Player -->
    <div class="video-player">
        <iframe id="courseVideo" width="100%" height="600" 
                src="https://www.youtube.com/embed/..." 
                title="Course Video">
        </iframe>
    </div>
    
    <!-- Progress Tracker -->
    <div class="progress-tracker">
        <h3>Learning Progress</h3>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
        </div>
        <p id="progressText">0 / 300 minutes (0%)</p>
        <p class="progress-hint" id="progressHint">Complete 5 hours of tutorials to unlock quiz</p>
        
        <!-- Quiz Unlock Button -->
        <button id="startQuizBtn" class="btn btn-primary" style="display: none;" onclick="startQuiz()">
            <i class="fas fa-edit"></i>
            Quiz Unlocked! Click to Start
        </button>
        <button id="markedCompleteBtn" class="btn btn-secondary" onclick="markTutorialComplete()">
            I've Watched the Tutorial
        </button>
    </div>
    
    <!-- Course Info -->
    <div class="course-info">
        <h2 id="courseTitle">Course Title</h2>
        <p id="courseDescription">Course description...</p>
    </div>
</div>
```

### JavaScript Code (add to courses.js or learn.js):

```javascript
let courseState = {
    domainId: null,
    courseLinkId: null,
    tutorialMinutes: 0,
    quizUnlocked: false
};

// Initialize course page
document.addEventListener('DOMContentLoaded', async function() {
    courseState.courseLinkId = getQueryParam('course_link_id');
    courseState.domainId = getQueryParam('domain');
    
    await loadCourseProgress();
    startAutomaticTimeTracking();
});

// Load and display course progress
async function loadCourseProgress() {
    try {
        const response = await fetch(
            `/api/domain/${courseState.domainId}/course/${courseState.courseLinkId}/progress`
        );
        const progress = await response.json();
        
        courseState.tutorialMinutes = progress.tutorial_minutes;
        courseState.quizUnlocked = progress.quiz_unlocked;
        
        updateProgressDisplay();
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

// Update UI based on progress
function updateProgressDisplay() {
    const percentage = (courseState.tutorialMinutes / 300) * 100;
    document.getElementById('progressFill').style.width = percentage + '%';
    document.getElementById('progressText').textContent = 
        `${courseState.tutorialMinutes} / 300 minutes (${Math.round(percentage)}%)`;
    
    // Show quiz button if unlocked
    if (courseState.quizUnlocked) {
        document.getElementById('startQuizBtn').style.display = 'block';
        document.getElementById('progressHint').textContent = '✅ Quiz Unlocked! You can now take the assessment.';
        document.getElementById('markedCompleteBtn').disabled = true;
    }
}

// Automatic time tracking (every minute)
function startAutomaticTimeTracking() {
    setInterval(async function() {
        try {
            await fetch(
                `/api/domain/${courseState.domainId}/course/${courseState.courseLinkId}/progress`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        minutes: 1,  // Add 1 minute
                        mark_complete: false
                    })
                }
            );
            
            // Reload progress
            await loadCourseProgress();
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }, 60000);  // Every 60 seconds
}

// Manual: Mark tutorial as complete
async function markTutorialComplete() {
    if (!confirm('Mark tutorial as complete? You cannot undo this.')) return;
    
    try {
        const response = await fetch(
            `/api/domain/${courseState.domainId}/course/${courseState.courseLinkId}/progress`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    minutes: 300,
                    mark_complete: true
                })
            }
        );
        
        if (response.ok) {
            await loadCourseProgress();
            alert('Tutorial marked complete! Quiz is now unlocked.');
        }
    } catch (error) {
        console.error('Error marking complete:', error);
        alert('Failed to mark tutorial complete');
    }
}

// Start quiz
async function startQuiz() {
    if (!courseState.quizUnlocked) {
        alert('You must complete 5 hours of tutorial before taking the quiz');
        return;
    }
    
    try {
        // Navigate to quiz page
        window.location.href = 
            `/domain/${courseState.domainId}/course/${courseState.courseLinkId}/quiz`;
    } catch (error) {
        console.error('Error starting quiz:', error);
        alert('Failed to start quiz');
    }
}

// Helper: Get URL query parameter
function getQueryParam(param) {
    const params = new URLSearchParams(window.location.search);
    return params.get(param);
}
```

---

## 3. Quiz Page: Full-Screen Proctored Quiz

### The quiz page is already implemented!

Just ensure this route exists in `app.py`:

```python
@app.route('/domain/<domain_id>/course/<course_link_id>/quiz')
def quiz_page(domain_id, course_link_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('domain_quiz.html')
```

The quiz template (`domain_quiz.html`) handles everything:
- Loading quiz data via API
- Enforcing fullscreen
- Detecting violations
- Sending heartbeats
- Submitting answers
- Redirecting to certificate on pass

---

## 4. Certificate Page: Display & Share

### Location: `templates/certificates.html`

The certificate page is already integrated! It:
1. Loads certificates via `/api/certificates`
2. Shows sample certificate first
3. Displays earned certificates below
4. Allows viewing, downloading, and sharing

Just make sure the certificates page links to:
- `href="/certificates"` - Main certificates page
- `href="/certificates/{cert_id}/view"` - Certificate detail view

---

## 5. Backend Routes Reference

### Routes That Need to Exist in `app.py`

```python
# Domain assessment
@app.route('/api/domain/<domain_id>/assess', methods=['POST'])

# Course listing for domain
@app.route('/api/domain/<domain_id>/courses', methods=['GET'])

# Progress tracking
@app.route('/api/domain/<domain_id>/course/<course_link_id>/progress', methods=['GET', 'POST'])

# Quiz management
@app.route('/api/domain/<domain_id>/course/<course_link_id>/quiz/start', methods=['POST'])
@app.route('/api/domain/<domain_id>/course/<course_link_id>/quiz/heartbeat', methods=['POST'])
@app.route('/api/domain/<domain_id>/course/<course_link_id>/quiz/violation', methods=['POST'])
@app.route('/api/domain/<domain_id>/course/<course_link_id>/quiz/submit', methods=['POST'])

# Certificate display
@app.route('/api/certificates', methods=['GET'])
@app.route('/api/certificates/<cert_id>', methods=['GET'])
@app.route('/certificates/<cert_id>/view', methods=['GET'])
@app.route('/certificates/<cert_id>/download', methods=['GET'])

# Quiz page
@app.route('/domain/<domain_id>/course/<course_link_id>/quiz', methods=['GET'])
```

All these routes are already implemented! ✅

---

## 6. CSS Classes & Styling

### Add to your CSS files as needed:

```css
/* Progress Tracker */
.progress-tracker {
    background: var(--bg-card);
    padding: 24px;
    border-radius: 12px;
    margin: 24px 0;
}

.progress-bar {
    width: 100%;
    height: 24px;
    background: var(--border-color);
    border-radius: 12px;
    overflow: hidden;
    margin: 16px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    transition: width 0.3s ease;
}

.progress-hint {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 12px;
}

/* Course Selection */
.course-card {
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.course-card:hover {
    transform: translateY(-4px);
    border-color: var(--accent-primary);
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
}

.course-card h3 {
    margin: 0 0 12px 0;
    color: var(--text-primary);
}

.course-card p {
    margin: 0 0 16px 0;
    color: var(--text-secondary);
    font-size: 0.95rem;
}

.course-card button {
    width: 100%;
}
```

---

## 7. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN ENROLLMENT                        │
│              (User takes assessment)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           COURSE SELECTION & START                          │
│     (Display 10 courses, user picks one)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│            TUTORIAL PROGRESS TRACKING                       │
│     (Use /progress endpoint to track 0-300 minutes)         │
│     (Automatic: +1 min/minute during viewing)               │
│     (Manual: +300 min "I've Watched" button)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
        (300 min)                       (<300 min)
           │                               │
           ↓                               ↓
    ✅ Quiz Unlocked              ⏳ Still Waiting
    "Start Quiz" visible          "X minutes left"
           │
           ↓
┌─────────────────────────────────────────────────────────────┐
│                  PROCTORED QUIZ                             │
│   (Full-screen, heartbeat, copy-paste prevention)           │
│   (30-minute time limit, score tracked)                     │
└──────────────────────────┬──────────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
 (70%+)        (<70%)
    │             │
    ↓             ↓
  PASS          FAIL
    │             │
    ↓             ↓
 ✅ Auto-    ❌ Retry Later
 Certificate  (Domain page)
    │
    ↓
┌─────────────────────────────────────────────────────────────┐
│            CERTIFICATE DISPLAY & SHARING                    │
│    (View, Download PDF/HTML, Share LinkedIn/Twitter)        │
│    (Unique code SF-DOMAIN-COURSE-HEX)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Testing Checklist

### Quiz Integration Testing
- [ ] Domain assessment completes successfully
- [ ] Courses displayed for selected domain
- [ ] Progress tracker shows 0/300 minutes initially
- [ ] Automatic time tracking increments every minute
- [ ] "I've Watched" button instantly unlocks quiz
- [ ] "Start Quiz" button appears when quiz_unlocked=true
- [ ] Quiz page loads in fullscreen
- [ ] Questions display correctly
- [ ] Options are clickable and selectable
- [ ] Previous/Next buttons work
- [ ] Submit button appears on last question

### Proctoring Testing
- [ ] Switching windows shows violation warning
- [ ] Copy attempts are blocked
- [ ] Ctrl+C/V/X/A are blocked
- [ ] Right-click menu is disabled
- [ ] Exiting fullscreen shows notice
- [ ] Heartbeat sent every 15 seconds
- [ ] 3+ violations auto-submit quiz
- [ ] Timer countdown works correctly
- [ ] Time = 0 auto-submits quiz

### Scoring & Certificate Testing
- [ ] 95% score → A+ grade
- [ ] 85% score → A- grade
- [ ] 65% score → C grade (fail, no cert)
- [ ] 70% score threshold enforced
- [ ] Certificate code unique (SF-XX-YY-HEX)
- [ ] Certificate displays user name, domain, course
- [ ] Sample certificate shows before passing

### UI/UX Testing
- [ ] Progress bar fills smoothly
- [ ] Timer color changes (warning at <10 min, danger at <5 min)
- [ ] All buttons respond to clicks
- [ ] Mobile responsive (landscape for quiz, portrait for cert)
- [ ] No JavaScript errors in console
- [ ] Graceful error handling (network errors, server errors)

---

## 9. Troubleshooting Integration

### "Quiz button not showing"
```javascript
// Debug: Check progress
fetch(`/api/domain/${domainId}/course/${courseLinkId}/progress`)
    .then(r => r.json())
    .then(data => console.log('Progress:', data));
    // Should show: quiz_unlocked: true
```

### "Quiz won't start full-screen"
```javascript
// Not all browsers/contexts allow requestFullscreen
// Try: Allow fullscreen in browser settings
// Try: Different browser (Chrome works best)
// Fallback: Warn user instead of requiring fullscreen
```

### "Certificate not appearing"
```javascript
// Debug: Check API response
fetch('/api/certificates')
    .then(r => r.json())
    .then(data => console.log('Certificates:', data));
    // Should include newly earned certificate
```

### "Heartbeat failing"
```python
# Debug: Check server logs
# Flask should show POST requests to /quiz/heartbeat
# If not appearing: Check browser network tab
# If 401: Session expired, re-login
```

---

## 10. Customization Points

### Change Quiz Duration
In `domain_quiz.html`, change `1800` to desired seconds:
```javascript
const remaining = 1800 - elapsed;  // 30 minutes = 1800 seconds
```

### Change Pass Threshold
In `app.py`, find `score_to_grade()` and adjust:
```python
if score >= 75:  # Change from 70% to 75%
    quiz_passed = True
```

### Change Grading Scale
In `score_to_grade()` function:
```python
def score_to_grade(score):
    if score >= 95: return 'A+'    # Adjust these thresholds
    elif score >= 90: return 'A'
    # etc.
```

### Change Certificate Code Format
In `generate_certificate_code()`:
```python
# Change from SF-DOMAIN-COURSE-HEX to custom format
return f"CERT-{uuid.uuid4().hex[:6]}"
```

### Change Certificate Design
Edit `certificate_view.html` CSS to customize:
- Gold gradient background
- Font styling
- Layout
- Signature lines
- Seal/badge

---

## 11. API Response Examples

### GET /api/certificates
```json
{
  "certificates": [
    {
      "id": "sample",
      "domain": "Sample Domain",
      "course_title": "Sample Course",
      "title": "Sample Certificate",
      "grade": "A",
      "score": 90,
      "isSample": true,
      "icon": "🏆",
      "date": "January 15, 2024"
    },
    {
      "id": 1,
      "domain": "Python",
      "course_title": "Python Fundamentals",
      "title": "Python Certificate",
      "grade": "A+",
      "score": 95,
      "isSample": false,
      "icon": "🐍",
      "date": "January 10, 2024"
    }
  ]
}
```

### POST /api/domain/{id}/course/{id}/quiz/submit
```json
// Request
{
  "session_token": "abc123...",
  "answers": {
    "0": 1,
    "1": 2,
    "2": 0,
    "3": 3
  }
}

// Response
{
  "score": 85,
  "passed": true,
  "grade": "A",
  "certificate_code": "SF-PYML-A1B2C3",
  "certificate_id": 12
}
```

---

## 12. Success Indicators

You've successfully integrated the system when:

✅ User completes domain assessment
✅ Course selection appears
✅ Progress tracker updates automatically
✅ Quiz unlocks after 5 hours
✅ Quiz page loads full-screen
✅ Heartbeat sent every 15 seconds
✅ Quiz submitted successfully
✅ Certificate auto-generated (if score >= 70%)
✅ Certificate viewable at /certificates/{id}/view
✅ Certificate downloadable as HTML
✅ Certificate shareable to LinkedIn/Twitter
✅ Multiple certificates displayed on /certificates page
✅ Sample certificate visible even without earned certs

---

## Quick Start

1. **Ensure these files exist**:
   - ✅ app.py (with all endpoints implemented)
   - ✅ templates/domain_quiz.html
   - ✅ templates/certificate_view.html
   - ✅ templates/certificates.html

2. **Update your course/learning page** with progress tracker HTML + JS

3. **Verify Flask is running**: `python app.py`

4. **Test the flow**: Assessment → Course Selection → Tutorial → Quiz → Certificate

5. **Check API responses**: Open browser DevTools, Network tab, look for API calls

6. **Debug any issues**: See Troubleshooting section above

---

**Integration Complete!** 🎉

Your SkillForge platform now has a fully-featured, proctored quiz and certificate system with automatic certificate generation upon successful completion.
