# SkillForge Avatar Management - User Flow Diagram

## 🎯 User Journey Map

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER PROFILE PAGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROFILE PICTURE SECTION                                 │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                            │  │
│  │  ┌────────────────────┐                                  │  │
│  │  │                    │                                  │  │
│  │  │   AVATAR IMAGE     │ ◎  ← CAMERA ICON                │  │
│  │  │   (120x120px)      │ /  (40x40px, appears on hover) │  │
│  │  │                    │                                  │  │
│  │  └────────────────────┘                                  │  │
│  │       ▲                                                    │  │
│  │       │                                                    │  │
│  │       └─ User hovers over avatar                          │  │
│  │                                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Click Camera Icon
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EDIT MENU APPEARS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                  ┌──────────────────────┐                       │
│                  │ 📷 Upload Photo      │                       │
│                  ├──────────────────────┤                       │
│                  │ 🗑️ Remove Photo      │ (if exists)          │
│                  ├──────────────────────┤                       │
│                  │ ❌ Cancel            │                       │
│                  └──────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
        │                           │                        │
        │ Click Upload             │ Click Remove          │ Click Cancel
        ▼                           ▼                        ▼
     [FLOW A]              [FLOW B: Remove]        Menu closes
```

---

## 🔄 FLOW A: Upload Photo

```
┌─────────────────────────────────┐
│  User Clicks "Upload Photo"     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  File Browser Opens             │
│  (Accept: .jpg, .png, .gif)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  User Selects Image File        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  File Validation                │
│  ✓ Size: ≤ 5MB                  │
│  ✓ Format: JPG/PNG/GIF          │
└────────────┬────────────────────┘
             │
        YES  │  NO
        ┌────┴─────┐
        │           │
        ▼           ▼
    CONTINUE    ERROR MSG
        │       (Show alert)
        │           │
        │           ▼
        │      Menu stays open
        │           │
        │           ▼
        │      User retries
        │
        ▼
┌─────────────────────────────────┐
│  Live Preview                   │
│  (Image shown in avatar)        │
│  (Upload button appears)        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  User Clicks "Upload"           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  BACKEND PROCESSING             │
│  1. Validate file again         │
│  2. Save to disk                │
│  3. Update database             │
│  4. Delete old file             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Success Message                │
│  "Avatar uploaded"              │
│  Page refresh (optional)        │
└─────────────────────────────────┘
```

---

## 🗑️ FLOW B: Remove Photo

```
┌──────────────────────────────────┐
│  User Clicks "Remove Photo"      │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  Confirmation Dialog             │
│  "Remove your profile picture?"  │
│  [Yes] [No]                      │
└────────────┬───────────────────┬─┘
             │                   │
        YES  │               NO  │
             ▼                   ▼
        PROCESS               CANCEL
             │              (Dialog closes,
             │               menu may close)
             │
             ▼
