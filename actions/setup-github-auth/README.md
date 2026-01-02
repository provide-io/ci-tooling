# Setup GitHub Auth Action

A GitHub Action that configures git authentication for private repositories using organization helper tokens. This action allows workflows to access private repositories across multiple GitHub organizations.

## Features

- **Multi-Organization Support**: Configure authentication for multiple GitHub organizations
- **Secure Token Handling**: Uses environment variables to securely pass tokens
- **Automatic Git Configuration**: Sets up git URL rewriting for seamless access
- **Error Handling**: Validates tokens and provides clear error messages
- **Flexible Configuration**: Configurable environment variable name

## Usage

### Basic Usage

```yaml
- name: 🔐 Setup GitHub Auth
  uses: provide-io/ci-tooling/actions/setup-github-auth@main
  env:
    GH_ORG_HELPERS: ${{ secrets.GH_ORG_HELPERS }}
```

### Custom Environment Variable

```yaml
- name: 🔐 Setup GitHub Auth
  uses: provide-io/ci-tooling/actions/setup-github-auth@main
  with:
    helpers-env-var: 'MY_CUSTOM_HELPERS'
  env:
    MY_CUSTOM_HELPERS: ${{ secrets.MY_CUSTOM_HELPERS }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `helpers-env-var` | Environment variable containing the organization helper tokens JSON | No | `GH_ORG_HELPERS` |

## Environment Variables

The action expects an environment variable (default: `GH_ORG_HELPERS`) containing a JSON object mapping organization names to GitHub Personal Access Tokens:

```json
{
  "my-org": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "another-org": "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

## How It Works

1. **Reads the environment variable** containing the organization-to-token mapping
2. **Validates the JSON format** and token formats
3. **Configures git URL rewriting** for each organization:
   - Maps `https://github.com/{org}/` to `https://{token}@github.com/{org}/`
   - This allows git operations to automatically use the token for that organization
4. **Provides feedback** on successful configuration or errors

## Security Considerations

- **Tokens are never logged** or exposed in workflow output
- **Tokens are validated** to ensure they look like GitHub PATs
- **Global git configuration** is used (appropriate for CI environments)
- **Environment variables** should be stored as GitHub secrets

## Example Workflow

```yaml
name: Deploy with Private Dependencies

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 🔐 Setup GitHub Auth
        uses: provide-io/ci-tooling/actions/setup-github-auth@main
        env:
          GH_ORG_HELPERS: ${{ secrets.GH_ORG_HELPERS }}

      - name: 📦 Install Dependencies
        run: |
          # Now can access private repos from configured organizations
          uv add git+https://github.com/my-org/private-package.git
```

## Token Requirements

The GitHub Personal Access Tokens should have:
- `repo` scope for private repository access
- Appropriate permissions for the repositories you need to access

## Error Handling

The action will:
- **Skip configuration** if no environment variable is found (graceful degradation)
- **Fail the workflow** if JSON is invalid
- **Fail the workflow** if git configuration fails
- **Warn** if tokens don't look like valid GitHub PATs

## Integration with Other Actions

This action is designed to work seamlessly with other ci-tooling actions:

```yaml
- name: 🔐 Parse Organization Helpers
  uses: provide-io/ci-tooling/actions/parse-org-helpers@main
  env:
    GH_ORG_HELPERS: ${{ secrets.GH_ORG_HELPERS }}

- name: 🔐 Setup GitHub Auth
  uses: provide-io/ci-tooling/actions/setup-github-auth@main
  env:
    GH_ORG_HELPERS: ${{ secrets.GH_ORG_HELPERS }}

- name: 🐍 Setup Python Environment
  uses: provide-io/ci-tooling/actions/setup-python-env@main
  # Now can install from private repos
```