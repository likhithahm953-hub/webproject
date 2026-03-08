# Quiz & Certificate System - Implementation Complete

## Overview
A comprehensive quiz and certificate system for SkillForge with strict server-side proctoring, automatic certificate generation, and full tracking of user progress through domain-based learning paths.

## System Architecture

### Database Models

#### 1. **DomainCourseProgress**
Tracks user progress through tutorials for each domain+course combination.

```python
Fields:
- user_id (FK → User)
- domain_id (FK → Domain)
- course_link_id (FK → CourseLink)
- tutorial_minutes (0-300 min max)
- completed_at (timestamp)
- quiz_unlocked (bool) - triggers when tutorial_minutes >= 300
- quiz_passed (bool)
- created_at, updated_at (timestamps)
```

**Purpose**: Gate quiz access behind 5-hour (300 minutes) tutorial completion requirement.

---

#### 2. **DomainCourseQuiz**
Stores reusable quiz content per domain+course combination.

```python
Fields:
- domain_id (FK → Domain)
- course_link_id (FK → CourseLink)
- title (string)
- quiz_data (JSON)
  - questions (array)
    - id (int)
    - question (string)
    - options (array of 4 choices)
    - correct_index (0-3)
- created_at (timestamp)
```

**Purpose**: Standardize and persist quiz definitions for consistent testing across users.

---

#### 3. **DomainCourseQuizAttempt**
Records each user's quiz session with proctoring tracking.

```python
Fields:
- user_id (FK → User)
- domain_id (FK → Domain)
- course_link_id (FK → CourseLink)
- quiz_data (JSON) - copy of quiz at attempt time
- session_token (unique, 32-byte cryptographic)
- started_at (timestamp)
- last_heartbeat_at (timestamp) - updated every heartbeat
- completed_at (timestamp)
- score (0-100 percentage)
- total_questions (int)
- passed (bool) - true if score >= 70%
- invalidated (bool) - true if proctoring violation detected
- violation_reason (string) - 'focus_lost', 'heartbeat_timeout', etc.
```

**Purpose**: Track quiz sessions with cryptographic session tokens and heartbeat monitoring for proctoring enforcement.

---

#### 4. **DomainCertificate**
Issued certificates upon successful quiz completion.

```python
Fields:
- user_id (FK → User)
- domain_id (FK → Domain)
- course_link_id (FK → CourseLink)
- title (string)
- issuer (string) - 'SkillForge Academy'
- certificate_code (string) - format: SF-XX-YY-HEXCODE
- grade (string) - A+, A, A-, B+, B, C
- score (int) - 0-100%
- issued_at (timestamp)
- is_sample (bool) - for demo certificates
```

**Purpose**: Persistently store earned certificates with unique codes and automatic grading.

---

## API Endpoints

### Tutorial Progress Tracking

#### GET `/api/domain/<domain_id>/course/<course_link_id>/progress`
Returns current progress for user in domain+course.

**Response**:
```json
{
  "tutorial_minutes": 120,
  "completed": false,
  "quiz_unlocked": false,
  "quiz_passed": false
}
```

#### POST `/api/domain/<domain_id>/course/<course_link_id>/progress`
Update tutorial progress. Can be called repeatedly to increment minutes or mark completion.

**Request**:
```json
{
  "minutes": 30,
  "mark_complete": false
}
```

**Logic**:
- Adds `minutes` to current total (capped at 300 max)
- Automatically unlocks quiz when tutorial_minutes >= 300
- If `mark_complete=true`, sets quiz_unlocked=true immediately

**Response**: Updated progress object

---

### Quiz Session Management

#### POST `/api/domain/<domain_id>/course/<course_link_id>/quiz/start`
Create a new quiz attempt session.

**Validation**:
- Checks that quiz_unlocked=true (5 hours completed)
- Generates unique session_token

**Response**:
```json
{
  "quiz": {
    "title": "Python Basics Quiz",
    "description": "Test your Python knowledge",
    "questions": [
      {
        "id": 1,
        "question": "What is the correct way to import NumPy?",
        "options": ["import np", "import numpy as np", "from numpy import *", "require numpy"],
        "correct_index": 1
      }
    ]
  },
  "session_token": "abcd1234efgh5678ijkl9012mnop3456"
}
```

---

