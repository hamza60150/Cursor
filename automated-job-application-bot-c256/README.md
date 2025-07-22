# 🤖 Automated Job Application Bot with OpenAI Integration

## 🎯 **Streamlined Auto-Apply Agent**

This folder contains the **focused, streamlined auto-apply bot** with OpenAI integration that automatically applies to jobs on ANY website.

## 📁 **Files in This Folder**

- **`auto_apply_agent.py`** - Main auto-apply agent with OpenAI intelligence
- **`run_auto_apply.py`** - Simple runner script to execute the bot
- **`sample_jobs.json`** - Example format for job links input
- **`sample_resume.json`** - Example format for parsed resume data
- **`requirements_auto_apply.txt`** - Required Python dependencies
- **`AUTO_APPLY_README.md`** - Comprehensive documentation

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements_auto_apply.txt
```

### 2. Set OpenAI API Key
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Prepare Your Data
- Update `sample_jobs.json` with your job URLs
- Update `sample_resume.json` with your parsed resume data

### 4. Run the Bot
```bash
python run_auto_apply.py
```

## 🧠 **How It Works**

1. **Takes your job links and parsed resume via JSON files**
2. **Uses OpenAI GPT-4 to analyze each job website's HTML**
3. **Gets intelligent navigation instructions from AI**
4. **Automatically navigates and fills forms on ANY website**
5. **Applies redundancy and retry strategies for robustness**
6. **Learns successful patterns and adapts to obstacles**

## ✅ **Key Features**

- ✅ **OpenAI Integration**: Uses GPT-4 for intelligent website navigation
- ✅ **Universal Compatibility**: Works on LinkedIn, Indeed, company sites, ANY website
- ✅ **Robust Retry Logic**: Multiple fallback strategies at every level
- ✅ **Anti-Detection**: Stealth browser with human-like behavior
- ✅ **Cookie Management**: Automatic session persistence
- ✅ **Adaptive Learning**: Remembers successful patterns per domain
- ✅ **Trial & Error Approach**: Continuously tries until successful application

## 📊 **Input Format**

### Jobs JSON Format:
```json
[
    {
        "job_url": "https://company.com/jobs/123",
        "job_title": "Software Engineer",
        "company": "TechCorp"
    }
]
```

### Resume JSON Format:
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "skills": ["Python", "JavaScript"],
    "experience_years": "5",
    "cover_letter": "I am excited to apply..."
}
```

## 🎯 **This Bot Will:**

🤖 **Navigate ANY job website** using AI intelligence  
📝 **Auto-fill ANY application form** with your resume data  
🔄 **Handle obstacles** like bot detection, CAPTCHAs, login requirements  
⚡ **Apply to jobs automatically** with robust retry mechanisms  
📊 **Learn and improve** from each application attempt  

**Ready to automate your job applications with AI power!** 🚀

For detailed documentation, see `AUTO_APPLY_README.md`