┌──────────────────────────────────┐
│  BACKEND PROCESSING              │
│  1. Verify user logged in        │
│  2. Delete file from disk        │
│  3. Clear avatar from database   │
│  4. Handle errors gracefully     │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  Success & Redirect              │
│  "Profile picture removed"       │
│  Avatar reverts to initial       │
│  Remove option disappears        │
└──────────────────────────────────┘
```

---

## 🏗️ Technical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HTML: profile.html                                  │  │
│  │  ├── Avatar Display Element                          │  │
│  │  ├── Edit Overlay with Camera Icon                   │  │
│  │  ├── Edit Menu (Hidden, toggle on click)             │  │
│  │  └── File Input (Hidden, opened by menu)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CSS: profile.css                                    │  │
│  │  ├── Avatar styling (120x120, gradient bg)           │  │
│  │  ├── Overlay styling (circular, positioned)          │  │
│  │  ├── Menu styling (dropdown, animation)              │  │
│  │  └── Responsive media queries                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JavaScript: profile.js                              │  │
│  │  ├── Event listeners (click, change)                 │  │
│  │  ├── File preview (FileReader API)                   │  │
│  │  ├── Menu toggle logic                               │  │
│  │  ├── Form submission handling                        │  │
│  │  └── API calls (remove-avatar)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ HTTP Requests
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask/Python)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  @app.route('/profile', methods=['GET','POST'])      │  │
│  │                                                       │  │
│  │  GET: Render profile template                        │  │
│  │       └─ Get user from session                       │  │
│  │       └─ Load avatar filename                        │  │
│  │                                                       │  │
│  │  POST: Handle avatar upload                          │  │
│  │       ├─ Validate authentication                     │  │
│  │       ├─ Check file exists                           │  │
│  │       ├─ Validate file type (JPG/PNG/GIF)            │  │
│  │       ├─ Validate file size (≤5MB)                   │  │
│  │       ├─ Generate unique filename                    │  │
│  │       ├─ Save to static/uploads/                     │  │
│  │       ├─ Update database user.avatar                 │  │
│  │       └─ Redirect with success message               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  @app.route('/api/remove-avatar', methods=['POST'])  │  │
│  │                                                       │  │
│  │  ├─ Validate authentication                          │  │
│  │  ├─ Get user from session                            │  │
│  │  ├─ Check if avatar exists                           │  │
│  │  ├─ Delete file from disk (try/except)               │  │
│  │  ├─ Clear user.avatar in database                    │  │
│  │  ├─ Commit changes                                   │  │
│  │  └─ Redirect with success message                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ ORM Queries
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  User Table                                          │  │
│  │  ├── id (Primary Key)                                │  │
│  │  ├── username (String, Unique)                       │  │
│  │  ├── email (String, Unique)                          │  │
│  │  ├── password_hash (String)                          │  │
│  │  ├── avatar (String) ← AVATAR FILENAME               │  │
│  │  ├── created_at (DateTime)                           │  │
│  │  └── role (String, Default='user')                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ File I/O
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FILE SYSTEM                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  static/                                                    │
│  └── uploads/                                               │
│      ├── user1_1707060000_profile.jpg    (120KB)           │
│      ├── user2_1707059000_avatar.png     (85KB)            │
│      ├── user3_1707058000_pic.gif        (200KB)           │
│      └── ...                                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
Upload Flow:
User Selects File
    ↓
Frontend: FileReader API
    ├─ Read file
    ├─ Preview in DOM
    ├─ Show upload button
    ↓
User Clicks Upload
    ↓
Frontend: Form Submission (POST /profile)
    ├─ multipart/form-data
    ├─ Include file object
    ↓
Backend: File Validation
    ├─ Check MIME type
    ├─ Check file size
    ├─ Validate extension
    ↓
Backend: File Processing
    ├─ Generate unique filename (username_timestamp_ext)
    ├─ Save to disk
    ├─ Update database (user.avatar = filename)
    ↓
Frontend: Redirect
    ├─ /profile with success message
    ├─ Display new avatar
    ├─ Update navbar avatar
    ↓
User Sees Updated Profile ✓


Remove Flow:
User Clicks Remove
    ↓
Frontend: Confirmation Dialog
    ├─ "Are you sure?"
    ├─ Show yes/no buttons
    ↓
User Confirms (if yes)
    ↓
Frontend: Form Submission (POST /api/remove-avatar)
    ├─ No file data
    ├─ Session validation
    ↓
Backend: User Verification
    ├─ Check session exists
    ├─ Get user from DB
    ├─ Verify avatar exists
    ↓
Backend: File Cleanup
    ├─ Delete file from disk
    ├─ Handle errors gracefully
    ↓
Backend: Database Update
    ├─ user.avatar = None
    ├─ Commit changes
    ↓
Frontend: Redirect
    ├─ /profile with success message
    ├─ Avatar reverts to initial
    ├─ Remove option disappears
    ↓
User Sees Profile Without Avatar ✓
```

---

## 🎨 UI State Diagram

