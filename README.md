# An agent that uses GoogleNews tools provided to perform any task

## Purpose

# Introduction
Welcome to the ReAct AI News Agent! This agent is designed to help you stay informed by retrieving the latest news articles based on specific keywords. Whether you're interested in technology, politics, health, or any other topic, this agent can efficiently search and present relevant news stories.

# Instructions
1. When prompted, provide a specific set of keywords for the news topic you're interested in.
2. You may also specify a country code and a language code to narrow down the search to relevant regions and languages.
3. Optionally, indicate the maximum number of articles you want the agent to return.
4. The agent will perform a news search using the provided keywords and parameters, then present the results in a clear format.

# Workflows
### Workflow 1: Basic News Search
- **Input Required:** Keywords
- **Tool Used:** GoogleNews_SearchNewsStories
  - **Parameters:** 
    - `keywords`: User-provided keywords
- **Outcome:** Return a list of news articles related to the specified keywords.

### Workflow 2: Geolocated News Search
- **Input Required:** Keywords, Country Code
- **Tool Used:** GoogleNews_SearchNewsStories
  - **Parameters:**
    - `keywords`: User-provided keywords
    - `country_code`: User-specified country code
- **Outcome:** Return news articles that are specific to the identified country based on the keywords.

### Workflow 3: Language-Specific News Search
- **Input Required:** Keywords, Language Code
- **Tool Used:** GoogleNews_SearchNewsStories
  - **Parameters:** 
    - `keywords`: User-provided keywords
    - `language_code`: User-specified language code
- **Outcome:** Return news articles in the specified language related to the keywords.

### Workflow 4: Customized News Search
- **Input Required:** Keywords, Country Code, Language Code, Limit
- **Tool Used:** GoogleNews_SearchNewsStories
  - **Parameters:**
    - `keywords`: User-provided keywords
    - `country_code`: User-specified country code
    - `language_code`: User-specified language code
    - `limit`: User-specified maximum number of articles
- **Outcome:** Return a limited number of tailored news articles based on the provided parameters.

## MCP Servers

The agent uses tools from these Arcade MCP Servers:

- GoogleNews

## Getting Started

1. Install dependencies:
    ```bash
    bun install
    ```

2. Set your environment variables:

    Copy the `.env.example` file to create a new `.env` file, and fill in the environment variables.
    ```bash
    cp .env.example .env
    ```

3. Run the agent:
    ```bash
    bun run main.ts
    ```