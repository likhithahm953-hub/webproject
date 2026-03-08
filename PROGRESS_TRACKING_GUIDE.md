# Progress Tracking & Quiz Unlock System - Testing Guide

## Overview

The system works in these steps:

```
1. Dashboard → Continue Button → Learning Page (domain_learn.html)
2. Learning Page → Open Course Link (YouTube/Udemy/Coursera)
3. Track Progress → Log Minutes of Learning
4. 300 Minutes Complete → Quiz Button Unlocks
5. Take Quiz → Upon Pass → Certificate Issued
```

---

## System Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│  Dashboard (User Sees 3 Domains)                    │
│  - Python Programming (72% progress)                │
│  - Data Science (44% progress)                      │
│  - Machine Learning (21% progress)                  │
└──────────────┬──────────────────────────────────────┘
               │
               ↓ Click "Continue"
               │
┌──────────────────────────────────────────────────────┐
│  Learning Page (/domain/<id>/learn)                 │
│  - Shows course title & metadata                    │
│  - Links to external course (YouTube, Udemy, etc)   │
│  - Progress bar (0/300 minutes)                     │
│  - Quiz button (DISABLED)                           │
└──────────────┬───────────────────────────────────────┘
               │
               ↓ Log progress minutes
               │
┌──────────────────────────────────────────────────────┐
│  API: POST /api/domain/<id>/course/<id>/progress    │
│  - Stores tutorial_minutes                          │
│  - Marks completed when minutes >= 300              │
└──────────────┬───────────────────────────────────────┘
               │
               ↓ Load progress (every 30s)
               │
┌──────────────────────────────────────────────────────┐
│  Check Progress                                      │
│  - Get tutorial_minutes from DB                     │
│  - Calculate percentage (minutes/300 * 100)         │
│  - If >= 300: Unlock Quiz Button                    │
└──────────────┬───────────────────────────────────────┘
               │
               ↓ Click "Start Quiz Now!"
               │
┌──────────────────────────────────────────────────────┐
│  Quiz Page (/domain/<id>/course/<id>/quiz)          │
│  - AI-generated assessment questions                │
│  - User answers questions                           │
│  - Get score & pass/fail status                     │
└──────────────┬───────────────────────────────────────┘
               │
               ↓ Pass Quiz
               │
┌──────────────────────────────────────────────────────┐
│  Certificate Issued                                  │
│  - Stored in DomainCertificate table                │
│  - User can view & share on /certificates           │
└──────────────────────────────────────────────────────┘
```

---

## Database Involved

### 1. **DomainEnrollment**
- Tracks user's enrollment in each domain
- Stores selected_level (Zero, Beginner, Intermediate, Advanced)
- Stores assessed_level (after assessment quiz)
- Stores learning_phase (assessment, course-learning, quiz)

### 2. **CourseLink**
- External course URLs (YouTube, Udemy, Coursera, etc.)
- Stores title, URL, source, rating, price, difficulty

### 3. **DomainCourseProgress**
- Tracks learning progress per domain/course combination
- **KEY**: `tutorial_minutes` - accumulated minutes spent learning
- `completed_at` - timestamp when 300 minutes reached
- `quiz_unlocked` - boolean flag
- `quiz_passed` - boolean flag

### 4. **DomainCourseQuizAttempt**
- Records each quiz attempt
- Stores `score`, `total_questions`, `passed` status
- Prevents cheating with `session_token`, `heartbeat`, `invalidated`

### 5. **DomainCertificate**
- Issued when quiz is passed
- Stores `score`, `grade`, `issued_at`
- Can be viewed and shared

---

## How Progress Tracking Works

### Step 1: Load Progress
```javascript
// Called on page load and every 30 seconds
GET /api/domain/{domainId}/course/{courseId}/progress
```

Returns:
```json
{
  "tutorial_minutes": 120,      // Current hours logged
  "completed": false,           // If >= 300 minutes
  "quiz_unlocked": false,       // If completed
  "quiz_passed": false          // If passed quiz
}
```

### Step 2: Update Progress
```javascript
// When user logs time spent learning
POST /api/domain/{domainId}/course/{courseId}/progress
{
  "minutes": 60,        // Minutes to add
  "mark_complete": false // Auto-complete if >= 300
}
```

### Step 3: Check for Unlock
```javascript
if (minutes >= 300) {
  // Quiz button becomes enabled
  // Progress bar turns green
  // Button text changes to "Start Quiz Now!"
}
```

---

## Testing Demo

### Method 1: Using Testing Panel (Easiest)

When you visit `/domain/<id>/learn`, there's a hidden testing panel at the bottom of the Quiz section:

```
Demo Testing Panel
┌─────────────────────────────────────┐
│ [Input: Enter minutes] [Add Button] │
│                                     │
│ [1h] [2h] [Complete (5h)]          │
└─────────────────────────────────────┘
```

**Quick Test Steps:**

1. **Login** to your account
2. **Enroll in a domain** (e.g., "Python Programming")
3. **Go to Dashboard** → Click "Continue"
4. **You land on the Learning Page**
5. **In the Testing Panel:**
   - Option A: Click **"Complete (5h)"** button
   - Option B: Enter "300" and click "Add"
6. **Watch the progress bar fill to 100%**
7. **Quiz button will change from red (locked) to green (unlocked)**
8. **Click "Start Quiz Now!" to take the assessment**

### Method 2: Manual Testing via Browser Console

1. Open the Learning page
2. Open Developer Console (F12 → Console tab)
3. Run these commands:

```javascript
// Add 60 minutes
logProgress(60);