```
AVATAR DISPLAY STATES:

State 1: No Avatar
┌──────────────────┐
│   [A] (Initial)  │ ◎  ← Camera icon (on hover)
└──────────────────┘

         ↓ (User uploads photo)

State 2: Has Avatar
┌──────────────────┐
│  [Avatar Image]  │ ◎  ← Camera icon (always visible)
└──────────────────┘

         ↓ (User clicks camera)

State 3: Menu Open
┌──────────────────┐
│  [Avatar Image]  │ ◎
└──────────────────┘
  ┌─────────────────┐
  │ 📷 Upload Photo │
  │ 🗑️ Remove Photo │
  │ ❌ Cancel       │
  └─────────────────┘

  ├─ Upload Path ──→ File selection → Preview → Upload
  │
  └─ Remove Path ──→ Confirmation → Delete → Refresh


File Size Chart:
────────────────────────────────────────────────────────
0MB     1MB     2MB     3MB     4MB     5MB (MAX)
│────────────────────────────────────────────│
Ideal    Average    Large    Too Large    Error
(< 1MB) (1-2MB)   (2-4MB)   (4-5MB)     (> 5MB)
```

---

## 📊 Database State Transitions

```
User Lifecycle with Avatar:

REGISTRATION
    ↓
User Created: avatar = NULL
    ├─ Can view profile
    ├─ Camera icon visible
    ├─ Upload option available
    ├─ Remove option hidden
    
    ├─ User Uploads Avatar
    │   ↓
    │   avatar = "user_1707060000_photo.jpg"
    │   ├─ Avatar displays
    │   ├─ Remove option shows
    │   ├─ Upload replaces
    │
    │   ├─ User Removes Avatar
    │   │   ↓
    │   │   avatar = NULL
    │   │   ├─ Avatar hides
    │   │   ├─ Remove option hides
    │   │   ├─ Upload ready again
    │   │
    │   └─ User Replaces Avatar
    │       ├─ Old file deleted
    │       ├─ New file saved
    │       ├─ Database updated
    │       └─ Display refreshes
    │
    └─ User Deletes Account
        ├─ Avatar file deleted
        ├─ User record deleted
        └─ Space freed
```

---

## 🔐 Security Flow

```
Authentication Check
    ↓
@session.get('user') ?
    ├─ YES → Continue
    └─ NO → Redirect to Login
    
    ↓
File Type Validation
    ├─ Check extension (.jpg, .png, .gif)
    ├─ Check MIME type
    └─ Whitelist only → Accept : Reject
    
    ↓
File Size Validation
    ├─ Check ≤ 5MB
    ├─ Pass → Save
    └─ Fail → Error message
    
    ↓
Filename Sanitization
    ├─ Use secure_filename()
    ├─ Add timestamp
    └─ Ensure uniqueness
    
    ↓
File Storage
    ├─ Save to secure location
    ├─ Set proper permissions
    └─ Track in database
```

---

## 🚀 Performance Optimization

```
Image Processing Timeline:

User Selects File
│ 0ms  ┌─────────────────────┐
│      │ File selected       │
│      └─────────────────────┘
│
│ 50-200ms ┌──────────────────────┐
│          │ FileReader processes │
│          └──────────────────────┘
│
│ 200ms ┌─────────────────────────┐
│       │ Preview image in DOM    │
│       └─────────────────────────┘
│
│ 300ms ┌──────────────────────────┐
│       │ Menu animation completes │
│       └──────────────────────────┘
│
│ User Clicks Upload
│ 300-500ms ┌──────────────────────────┐
│           │ Form submission sent     │
│           └──────────────────────────┘
│
│ Backend Processing (50-500ms depending on image size)
│
│ 500-1000ms ┌──────────────────────────┐
│            │ File saved, DB updated   │
│            └──────────────────────────┘
│
│ Page Reload / Redirect (< 100ms)

TOTAL: < 2 seconds for entire flow
```

---

## 📈 Scaling Considerations

```
Current Implementation (Local Storage):
├─ Single server
├─ Local filesystem
└─ Suitable for: < 10,000 users

Phase 2 (CDN Integration):
├─ Cloud storage (S3, Azure Blob, etc.)
├─ CDN distribution
└─ Suitable for: 10,000 - 1,000,000 users

Phase 3 (Enterprise Scale):
├─ Distributed storage
├─ Image optimization pipeline
├─ Global CDN with caching
└─ Suitable for: 1,000,000+ users
```

---

**Diagram Version**: 1.0  
**Last Updated**: February 4, 2026  
**Status**: ✅ Complete