#### POST `/api/domain/<domain_id>/course/<course_link_id>/quiz/heartbeat`
Signal user activity within quiz. Called every 15 seconds from frontend.

**Request**:
```json
{
  "session_token": "abcd1234efgh5678ijkl9012mnop3456"
}
```

**Logic**:
- Updates `last_heartbeat_at` timestamp
- Returns error if session not found or already invalidated
- Detects missing heartbeats to flag focus loss

---

#### POST `/api/domain/<domain_id>/course/<course_link_id>/quiz/violation`
Record detected proctoring violation (window blur, copy attempt, etc.).

**Request**:
```json
{
  "session_token": "abcd1234efgh5678ijkl9012mnop3456",
  "reason": "focus_lost"
}
```

**Logic**:
- Sets attempt.invalidated=true
- Records violation_reason
- Prevents quiz submission (auto-fails)
- Counts violations for potential auto-termination

---

#### POST `/api/domain/<domain_id>/course/<course_link_id>/quiz/submit`
Submit quiz answers and score the attempt.

**Request**:
```json
{
  "session_token": "abcd1234efgh5678ijkl9012mnop3456",
  "answers": {
    "0": 1,
    "1": 2,
    "2": 0
  }
}
```

**Scoring Logic**:
1. Compares each answer[i] against correct_index
2. Calculates percentage: (correct_count / total) * 100
3. Checks score >= 70% threshold
4. Auto-grades using score_to_grade() function
5. If passed AND not invalidated: creates DomainCertificate
6. Returns {score, passed, grade, certificate_code, certificate_id}

**Response**:
```json
{
  "score": 85,
  "passed": true,
  "grade": "A",
  "certificate_code": "SF-PYML-A1B2C3",
  "certificate_id": 12
}
```

---

### Certificate Management

#### GET `/api/certificates`
Get all certificates for logged-in user.

**Response**:
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

**Note**: Sample certificate always returned first to show demo certificate before user completes any course.

---

#### GET `/api/certificates/<cert_id>`
Get detailed certificate data for viewing/displaying.

**Response**:
```json
{
  "certificate": {
    "id": 1,
    "domain": "Python",
    "title": "Python Fundamentals",
    "issuer": "SkillForge Academy",
    "issued_at": "2024-01-10T14:32:00",
    "certificate_code": "SF-PYML-A1B2C3",
    "grade": "A+",
    "score": 95
  },
  "user_name": "John Doe"
}
```

---

#### GET `/certificates/<cert_id>/view`
Renders certificate_view.html template with certificate display and sharing options.

---

#### GET `/certificates/<cert_id>/download`
Download certificate as HTML file attachment.

---

## Frontend Templates

### 1. **domain_quiz.html**
Full-screen, proctored quiz interface with:

**Proctoring Features**:
- ✅ Fullscreen enforcement (requestFullscreen API)
- ✅ Tab/window blur detection (recordViolation on blur)
- ✅ Copy/paste prevention (preventDefault on contextmenu, copy, cut, paste)
- ✅ Right-click context menu disabled
- ✅ Keyboard shortcuts blocked (Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+A)
- ✅ Heartbeat monitoring (POST every 15 seconds)
- ✅ Violation tracking (3+ violations = auto-submit)
- ✅ 30-minute timer with visual warnings (warning at <10 min, danger at <5 min)

**UI Elements**:
- Question display (1 question per screen)
- Radio button options with immediate selection feedback
- Progress bar showing completion percentage
- Previous/Next navigation (Previous disabled on first question)
- Submit button (shown on last question)
- Violation warning banner (displayed when fullscreen exits or copy attempted)
- Proctoring notice (explains monitoring and consequences)

**Scoring/Result Flow**:
- On submit: POST to /quiz/submit with answers and session_token
- If passed: redirect to `/certificates/<cert_id>/view`
- If failed: redirect to domain page to retry

---

### 2. **certificate_view.html**
Beautiful certificate display with permanent and shareable format.

**Display**:
- Full-width certificate design (gold gradient background, official styling)
- User name, domain, course, score, grade, date
- Certificate code (unique identifier)
- Signature lines and issuer details

**Actions**:
- Print (browser print dialog)
- Download (as HTML file)
- Share LinkedIn (with pre-filled text)
- Share Twitter (with certificate details emoji)
- Copy Share Link (to clipboard)
- Back (navigate to previous page)

