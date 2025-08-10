# Slack OAuth 2.0 Integration

This document explains how to set up and use the Slack OAuth 2.0 integration in the Finance Inbox application.

## Setup

### 1. Create a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name and select your workspace
5. Click "Create App"

### 2. Configure OAuth & Permissions

1. In your app settings, go to "OAuth & Permissions"
2. Add the following redirect URL:
   ```
   http://localhost:8000/slack-auth/callback
   ```
   (Replace with your actual backend URL in production)

3. Add the following Bot Token Scopes:
   - `channels:read` - View basic information about public channels
   - `channels:history` - View messages and other content in public channels
   - `users:read` - View people in the workspace
   - `team:read` - View the name, email domain, and icon of the workspace

### 3. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Slack OAuth Configuration
SLACK_CLIENT_ID=your_slack_client_id_here
SLACK_CLIENT_SECRET=your_slack_client_secret_here
SLACK_REDIRECT_URI=http://localhost:8000/slack-auth/callback
```

You can find your Client ID and Client Secret in the "Basic Information" section of your Slack app.

### 4. Database Migration

Run the database migration to add Slack support:

```bash
# The migration should automatically be applied when you restart the backend
# If not, you may need to run migrations manually
```

## Usage

### Backend API Endpoints

#### OAuth Flow
- `GET /slack-auth/` - Get authorization URL
- `GET /slack-auth/callback` - Handle OAuth callback
- `GET /slack-auth/status` - Check authentication status
- `DELETE /slack-auth/disconnect` - Disconnect Slack

#### Slack API Examples (with automatic token refresh)
- `GET /slack-api/user-info` - Get current user info
- `GET /slack-api/channels` - Get workspace channels
- `GET /slack-api/test-connection` - Test connection status

#### Settings API
- `GET /settings/connections` - Get all connections including Slack
- `POST /settings/connections/slack/disconnect` - Disconnect Slack

### Frontend Integration

The frontend Settings page already includes Slack connection UI. Users can:

1. Click "Connect" on the Slack card
2. Be redirected to Slack for authorization
3. Return to the app with the connection established
4. Disconnect when needed

### Automatic Token Management

The integration includes automatic token management:

1. **Token Refresh**: Tokens are checked before each API call
2. **Error Handling**: Expired tokens trigger re-authentication flow
3. **Connection Status**: Real-time status updates in the UI

### Example Usage in Code

```python
from services.token_manager import token_manager
from models import ConnectionProvider

# Get a valid token (automatically refreshes if needed)
token = token_manager.get_valid_token(user_id, ConnectionProvider.SLACK)

if token:
    # Make your Slack API call
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://slack.com/api/auth.test", headers=headers)
```

## Security Notes

- Slack OAuth tokens typically don't expire, but the system handles refresh gracefully
- All tokens are stored securely in the database
- RLS (Row Level Security) ensures users can only access their own tokens
- The system follows OAuth 2.0 best practices

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**: Make sure the redirect URI in your Slack app matches exactly
2. **"Missing scopes"**: Ensure all required scopes are added to your Slack app
3. **"Connection failed"**: Check that your environment variables are set correctly

### Token Issues

If users experience connection issues:
1. They can disconnect and reconnect in the Settings page
2. Check the logs for specific error messages
3. Verify the Slack app configuration

## Testing

You can test the integration using the provided endpoints:

```bash
# Test connection
curl -X GET "http://localhost:8000/slack-api/test-connection" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get user info
curl -X GET "http://localhost:8000/slack-api/user-info" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
``` 