# SkillForge - Quick Reference Guide

**Last Updated**: February 4, 2026  
**Version**: 1.0

---

## 🚀 Quick Start

### Installation
```bash
cd c:\Users\hp\OneDrive\Desktop\webproject
pip install flask flask-sqlalchemy werkzeug
python app.py
```

### Access Application
```
URL: http://localhost:5000
Profile: http://localhost:5000/profile
Dashboard: http://localhost:5000/dashboard
```

---

## 📁 File Structure Quick Reference

```
webproject/
├── app.py                          ← Main Flask application
├── database.db                     ← SQLite database
├── SKILLFORGE_FEATURES.md          ← Feature documentation
├── PROFILE_AVATAR_GUIDE.md         ← Avatar management guide
├── IMPLEMENTATION_SUMMARY.md       ← Changes summary
├── ARCHITECTURE_DIAGRAMS.md        ← Technical diagrams
│
├── templates/
│   ├── profile.html                ← Profile with avatar management
│   ├── dashboard.html              ← Dashboard
│   ├── courses.html                ← Courses listing
│   ├── challenges.html             ← Challenges listing
│   ├── certificates.html           ← Certificates showcase
│   ├── login.html                  ← Login page
│   ├── signup.html                 ← Registration page
│   └── ... (other templates)
│
├── static/
│   ├── profile.css                 ← Profile styles + avatar
│   ├── profile.js                  ← Profile functionality + avatar
│   ├── dashboard.css               ← Dashboard styles
│   ├── dashboard.js                ← Dashboard scripts
│   ├── style.css                   ← Global styles
│   ├── script.js                   ← Global scripts
│   ├── uploads/                    ← Avatar storage
│   │   ├── user1_1707060000_profile.jpg
│   │   └── user2_1707059000_avatar.png
│   └── ... (other assets)
│
└── instance/
    └── database.db                 ← SQLite database file
```

---

## 🎯 Avatar Management - Quick Reference

### For Users

**How to Upload Profile Picture**:
1. Go to Profile page
2. Hover over profile picture → Camera icon appears
3. Click camera icon → Edit menu opens
4. Click "📷 Upload Photo"
5. Select image (JPG, PNG, GIF - Max 5MB)
6. Preview updates automatically
7. Click "Upload" button
8. Success! Avatar updated

**How to Remove Profile Picture**:
1. Click camera icon on profile picture
2. Click "🗑️ Remove Photo"
3. Confirm in dialog
4. Avatar removed, reverts to initial

**How to Change Profile Picture**:
- Simply upload new image (automatically replaces old one)

---

## 🔧 Customization Guide

### Change Avatar Size
Edit `static/profile.css`:
```css
.current-avatar {
  width: 120px;      /* Change this */
  height: 120px;     /* and this */
}
```

### Change Camera Icon Size
```css
.avatar-edit-overlay {
  width: 40px;       /* Change this */
  height: 40px;      /* and this */
}
```

### Change Primary Color
```css
.avatar-edit-overlay {
  background: #your-color;  /* Update this */
}
```

### Change Max File Size
Edit `app.py`:
```python
# Find and modify the file size check
MAX_SIZE = 5 * 1024 * 1024  # Change 5 to desired MB
```

### Change Allowed File Types
Edit `app.py`:
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
```

---

## 🐛 Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| Avatar not uploading | Check file size & format |
| Camera icon not visible | Clear browser cache (Ctrl+F5) |
| Remove option missing | Upload avatar first, then refresh |
| Old image shows after delete | Hard refresh (Ctrl+Shift+R) |
| File size error | Resize image, keep < 5MB |
| Format not supported | Convert to JPG or PNG |

---

## 📊 API Endpoints

### Profile Upload
```
Method: POST
URL: /profile
Content-Type: multipart/form-data
Data: {avatar: File}
Response: Redirect to /profile (with success message)
```

### Avatar Removal
```
Method: POST
URL: /api/remove-avatar
Content-Type: application/x-www-form-urlencoded
Response: Redirect to /profile (with success message)
```

### Get User Info
```
Method: GET
URL: /profile
Response: Render profile.html with user data
```

---

## 🔐 Security Checklist

- ✅ File type validation (whitelist: JPG, PNG, GIF)
- ✅ File size check (max 5MB)
- ✅ User authentication required
- ✅ Secure filename generation (prevents path traversal)
- ✅ Unique timestamped filenames (prevents collisions)
- ✅ Database integration (tracks avatar)
- ✅ Error handling (try/except blocks)

---

## 🎨 Color Reference

### Avatar Colors
- **Primary Gradient Start**: #6366f1 (Indigo)
- **Primary Gradient End**: #8b5cf6 (Purple)
- **Hover Color**: var(--accent-secondary)
- **Danger Color**: #ef4444 (Red)
- **Border Color**: var(--border-color)

### Text Colors
- **Primary Text**: var(--text-primary)
- **Secondary Text**: var(--text-secondary)
- **Muted Text**: var(--text-muted)

---

## 📱 Responsive Breakpoints

| Device | Width | Avatar Size | Camera Size |
|--------|-------|-------------|-------------|
| Mobile | < 768px | 100x100px | 36x36px |
| Tablet | 768-1199px | 100x100px | 36x36px |
| Desktop | ≥ 1200px | 120x120px | 40x40px |

---

## 💾 Database Schema

### User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    avatar VARCHAR(255),  ← Avatar filename
    role VARCHAR(20) DEFAULT 'user'
);
```

