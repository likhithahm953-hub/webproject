# AI-Generated Questions Setup

## Overview
The system now uses **Google Gemini AI** to dynamically generate assessment questions for each domain based on the level (Zero/Beginner/Intermediate/Advanced). No more hardcoded questions!

## Setup Instructions

### 1. Install Google Generative AI Package
```bash
pip install google-generativeai
```

### 2. Get Your Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 3. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 4. Run Your App
```bash
python app.py
```

## How It Works

1. **AI Generation**: When a user selects a domain and level, the system calls Gemini AI to generate 8 questions
2. **Smart Prompts**: Different prompts for survey questions (Zero level) vs assessment questions (Beginner/Intermediate/Advanced)
3. **Fallback**: If AI is unavailable or fails, it uses generic template questions as backup

## Question Generation Details

- **Zero Level**: Survey questions about background, goals, and time commitment
- **Beginner Level**: Foundational knowledge questions
- **Intermediate Level**: Practical application questions  
- **Advanced Level**: Expert-level concepts and best practices

Each level gets **8 questions** automatically generated based on the domain name and difficulty level!

## Benefits

✅ No hardcoded questions - AI generates fresh, relevant questions
✅ Adapts to any domain automatically
✅ Questions are contextual and domain-specific
✅ Easy to scale to 100+ domains without manual work
✅ Questions stay current and varied

## Testing

To test if AI is working:
1. Enroll in any domain
2. Select a level
3. Check browser console for any errors
4. Questions should load dynamically

If AI fails, you'll see generic fallback questions - check your API key is set correctly!
