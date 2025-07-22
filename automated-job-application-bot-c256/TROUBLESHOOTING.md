# 🛠️ Troubleshooting Guide - Auto Apply Agent

## 🚨 Common Issues & Solutions

### ❌ "Element Not Interactable" Error

**Problem:** The bot can't interact with form fields or buttons.

**Solutions:**
1. **Use the FIXED version:**
   ```bash
   python run_auto_apply_fixed.py
   ```

2. **Run in visible mode (not headless):**
   - Set `HEADLESS = False` in the runner script
   - This helps you see what's happening

3. **Check if the page has loaded completely:**
   - The fixed version includes better page load waits
   - Try increasing delays between actions

### 🔄 Bot Getting Stuck in Loops

**Problem:** Bot keeps trying the same action repeatedly.

**Solutions:**
1. **Check OpenAI responses:**
   - Make sure your API key is valid
   - Check if you have sufficient API credits

2. **Improve job URLs:**
   - Use direct job application URLs
   - Avoid URLs that redirect multiple times

3. **Update the prompt:**
   - The fixed version has improved prompts for better AI guidance

### 🤖 Bot Detection Issues

**Problem:** Websites detect and block the bot.

**Solutions:**
1. **Use the enhanced stealth features:**
   - The fixed version includes better anti-detection
   - Random delays and human-like behavior

2. **Add more delays:**
   - Increase sleep times between actions
   - Use random delays to appear more human

3. **Rotate user agents:**
   - The fixed version automatically rotates user agents

### 🔑 OpenAI API Issues

**Problem:** OpenAI API calls failing.

**Solutions:**
1. **Check your API key:**
   ```bash
   export OPENAI_API_KEY=your_actual_api_key_here
   ```

2. **Verify API credits:**
   - Check your OpenAI account for remaining credits
   - The bot uses GPT-4 which costs more than GPT-3.5

3. **Check rate limits:**
   - OpenAI has rate limits for API calls
   - The bot includes automatic retry logic

### 🌐 Website-Specific Issues

**Problem:** Bot works on some sites but not others.

**Solutions:**
1. **LinkedIn specific:**
   - Make sure you're logged in manually first
   - Use direct job URLs, not search results

2. **Indeed specific:**
   - Some Indeed jobs redirect to company sites
   - The bot should handle redirects automatically

3. **Company websites:**
   - These vary widely in structure
   - The AI should adapt, but some may be too complex

## �� Debugging Steps

### 1. Run with Visible Browser
```python
# In run_auto_apply_fixed.py, set:
HEADLESS = False
```

### 2. Check Logs
```bash
# View the detailed log file:
tail -f auto_apply_fixed.log
```

### 3. Test Individual Components

**Test OpenAI API:**
```python
import openai
openai.api_key = "your_key"
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=50
)
print(response.choices[0].message.content)
```

**Test Browser Initialization:**
```python
from auto_apply_agent_fixed import AutoApplyAgent
agent = AutoApplyAgent("your_openai_key", headless=False)
success = agent._init_browser()
print(f"Browser init: {success}")
```

### 4. Simplify Job List
Start with just one simple job:
```json
[
    {
        "job_url": "https://simple-company-job-url.com",
        "job_title": "Test Position",
        "company": "Test Company"
    }
]
```

## 🚀 Performance Optimization

### 1. Reduce Navigation Attempts
```python
# In auto_apply_agent_fixed.py, reduce:
self.max_navigation_attempts = 10  # Instead of 15
```

### 2. Increase Delays
```python
# Add longer delays for problematic sites:
time.sleep(random.uniform(3, 7))  # Instead of 2-5
```

### 3. Use Headless Mode for Production
```python
# Once debugging is complete:
HEADLESS = True
```

## 📋 Best Practices

### 1. Job URL Quality
- ✅ Use direct application URLs
- ✅ Avoid search result URLs
- ✅ Test URLs manually first

### 2. Resume Data Quality
- ✅ Include all required fields
- ✅ Use consistent formatting
- ✅ Test with simple data first

### 3. OpenAI Usage
- ✅ Monitor API usage and costs
- ✅ Use specific prompts
- ✅ Handle API errors gracefully

### 4. Rate Limiting
- ✅ Don't apply to too many jobs at once
- ✅ Add delays between applications
- ✅ Respect website terms of service

## 🆘 Still Having Issues?

### 1. Check Prerequisites
- ✅ Python 3.8+
- ✅ Chrome browser installed
- ✅ Valid OpenAI API key
- ✅ All dependencies installed

### 2. Try Manual Testing
- Navigate to the job URL manually
- See if you can apply without the bot
- Check if login is required

### 3. Update Dependencies
```bash
pip install --upgrade -r requirements_auto_apply.txt
```

### 4. Use Alternative Approach
If the bot consistently fails on certain sites:
- Focus on sites that work well
- Manually apply to problematic jobs
- Use the bot for bulk applications on supported sites

## 📝 Reporting Issues

If you continue having problems:

1. **Capture the error:**
   - Full error message
   - Log file contents
   - Job URL that failed

2. **Provide context:**
   - Operating system
   - Python version
   - Chrome version

3. **Test with minimal example:**
   - Single job application
   - Simple resume data
   - Visible browser mode

Remember: The bot is designed to handle most common scenarios, but some websites may require manual intervention or specific customizations.