---

## 🧪 Testing Checklist

- [ ] Upload JPG file
- [ ] Upload PNG file
- [ ] Upload GIF file
- [ ] Test file size limit (> 5MB)
- [ ] Test invalid format
- [ ] Remove avatar
- [ ] Change avatar
- [ ] Test on mobile
- [ ] Test on tablet
- [ ] Test on desktop
- [ ] Check responsive design
- [ ] Verify animations work
- [ ] Check menu closes on click outside
- [ ] Verify preview updates
- [ ] Test confirmation dialog

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| SKILLFORGE_FEATURES.md | Complete feature list and requirements |
| PROFILE_AVATAR_GUIDE.md | Detailed avatar management guide |
| IMPLEMENTATION_SUMMARY.md | What was changed and why |
| ARCHITECTURE_DIAGRAMS.md | Technical architecture and flows |
| README.md | Setup and basic usage |

---

## 🚀 Deployment Steps

1. **Test Locally**
   ```bash
   python app.py
   # Test all features in browser
   ```

2. **Create Uploads Directory**
   ```bash
   mkdir -p static/uploads
   chmod 755 static/uploads
   ```

3. **Set Permissions**
   ```bash
   chmod 644 static/uploads
   ```

4. **Deploy to Server**
   ```bash
   # Copy files to server
   # Restart Flask application
   # Test all functionality
   ```

---

## 🎯 Performance Tips

- Use image compression tools before uploading
- Keep images square (1:1 ratio) for best display
- Use PNG for transparency, JPG for photos
- Optimize images to < 1MB when possible
- Clear old uploads periodically

---

## 📞 Common Commands

### View Avatar Uploads
```bash
ls -lh static/uploads/
```

### Clear All Avatars
```bash
rm -f static/uploads/*
```

### Backup Database
```bash
cp instance/database.db instance/database.db.backup
```

### Reset Database
```bash
rm instance/database.db
# Restart app to create new DB
```

---

## 🔔 Feature Toggle

To disable avatar removal (remove option in menu):

Edit `templates/profile.html`:
```html
<!-- Comment out or remove this block -->
{% if user and user.avatar %}
<button type="button" class="menu-item remove-item" id="remove-avatar-btn">
  <i class="fa-solid fa-trash"></i>
  <span>Remove Photo</span>
</button>
{% endif %}
```

---

## 📈 Monitoring

Monitor these metrics:
- Upload success rate
- Average file size
- Remove action frequency
- Error count and types
- Storage usage
- Load times

---

## 🎓 Learning Resources

### CSS Features Used
- Flexbox layout
- CSS Grid
- Transform animations
- Position absolute/relative
- Media queries
- Gradient backgrounds

### JavaScript Features Used
- Event listeners
- FileReader API
- Form submission
- Fetch API (for removal)
- DOM manipulation
- Confirmation dialogs

### Flask Features Used
- Route decorators
- File uploads
- Session management
- Database ORM
- Secure filename handling
- Error handling

---

## 🔗 Related Routes

```
GET  /dashboard         → Dashboard
GET  /profile           → Profile page
POST /profile           → Upload avatar
POST /api/remove-avatar → Remove avatar
GET  /login             → Login page
GET  /signup            → Registration page
GET  /logout            → Logout
GET  /courses           → Courses page
GET  /challenges        → Challenges page
GET  /certificates      → Certificates page
```

---

## 📝 Version Information

**Current Version**: 1.0  
**Release Date**: February 4, 2026  
**Status**: Production Ready ✅  
**Last Tested**: February 4, 2026  

---

## 📋 Pre-Flight Checklist

Before going live:
- [ ] Test avatar upload/remove
- [ ] Test on mobile devices
- [ ] Test file size limit
- [ ] Test invalid formats
- [ ] Clear browser cache
- [ ] Test database backups
- [ ] Verify file permissions
- [ ] Test error messages
- [ ] Verify success messages
- [ ] Check security measures
- [ ] Performance test
- [ ] Accessibility test

---

## 🎉 You're All Set!

Your SkillForge application now has WhatsApp-style profile picture management with:
- ✅ Easy upload/remove functionality
- ✅ Beautiful UI with animations
- ✅ Secure file handling
- ✅ Responsive design
- ✅ Complete documentation

**Happy Learning!** 🚀

---

For detailed information, please refer to:
- SKILLFORGE_FEATURES.md (Features overview)
- PROFILE_AVATAR_GUIDE.md (Detailed guide)
- IMPLEMENTATION_SUMMARY.md (Technical details)
- ARCHITECTURE_DIAGRAMS.md (System design)

---

*Questions? Check the documentation files or contact the development team.*
