# AI Assistant Hub MCP Server

AI Assistant Hub is a production-ready **Model Context Protocol (MCP)** server that exposes a collection of tools (like Weather, GitHub, and Slack) to any MCP-compatible AI assistant or client.

## Getting Started

Follow these steps to set up and run the server.

### 1. Set Up the Python Environment

First, create a virtual environment and install the required packages.

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure API Keys with a `.env` File

The server needs API keys for the tools it provides. The recommended way to provide them is with a `.env` file.

1.  Create a new file named `.env` in the root of the project (`/home/harsh/Documents/MCPServer/ai-hub/.env`).
2.  Copy and paste the following into the `.env` file, replacing the placeholder values with your actual keys.

```ini
# --- API Keys and Secrets ---

# Weather (OpenWeatherMap)
TOOL_WEATHER_CONFIG__API_KEY=your-openweathermap-api-key

# GitHub Issues (optional for public repositories)
TOOL_GITHUB_ISSUES_CONFIG__TOKEN=ghp_your_token

# Slack
TOOL_SLACK_POST_MESSAGE_CONFIG__TOKEN=xoxb-your-slack-token


# --- Tool Toggles (all enabled by default) ---
TOOL_WEATHER_ENABLED=true
TOOL_GITHUB_ISSUES_ENABLED=true
TOOL_SLACK_POST_MESSAGE_ENABLED=true
```

### 3. Run the Server

Once the environment is set up and configured, run the server from your terminal:

```bash
ai-assistant-hub
```

The server will start and wait for a client to connect. You should see output like:

```
MCP server started with stdio transport. Waiting for client...
Tools available: ['weather', 'github_issues', 'slack_post_message']
```

## Connecting Your LLM Client

To use the tools, you need to connect your AI assistant or LLM client to this server. Most clients support connecting to an MCP server using a JSON configuration.

1.  **Find your client's server configuration settings** (e.g., "Tool Servers", "MCP Servers").
2.  **Add a new server** and provide the following JSON.

```json
{
  "mcpServers": {
    "ai-hub": {
      "command": "/home/harsh/Documents/MCPServer/ai-hub/.venv/bin/ai-assistant-hub",
      "args": [],
      "cwd": "/home/harsh/Documents/MCPServer/ai-hub",
      "env": {
        "TOOL_WEATHER_CONFIG__API_KEY": "your-openweathermap-api-key",
        "TOOL_GITHUB_ISSUES_CONFIG__TOKEN": "ghp_your_token",
        "TOOL_SLACK_POST_MESSAGE_CONFIG__TOKEN": "xoxb-your-slack-token"
      }
    }
  }
}
```

**Important:**
*   Make sure the `command` and `cwd` paths in the JSON match the location of your project.
*   The `env` block in the JSON is an alternative way to provide the API keys if you prefer not to use a `.env` file. You don't need to fill it out if you've already created a `.env` file.

3.  **Save and activate the new server.** Your client can now use the tools.

---

## Project Details

### Features

- ✅ Built on the official MCP server runtime from Hugging Face.
- ✅ Modular tools for Weather, GitHub Issues, and Slack.
- ✅ Resilient HTTP clients with built-in retries.
- ✅ Centralised configuration via `.env` files or environment variables.

### Architecture

The project is structured to be modular and extensible.

-   `ai_assistant_hub/server/main.py`: The main entrypoint that starts the server.
-   `ai_assistant_hub/tools/`: Contains the definition for each tool.
-   `ai_assistant_hub/integrations/`: Contains the logic for communicating with third-party APIs (like OpenWeatherMap).

### Adding New Tools

1.  Create an "adapter" in `ai_assistant_hub/integrations/` to handle the external API communication.
2.  Define a new tool in `ai_assistant_hub/tools/` that uses the adapter.
3.  Enable your new tool and provide its configuration in your `.env` file.

### Testing

The project includes a test suite using `pytest`. Run the tests with:

```bash
pytest
```

---

Need help or want to add more adapters? Open an issue or submit a pull request!
