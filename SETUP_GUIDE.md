# SBI Resume Screening & Talent Intelligence System - Setup Guide

## 🚀 Quick Start

### 1. Get Your OpenRouter API Key

**Step 1:** Visit [openrouter.ai](https://openrouter.ai)

**Step 2:** Click **"Sign Up"** or **"Log In"** if you have an account

**Step 3:** Go to **"API Keys"** in your account settings

**Step 4:** Click **"Create API Key"** or **"New API Key"**

**Step 5:** Give it a name (e.g., "SBI Talent System") and click **Create**

**Step 6:** Copy the API key (it will look like `sk-or-v1-xxxxxxxxxxxxx`)

**Step 7:** Paste it in the Streamlit app's **"API Key"** field in the sidebar

### 2. Fix the 404 Error

The 404 error means your API key or model name was incorrect. Here's how to fix it:

**Option A: Verify Your API Key**
- Make sure you copied the entire API key without spaces
- API keys usually start with `sk-or-v1-`
- Check that your API key is valid by logging into openrouter.ai

**Option B: Use Free Models**
If you don't have credits, use free models available on OpenRouter:
1. In the sidebar, select from the available models
2. Some models like Mistral are free with rate limits
3. Check openrouter.ai for current free model availability

**Option C: Check Model Availability**
Different models may have different availability:
- `openai/gpt-3.5-turbo` - Usually available
- `openai/gpt-4-turbo` - May require credits
- `anthropic/claude-3-haiku` - Usually available (cheapest)
- `anthropic/claude-3-sonnet` - Usually available
- `mistralai/mistral-7b-instruct` - May be free

### 3. Common Error Messages

| Error | Solution |
|-------|----------|
| **404 Not Found** | API key invalid or model not available on OpenRouter |
| **401 Unauthorized** | API key expired or incorrect format |
| **Connection Error** | Check internet connection or OpenRouter service status |
| **Timeout** | OpenRouter is slow - try again or select faster model |

### 4. Features That Require API Key

✅ **Require OpenRouter API Key:**
- RAG Chat (page 5)
- Talent Intelligence Reports (page 3)
- Candidate Ranking with AI insights (page 6)

✅ **Work WITHOUT API Key:**
- Dashboard & Analytics (page 1)
- Candidate Explorer (page 2)
- Semantic Resume Search (page 4) - uses Jaccard similarity
- Database Explorer (page 7)
- Report Export (page 8)

### 5. Test Without API Key First

1. **Upload Sample Resumes** (convert SAMPLE_TEST_RESUMES.txt to PDF first)
2. **Explore Dashboard** - View metrics, skills, certifications
3. **Search Resumes** - Use semantic search without API
4. **Add API Key Later** - Enable AI features when ready

### 6. OpenRouter Costs

- **Free Tier**: Limited requests per minute with free models
- **Paid Plans**: Pay-as-you-go starting at ~$5/month
- **Cost Examples**:
  - GPT-3.5-turbo: ~$0.001 per request
  - Claude 3 Haiku: ~$0.0001 per request (cheapest)
  - GPT-4-turbo: ~$0.03 per request (expensive)

### 7. Debugging the Connection

If you still get 404 errors:

**Check OpenRouter Status:**
```
Visit https://openrouter.ai/status
Make sure the service is UP (green checkmark)
```

**Verify Your Request:**
1. Go to OpenRouter API Docs: https://openrouter.ai/api
2. Check which models are currently available
3. Copy exact model name from docs
4. Update MODEL_OPTIONS in utils.py if needed

**Test Your API Key:**
```python
# Run this in terminal to test
python -c "
from utils import call_openrouter
try:
    result = call_openrouter('YOUR_API_KEY', 'openai/gpt-3.5-turbo', 'Hello')
    print('Success:', result[:50])
except Exception as e:
    print('Error:', e)
"
```

### 8. Model Selection Recommendations

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| **Fast & Cheap** | `mistralai/mistral-7b-instruct` | Fastest, free tier available |
| **Balanced** | `anthropic/claude-3-haiku` | Good quality, cheap ($0.0001/request) |
| **High Quality** | `openai/gpt-4-turbo` | Best results, but expensive |
| **Default** | `openai/gpt-3.5-turbo` | Good balance of quality and speed |

### 9. Feature: RAG Chat Without API

If you don't have an API key, the semantic search still works:
- Go to **Resume Search** page
- Enter a query like "Python developers with AWS"
- Results use pure Python Jaccard similarity (no API needed)

### 10. Support & Troubleshooting

**If you get errors:**
1. Check internet connection
2. Verify API key is valid (test at openrouter.ai dashboard)
3. Try a different model from the dropdown
4. Check OpenRouter service status
5. Try again in 30 seconds (rate limiting)

**For more help:**
- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Status: https://openrouter.ai/status
- Check error message in terminal output

---

**Ready to go?** 
1. Get your API key from openrouter.ai
2. Paste it in the sidebar
3. Upload your first resume (convert TXT to PDF)
4. Start exploring!