// Add 120 minutes (2 hours)
logProgress(120);

// Complete remaining minutes to reach 300
logProgress(120);

// Check current state
loadProgress();
```

### Method 3: Database Direct Update

If you have database access, you can directly update:

```sql
-- For testing only - add 300 minutes to current user's progress
UPDATE domain_course_progress 
SET tutorial_minutes = 300, completed_at = datetime('now')
WHERE user_id = 1 AND domain_id = 1 AND course_link_id = 1;
```

---

## Expected Behavior Timeline

### Initial State (0 minutes logged)
```
📊 Progress: 0%
⏳ Status: Quiz Locked
🔴 Quiz Button: Disabled (gray, shows "300 minutes remaining")
📈 Progress Bar: Empty (0/300 min)
```

### After Adding 60 Minutes
```
📊 Progress: 20%
⏳ Status: Quiz Locked
🔴 Quiz Button: Disabled (shows "240 minutes remaining")
📈 Progress Bar: 20% filled (60/300 min)
```

### After Adding 120 More Minutes (Total: 180)
```
📊 Progress: 60%
⏳ Status: Quiz Locked
🔴 Quiz Button: Disabled (shows "120 minutes remaining")
📈 Progress Bar: 60% filled (180/300 min)
```

### After Adding 120 More Minutes (Total: 300)
```
📊 Progress: 100% ✅
⏳ Status: Quiz Unlocked!
🟢 Quiz Button: Enabled (green, shows "Start Quiz Now!")
📈 Progress Bar: 100% filled (300/300 min)
💚 Progress fill color: Green
```

### When User Clicks Quiz Button
```
1️⃣ Redirects to: /domain/{id}/course/{id}/quiz
2️⃣ AI generates 10 assessment questions
3️⃣ User answers questions
4️⃣ System calculates score
5️⃣ If passing (typically 70%+): Certificate issued
6️⃣ User can view certificate on /certificates page
```

---

## Console Logs (Debugging)

When in the testing panel or via console, you'll see helpful logs:

```
🚀 Domain Learning Page Initialized
📖 System Workflow:
1️⃣ User clicks "Continue" button on dashboard
2️⃣ Lands on this learning page
3️⃣ Opens external course link (YouTube, Udemy, etc)
4️⃣ Logs learning hours (manually or via tracking)
5️⃣ Once 300 minutes logged → Quiz button unlocks
6️⃣ User takes assessment quiz
7️⃣ Upon passing → Certificate is issued

📊 Loading progress for domain 1, course 5
Progress data received: {tutorial_minutes: 120, ...}
Updating UI - Minutes: 120, Percent: 40%, Completed: false
⏳ Quiz locked. 180 minutes remaining until unlock.
```

---

## Files Involved

1. **Frontend:**
   - `templates/domain_learn.html` - Learning page with progress UI
   - `static/dashboard.js` - Dashboard with "Continue" buttons

2. **Backend:**
   - `app.py` - Routes and API endpoints
   - `/api/domain/<id>/course/<id>/progress` - GET/POST progress

3. **Database:**
   - `DomainCourseProgress` - Stores minutes
   - `DomainCourseQuizAttempt` - Stores quiz attempts
   - `DomainCertificate` - Stores issued certificates

---

## Full Test Case Walkthrough

### Test Case: "Complete Learning Path for Python Programming"

**Setup:**
- User: `testuser` (already logged in)
- Domain: Python Programming (ID: 2)
- Course: "The Complete Python Course" from Udemy

**Steps:**

1. ✅ **Navigate to Dashboard**
   - URL: `http://localhost:5000/dashboard`
   - See: 3 domains with "Continue" buttons

