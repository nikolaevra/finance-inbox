# Finance Inbox Backend API Tests

This directory contains comprehensive unit tests for all backend API endpoints with mock data validation and edge case testing.

## Test Structure

```
tests/
├── __init__.py                     # Test package init
├── conftest.py                     # Pytest configuration and shared fixtures
├── factories.py                    # Mock data factories and generators
├── test_auth_api.py               # Authentication API endpoint tests
├── test_inbox_api.py              # Inbox API endpoint tests  
├── test_settings_api.py           # Settings API endpoint tests
├── test_prompt_settings_api.py    # Prompt settings API endpoint tests
├── test_connection_apis.py        # OAuth connection API tests (Gmail/Slack)
├── test_main_api.py              # Main app and general API tests
└── README.md                     # This file
```

## Test Coverage

The test suite covers:

### API Endpoints
- **Authentication (`/auth/*`)**: Login, logout, token refresh, user info
- **Inbox (`/inbox/*`)**: Email retrieval, sync, marking as read, replies
- **Settings (`/settings/*`)**: User connections, provider disconnection
- **Prompt Settings (`/settings/prompt/*`)**: Prompt configuration CRUD
- **Gmail OAuth (`/google-auth/*`)**: OAuth flow, status, logout
- **Slack OAuth (`/slack-auth/*`)**: OAuth flow, status, disconnection
- **Slack API (`/slack-api/*`)**: User info, channels, connection testing
- **Main App (`/`, `/health`)**: Root endpoints, documentation

### Test Types
- **Happy Path Tests**: Valid inputs and expected successful responses
- **Error Handling**: Invalid inputs, missing fields, service failures
- **Edge Cases**: Boundary conditions, malformed data, exception scenarios
- **Authentication**: Authorized and unauthorized access patterns
- **Validation**: Request/response model validation with Pydantic
- **Service Integration**: Mocked service calls and responses

### Mock Data
- Comprehensive factories using Faker for realistic test data
- Mock OAuth responses for Gmail and Slack APIs
- Simulated database responses and service interactions
- Generated email threads, user profiles, and connection data

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Run all tests
python run_tests.py

# Run with coverage report
python run_tests.py --coverage

# Run specific test file
python run_tests.py --specific test_auth_api.py

# Run specific test function
python run_tests.py --specific test_auth_api.py::TestAuthAPI::test_login_success

# Run tests with specific markers
python run_tests.py --markers "auth"

# Skip slow tests
python run_tests.py --fast

# Verbose output
python run_tests.py --verbose
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apis --cov=services --cov=models --cov-report=html

# Run specific tests
pytest tests/test_auth_api.py -v

# Run tests with markers
pytest -m "auth" -v

# Run tests matching pattern
pytest -k "test_login" -v
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Configured for comprehensive coverage reporting
- Minimum 80% coverage requirement
- HTML coverage reports generated in `htmlcov/`
- Test discovery patterns and markers defined

### Fixtures (`conftest.py`)
- **`client`**: FastAPI test client for making HTTP requests
- **`mock_user_profile`**: Standard user profile for authenticated tests
- **`mock_*_service`**: Mocked service dependencies
- **`authenticated_user`**: Simulated authenticated user context
- **Environment variables**: Mocked for consistent test environment

### Mock Factories (`factories.py`)
- **UserAuthDataFactory**: Authentication response data
- **EmailDetailsFactory**: Email data structures
- **UserFactory**: User profile data
- **ConnectionFactory**: OAuth connection data
- **Helper functions**: Gmail threads, Slack responses, etc.

## Test Markers

Tests are organized with markers for selective execution:

- `@pytest.mark.auth`: Authentication-related tests
- `@pytest.mark.inbox`: Inbox functionality tests
- `@pytest.mark.settings`: Settings management tests
- `@pytest.mark.connections`: OAuth connection tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.unit`: Unit tests

## Coverage Reports

Coverage reports are generated in multiple formats:

- **Terminal**: Summary displayed after test run
- **HTML**: Detailed interactive report in `htmlcov/index.html`
- **Coverage threshold**: Minimum 80% required for build success

## Best Practices

### Writing Tests
1. **Descriptive names**: Test methods clearly describe what they test
2. **Arrange-Act-Assert**: Clear test structure
3. **Mock external dependencies**: Services, databases, external APIs
4. **Test edge cases**: Error conditions, boundary values
5. **Validate responses**: Status codes, response format, required fields

### Mock Data
1. **Use factories**: Consistent, realistic test data
2. **Avoid hardcoded values**: Use Faker for dynamic data
3. **Test with variations**: Different data scenarios
4. **Keep mocks simple**: Focus on the interface being tested

### Error Testing
1. **Test all error paths**: 400, 401, 404, 422, 500 responses
2. **Validate error messages**: Ensure helpful error responses
3. **Test validation**: Both success and failure cases
4. **Mock service failures**: Network errors, timeouts, etc.

## Maintenance

### Adding New Tests
1. Create test file following naming convention (`test_*.py`)
2. Add appropriate imports and fixtures
3. Group related tests in classes
4. Add descriptive docstrings
5. Include both success and failure scenarios

### Updating Mocks
1. Keep factories synchronized with models
2. Update mock responses when APIs change
3. Maintain realistic test data
4. Document mock behavior in complex scenarios

### Performance
- Use `@pytest.mark.slow` for time-consuming tests
- Mock external services to avoid network delays
- Keep test data minimal but representative
- Use parametrized tests for multiple scenarios

## Troubleshooting

### Common Issues
1. **Import errors**: Check Python path and dependencies
2. **Mock failures**: Verify mock patches target correct modules
3. **Fixture conflicts**: Check fixture scope and dependencies
4. **Coverage gaps**: Identify untested code paths

### Debug Tips
1. Use `pytest -s` for print debugging
2. Use `pytest --pdb` to drop into debugger on failures
3. Check mock call counts and arguments
4. Verify test isolation with `pytest --tb=long` 