**Details Panel**:
- Achievement status (Completed badge)
- Course details (Domain, Course name)
- Performance stats (Score %, Grade)
- Verification badge (Verified & Authentic)

---

## Helper Functions

### score_to_grade(score)
Maps numerical score to letter grade:
- 95+ → A+
- 90+ → A
- 85+ → A-
- 80+ → B+
- 75+ → B
- <75 → C

### generate_certificate_code(domain_name, course_title)
Generates unique certificate code format:
```
SF-{domain_2_chars}{course_2_chars}-{3_random_hex_bytes}
Example: SF-PYML-A1B2C3
```

### build_course_quiz(domain_name, course_title, num_questions=10)
Generates quiz payload with questions, options, and correct answers:
```python
{
  "title": "Python Basics Quiz",
  "description": "Test your knowledge...",
  "questions": [
    {
      "id": 0,
      "question": "What is...?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 1
    }
  ]
}
```

---

## Security & Data Integrity

### Session Token System
- ✅ 32-byte cryptographically random tokens (secrets.token_urlsafe)
- ✅ Tokens stored in DomainCourseQuizAttempt
- ✅ Tokens validated on every heartbeat/submission
- ✅ Tokens cannot be reused after submission

### Proctoring Enforcement
- ✅ Heartbeat timeout detection (15-second window)
- ✅ Invalidation flag prevents score submission if violations present
- ✅ User focus loss recorded (blur event)
- ✅ Copy/paste attempts blocked and logged
- ✅ Auto-submit on 3+ violations

### Database Constraints
- ✅ Cascade delete (parent domain deletion removes all related records)
- ✅ Foreign key relationships enforce referential integrity
- ✅ user_id checks prevent cross-user certificate access
- ✅ All API endpoints check session['user_id'] before proceeding

### Grading System
- ✅ 70% pass threshold enforced server-side
- ✅ Invalidated attempts automatically fail (even if score >= 70%)
- ✅ Grade assigned based on score (not user-submitted)
- ✅ Certificate code generated only on successful pass

---

## User Journey

### Complete Flow
```
1. User enrolls in domain
2. Completes assessment (gets enrolled + assessed_level recorded)
3. Navigates to course link page
4. Starts tutorial video/content
5. System tracks tutorial time (manual OR automatic via heartbeat)
6. After 5 hours: Quiz button unlocks
7. User clicks "Start Quiz" → POST /quiz/start
8. Kernel enforced fullscreen, heartbeat starts, proctoring active
9. User answers all questions
10. User submits → POST /quiz/submit with answers
11. Backend scores answers, checks >= 70% threshold
12. If passed: DomainCertificate created, auto-redirect to certificate view
13. If failed: Redirect to domain to retry (after allowing retake cooldown)
14. User views, downloads, or shares certificate
15. Certificate appears in /certificates page with all other certificates
```

---

## Configuration & Thresholds

| Parameter | Value | Notes |
|-----------|-------|-------|
| Tutorial Duration | 300 minutes (5 hours) | Tutorial_minutes >= 300 unlocks quiz |
| Pass Threshold | 70% | Score must be >= 70 to pass |
| Heartbeat Interval | 15 seconds | Client sends heartbeat every 15 sec |
| Max Quiz Time | 30 minutes | Auto-submit when time expires |
| Violation Threshold | 3 | Auto-submit after 3 violations |
| Fullscreen Required | Yes | Quiz enforces fullscreen mode |
| Copy/Paste Block | Yes | All copy, cut, paste attempts blocked |
| Tab Switching | Tracked | Records violation and shows warning |

---

## Database Migrations

The system automatically creates/updates columns on startup:

```python
# Added to DomainEnrollment:
assessed_level = db.Column(db.String(50), nullable=True)

# Created tables:
- DomainCourseProgress
- DomainCourseQuiz
- DomainCourseQuizAttempt
- DomainCertificate
```

All migrations are backward compatible (uses nullable fields for existing data).

---

## Testing Checklist

