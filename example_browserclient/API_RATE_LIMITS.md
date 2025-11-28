# OpenAI API Rate Limits & Solutions

## Error 429: Rate Limit Exceeded

This error means you've made too many requests to the OpenAI API in a short time.

### OpenAI Free Tier Limits:
- **3 requests per minute (RPM)**
- **200 requests per day (RPD)**
- **40,000 tokens per minute (TPM)**

### Solutions:

#### 1. **Wait and Retry**
Simply wait 20-60 seconds before trying auto-fix again.

#### 2. **Use Manual Correction**
Instead of clicking "🤖 Auto-Fix", type your correction manually and click "✓ Submit".

#### 3. **Upgrade Your OpenAI Plan**
- **Tier 1**: $5+ spent → 500 RPM
- **Tier 2**: $50+ spent → 5,000 RPM
- **Tier 3**: $100+ spent → 10,000 RPM

#### 4. **Use Simple Rule-Based Fallback**
The system now automatically falls back to simple rules when ChatGPT is unavailable.

### Current Behavior:

When you click "🤖 Auto-Fix":
1. **First**: Tries ChatGPT API
2. **If rate limited**: Uses simple rule-based correction
3. **If that fails**: Shows message to use manual correction

### Rate Limit Status Messages:

| Message | Meaning | Action |
|---------|---------|--------|
| ⚠️ Rate limit exceeded (429) | Too many requests | Wait 1 minute |
| ⚠️ Authentication failed (401) | Invalid API key | Check config.py |
| ⚠️ Connection error | No internet | Check connection |
| ⚠️ Request timeout | Slow response | Try again |

### Best Practices:

1. **Don't spam auto-fix** - Use it sparingly
2. **Prefer manual corrections** - They're instant and free
3. **Batch your corrections** - Wait between auto-fix attempts
4. **Monitor your usage** - Check OpenAI dashboard

### Alternative: Use Manual Corrections

Manual corrections are:
- ✅ **Instant** - No API delay
- ✅ **Free** - No API costs
- ✅ **Reliable** - No rate limits
- ✅ **Effective** - System learns the same way

### Checking Your Rate Limit:

Visit: https://platform.openai.com/account/rate-limits

### Cost Optimization:

- **GPT-3.5-turbo**: ~$0.001 per correction
- **Manual corrections**: $0.00 (free)
- **Simple rules**: $0.00 (free)

### Recommendation:

For most users, **manual corrections are better** because:
1. You know exactly what you want
2. No waiting for API
3. No rate limits
4. No costs
5. System learns just as well

Use auto-fix only when:
- You're unsure of the correct output
- You want AI suggestions
- You have API quota available
