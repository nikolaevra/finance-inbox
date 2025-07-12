# Email Categorization with LLM

This document explains how to set up and use the LLM-powered email categorization feature for financial professionals.

## Overview

The email categorization system automatically categorizes incoming emails into 10 predefined categories relevant to financial professionals using OpenAI's GPT models.

## Categories

1. **CLIENT_COMMUNICATION** - Direct communication with clients, prospects, or their representatives
2. **MARKET_RESEARCH** - Market analysis, investment research, economic reports, analyst recommendations
3. **REGULATORY_COMPLIANCE** - Regulatory filings, compliance updates, legal notices, audit requests
4. **FINANCIAL_REPORTING** - Financial statements, earnings reports, quarterly reports, performance summaries
5. **TRANSACTION_ALERTS** - Trade confirmations, settlement notices, payment alerts, transaction updates
6. **INTERNAL_OPERATIONS** - Internal company communications, HR updates, system notifications, IT alerts
7. **VENDOR_SERVICES** - Communications from financial service providers, software vendors, data providers
8. **MARKETING_SALES** - Sales pitches, promotional content, marketing materials, product announcements
9. **EDUCATIONAL_CONTENT** - Training materials, webinars, industry news, educational resources
10. **OTHER** - Any email that doesn't clearly fit into the above categories

## Setup

### 1. Configure OpenAI API Key

Add your OpenAI API key to your environment variables:

```bash
# Add to your .env file or environment
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 2. Install Dependencies

```bash
pip install openai==1.51.2
```

### 3. Apply Database Migration

The categorization fields have been added to the emails table:

```bash
supabase migration up --linked
```

## Usage

### Automatic Categorization

All new emails fetched from Gmail are automatically categorized when saved to the database.

### One-Time Migration Script

For existing emails in your database, use the standalone categorization script:

```bash
cd backend
source .venv/bin/activate  # Activate virtual environment
export OPENAI_API_KEY="your-api-key-here"
python categorize_existing_emails.py
```

**Script Features:**
- ✅ Processes all uncategorized emails in batches
- ✅ Shows progress and statistics in real-time
- ✅ Configurable batch size and delay between batches
- ✅ Dry-run mode to preview what will be processed
- ✅ User-specific processing option
- ✅ Graceful error handling and recovery
- ✅ Confirmation prompt before processing

### Batch Categorization

To categorize existing emails in your database, use the standalone script:

```bash
# Basic usage - processes all uncategorized emails
python categorize_existing_emails.py

# With custom batch size
python categorize_existing_emails.py --batch-size 25

# Process specific user only
python categorize_existing_emails.py --user-id "user-uuid-here"

# Dry run to see what would be processed
python categorize_existing_emails.py --dry-run

# With custom delay between batches (to manage API rate limits)
python categorize_existing_emails.py --delay 2.0
```

Example output:
```
🚀 Email Categorization Script
==================================================
🔧 Initializing services...
✅ Services initialized successfully!
📊 Found 145 uncategorized emails
   - Batch size: 50
   - Estimated batches: 3
   - User filter: All users

🤖 Starting categorization...

📦 Processing batch 1...
   ✅ Processed: 50
   ✅ Successful: 48
   ❌ Failed: 2
   📈 Progress: 50/145 (34.5%)

🎉 Categorization completed!
   - Total processed: 145
   - Successful: 140
   - Failed: 5
   - Success rate: 96.6%
   - Time elapsed: 145.2s
   - Average per email: 1.00s
```

### API Response

All email API responses now include categorization data:

```json
{
  "id": "email-uuid",
  "subject": "Q4 Earnings Report",
  "category": "FINANCIAL_REPORTING",
  "category_confidence": 0.95,
  "categorized_at": "2025-06-25T10:30:00Z",
  "category_prompt_version": "1.0",
  ...
}
```

## Customizing the Prompt

### Configuration File

The email categorization system uses a YAML configuration file: `backend/prompts/email_categorization.yaml`

```yaml
name: email_categorization
model: gpt-4o-mini
temperature: 0.1
max_tokens: 200
timeout: 10
input_variables: ["subject", "sender", "content"]
prompt_version: 1.0
template: |-
  Your prompt template here with {subject}, {sender}, {content} variables
```

### Editing Categories and Configuration

To modify the categorization system:

1. **Edit the YAML file**: `backend/prompts/email_categorization.yaml`
   - Update the `template` section to modify categories or instructions
   - Change `model`, `temperature`, `max_tokens` for different behavior
   - Increment `prompt_version` when making changes

2. **Update the categories list**: In `backend/services/email_categorization_service.py`
   - Modify the `get_valid_categories()` method if you add/remove categories

3. **Test your changes**: Use a small batch to validate new prompts

### Configuration Parameters

- **model**: OpenAI model to use (e.g., `gpt-4o-mini`, `gpt-4o`)
- **temperature**: Creativity level (0.0-1.0, lower = more consistent)
- **max_tokens**: Maximum response length
- **timeout**: API request timeout in seconds
- **input_variables**: Variables available in the template
- **prompt_version**: Version tracking for prompts

### Prompt Best Practices

- Be specific about what each category includes
- Provide clear examples
- Keep the JSON response format consistent
- Use input variables: `{subject}`, `{sender}`, `{content}`
- Test changes with a small batch first
- Increment `prompt_version` when making significant changes

## Cost Optimization

The system uses `gpt-4o-mini` for cost efficiency:
- ~$0.00015 per 1K input tokens
- ~$0.0006 per 1K output tokens
- Average cost per email: ~$0.001-0.003

For high-volume processing, consider:
- Batch processing during off-peak hours
- Adjusting the temperature parameter
- Using shorter prompts for simple categorization

## Monitoring

### Logs

Categorization events are logged with prefixes:
- `🤖` - Starting categorization
- `✅` - Successful categorization  
- `⚠️` - Warning or low confidence
- `❌` - Failed categorization

### Confidence Scores

- **High (0.8+)**: Clear categorization
- **Medium (0.5-0.8)**: Likely correct
- **Low (0.3-0.5)**: Uncertain, review recommended

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: OPENAI_API_KEY environment variable is required
   ```
   Solution: Set the `OPENAI_API_KEY` environment variable

2. **Missing Configuration File**
   ```
   Error: Email categorization config file not found
   ```
   Solution: Ensure `backend/prompts/email_categorization.yaml` exists

3. **Invalid Configuration**
   ```
   Error: Missing required fields in config: ['template', 'model']
   ```
   Solution: Check your YAML file has all required fields: `template`, `model`, `prompt_version`

4. **Invalid YAML Format**
   ```
   Error: Invalid YAML in config file
   ```
   Solution: Validate your YAML syntax using a YAML validator

5. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   ```
   Solution: Reduce batch size or add delays between requests

6. **Invalid Category**
   ```
   Warning: Unknown category returned
   ```
   Solution: Check prompt consistency and update valid categories list

### Performance Issues

- Large batch sizes may timeout
- Reduce `batch_size` parameter for slower connections
- Monitor OpenAI usage limits

## Development

### Testing New Prompts

1. Create a backup of the current prompt
2. Test with a small batch of emails
3. Monitor confidence scores and accuracy
4. Roll back if results are poor

### Adding New Fields

To add new categorization metadata:

1. Add database columns via migration
2. Update the `Email` model in `models.py`
3. Modify the categorization service
4. Update API response formatting

## Security

- Never log full email content in production
- Ensure OpenAI API key is properly secured
- Consider data privacy requirements for email content
- Implement rate limiting for batch operations 