- [ ] User 1: Complete 5 hours of tutorial, quiz unlocks
- [ ] User 2: Score 85% on quiz, certificate auto-generated
- [ ] User 3: Score 65% on quiz, certificate NOT generated
- [ ] User 4: Switch window during quiz, violation recorded
- [ ] User 5: Exit fullscreen, notice shown and violation recorded
- [ ] User 6: Attempt copy/paste, blocked and violation recorded
- [ ] User 7: View own certificates, sample shown first
- [ ] User 8: Download certificate as HTML
- [ ] User 9: Share certificate on LinkedIn/Twitter
- [ ] User 10: Certificate accessible only by owner (403 forbidden for others)

---

## Frontend JavaScript Components

### domain_quiz.js (embedded in domain_quiz.html)
- quizState: Global state for quiz session
- setupProctoring(): Sets up violation detection
- startQuiz(): Initializes quiz from backend
- renderQuestions(): Displays current question
- selectAnswer(): Handles radio button selection
- nextQuestion/previousQuestion(): Navigation
- recordViolation(): Logs proctoring violations
- sendHeartbeat(): Periodic server check-in
- submitQuiz(): Scores and submits to backend
- updateTimer(): Countdown with color warnings

### certificate_view.js (embedded in certificate_view.html)
- renderCertificate(): Displays loaded certificate data
- downloadCertificate(): Creates HTML download link
- shareCertificate(): Uses native share API or manual share
- shareLinkedIn/shareTwitter(): Pre-filled social posts
- copyShareLink(): Clipboard copy of certificate URL

---

## API Integration Points

### From domains.html:
```javascript
// After assessment, link to course:
window.location.href = `/domain/${domainId}/course/${courseLinkId}`;
```

### From course page:
```javascript
// Start quiz if unlocked:
async function startQuiz() {
  const response = await fetch(
    `/api/domain/${domainId}/course/${courseLinkId}/quiz/start`,
    { method: 'POST' }
  );
  const { quiz, session_token } = await response.json();
  // Redirect to quiz page
  window.location.href = `/domain/${domainId}/course/${courseLinkId}/quiz`;
}
```

### From certificates page:
```javascript
// Load all certificates:
async function loadCertificates() {
  const response = await fetch('/api/certificates');
  const { certificates } = await response.json();
  // Render to page
}
```

---

## Performance & Scalability

- ✅ Session tokens: O(1) lookup
- ✅ Heartbeat: Lightweight timestamp update
- ✅ Certificate generation: Calculated on-the-fly, cached in DB
- ✅ Quiz queries: Indexed by user_id + domain_id + course_link_id
- ✅ No long-polling: Heartbeat is fire-and-forget POST

---

## Future Enhancements

1. **Proctoring AI**: Integrate face recognition (Proctorio, Honorlock)
2. **Retake Cooldown**: Enforce 24-hour wait before retaking failed quiz
3. **Adaptive Difficulty**: Adjust question difficulty based on performance
4. **Leaderboards**: Show top performers by domain
5. **Email Notifications**: Send certificate issued emails
6. **Peer Review**: Allow peer assessment of certificate-holders
7. **Blockchain Certificates**: Immutable cert records on blockchain
8. **Certificate Revocation**: Admin ability to revoke fraudulent certificates
9. **Quiz Analytics**: Dashboard showing pass rates, common mistakes
10. **Timed Practice**: Unlimited practice quizzes before official attempt

---

## Troubleshooting

### Quiz won't start
- Check: User has completed 5 hours of tutorials (progress.quiz_unlocked = true)
- Check: Session token generated successfully
- Check: Course exists and is linked to domain

### Certificate not generated despite passing score
- Check: Score >= 70%
- Check: attempt.invalidated != true (no proctoring violations)
- Check: User passed all questions (not just lucky guesses)

### Heartbeat timeout
- Check: Client sending heartbeat every 15 seconds
- Check: Server '/quiz/heartbeat' endpoint reachable
- Check: Session token valid (not invalidated)

### Session tamper detection
- All session tokens are 32-byte random (cannot guess)
- Answers submitted must reference same session_token
- Any mismatch results in 401 error

---

## Code References

| Component | File | Lines |
|-----------|------|-------|
| Models | app.py | 208-283 |
| Helper Functions | app.py | 2820-2900 |
| API Endpoints | app.py | 2949-3350 |
| Certificate Styling | certificates.css | 164-240 |
| Quiz Template | domain_quiz.html | Full file |
| Certificate View | certificate_view.html | Full file |

---

**Implementation Date**: January 2024
**Status**: ✅ Complete and Ready for Testing
**Last Updated**: Today