2. ✅ **Click Continue on Python Programming**
   - Redirected to: `/domain/2/learn`
   - See: Course title, metadata, progress bar (0%)

3. ✅ **Open External Course**
   - Click "Open Course" button
   - Opens Udemy course in new tab
   - User would watch videos (in real scenario)

4. ✅ **Log Learning Progress**
   - Return to learning page (keep it open)
   - In Testing Panel, click: `[Complete (5h)]`
   - Watch progress bar animate to 100%

5. ✅ **Quiz Button Unlocks**
   - Notice quiz button color changes from gray to green
   - Button text: "Start Quiz Now!"
   - Button is now clickable

6. ✅ **Take Assessment Quiz**
   - Click "Start Quiz Now!"
   - Redirected to: `/domain/2/course/5/quiz`
   - Answer 10 AI-generated questions about Python

7. ✅ **Submit Quiz**
   - Get score and pass/fail result
   - If passing (70%+): Certificate generated
   - If failing: Can retake later

8. ✅ **View Certificate**
   - Redirect to certificate page
   - See: Certificate with score, grade, date
   - Can download, share on LinkedIn/Twitter

---

## Troubleshooting

### Quiz Button Not Unlocking
```
Check:
1. Progress bar shows 100%? (If not, add more minutes)
2. Minutes in DB >= 300? (SELECT tutorials_minutes FROM...)
3. Console shows "✅ Quiz unlocked"? (Open F12)
4. Page cached? (Hard refresh: Ctrl+Shift+R)
```

### Minutes Not Saving
```
Check:
1. Network tab in DevTools (F12 → Network)
2. POST request to /api/domain/.../progress
3. Response status: 200 OK?
4. Response body shows updates?
5. Database updated? (Query DB directly)
```

### Quiz Not Starting
```
Check:
1. User enrolled in domain? (Check DomainEnrollment table)
2. Course link exists? (Check CourseLink table)
3. Quiz endpoint accessible? (/domain/<id>/course/<id>/quiz)
4. Gemini API configured? (For AI question generation)
```

---

## API Reference

### GET Progress
```
GET /api/domain/{domain_id}/course/{course_id}/progress

Response:
{
  "tutorial_minutes": 120,
  "completed": false,
  "quiz_unlocked": false,
  "quiz_passed": false
}
```

### POST Progress
```
POST /api/domain/{domain_id}/course/{course_id}/progress

Body:
{
  "minutes": 60,           // Minutes to add
  "mark_complete": false   // Auto-complete if >= 300
}

Response:
{
  "tutorial_minutes": 180,
  "completed": false,
  "quiz_unlocked": false,
  "quiz_passed": false
}
```

### Submit Quiz
```
POST /api/domain/{domain_id}/course/{course_id}/quiz/submit

Body:
{
  "session_token": "xyz123",
  "answers": {
    "1": "option_a",
    "2": "option_b",
    ...
  }
}

Response:
{
  "score": 85,
  "grade": "A",
  "passed": true,
  "certificate_id": 42
}
```

---

## Success Criteria

✅ User can enroll in domain  
✅ Dashboard shows "Continue" button  
✅ Learning page displays course link  
✅ Progress tracking works (can see minutes logged)  
✅ Quiz button unlocks at 300 minutes  
✅ Quiz questions display properly  
✅ Scoring calculates correctly  
✅ Certificate issues upon passing  
✅ Certificate visible on /certificates page  

---

## Notes

- **Real Scenario**: Users actually spend time on external courses
- **Testing Scenario**: Use the quick-add buttons to simulate 300 minutes instantly
- **Minutes Auto-Lock**: System automatically prevents adding more than 300 minutes
- **Quiz Attempts**: Users can retake quizzes multiple times
- **Certificate**: One certificate per domain (latest attempt counts)
- **Progress Refresh**: Checks every 30 seconds for real-time updates
