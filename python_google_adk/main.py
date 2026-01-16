from arcadepy import AsyncArcade
from dotenv import load_dotenv
from google.adk import Agent, Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService, Session
from google_adk_arcade.tools import get_arcade_tools
from google.genai import types
from human_in_the_loop import auth_tool, confirm_tool_usage

import os

load_dotenv(override=True)


async def main():
    app_name = "my_agent"
    user_id = os.getenv("ARCADE_USER_ID")

    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    client = AsyncArcade()

    agent_tools = await get_arcade_tools(
        client, toolkits=["GoogleNews"]
    )

    for tool in agent_tools:
        await auth_tool(client, tool_name=tool.name, user_id=user_id)

    agent = Agent(
        model=LiteLlm(model=f"openai/{os.environ["OPENAI_MODEL"]}"),
        name="google_agent",
        instruction="# Introduction
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
- **Outcome:** Return a limited number of tailored news articles based on the provided parameters.",
        description="An agent that uses GoogleNews tools provided to perform any task",
        tools=agent_tools,
        before_tool_callback=[confirm_tool_usage],
    )

    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, state={
            "user_id": user_id,
        }
    )
    runner = Runner(
        app_name=app_name,
        agent=agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )

    async def run_prompt(session: Session, new_message: str):
        content = types.Content(
            role='user', parts=[types.Part.from_text(text=new_message)]
        )
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f'** {event.author}: {event.content.parts[0].text}')

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        await run_prompt(session, user_input)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())