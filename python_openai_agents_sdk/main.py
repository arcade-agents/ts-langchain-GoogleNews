from agents import (Agent, Runner, AgentHooks, Tool, RunContextWrapper,
                    TResponseInputItem,)
from functools import partial
from arcadepy import AsyncArcade
from agents_arcade import get_arcade_tools
from typing import Any
from human_in_the_loop import (UserDeniedToolCall,
                               confirm_tool_usage,
                               auth_tool)

import globals


class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self,
                       context: RunContextWrapper,
                       agent: Agent) -> None:
        self.event_counter += 1
        print(f"### ({self.display_name}) {
              self.event_counter}: Agent {agent.name} started")

    async def on_end(self,
                     context: RunContextWrapper,
                     agent: Agent,
                     output: Any) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                # agent.name} ended with output {output}"
                agent.name} ended"
        )

    async def on_handoff(self,
                         context: RunContextWrapper,
                         agent: Agent,
                         source: Agent) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                source.name} handed off to {agent.name}"
        )

    async def on_tool_start(self,
                            context: RunContextWrapper,
                            agent: Agent,
                            tool: Tool) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}:"
            f" Agent {agent.name} started tool {tool.name}"
            f" with context: {context.context}"
        )

    async def on_tool_end(self,
                          context: RunContextWrapper,
                          agent: Agent,
                          tool: Tool,
                          result: str) -> None:
        self.event_counter += 1
        print(
            f"### ({self.display_name}) {self.event_counter}: Agent {
                # agent.name} ended tool {tool.name} with result {result}"
                agent.name} ended tool {tool.name}"
        )


async def main():

    context = {
        "user_id": os.getenv("ARCADE_USER_ID"),
    }

    client = AsyncArcade()

    arcade_tools = await get_arcade_tools(
        client, toolkits=["GoogleNews"]
    )

    for tool in arcade_tools:
        # - human in the loop
        if tool.name in ENFORCE_HUMAN_CONFIRMATION:
            tool.on_invoke_tool = partial(
                confirm_tool_usage,
                tool_name=tool.name,
                callback=tool.on_invoke_tool,
            )
        # - auth
        await auth_tool(client, tool.name, user_id=context["user_id"])

    agent = Agent(
        name="",
        instructions="# Introduction
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
        model=os.environ["OPENAI_MODEL"],
        tools=arcade_tools,
        hooks=CustomAgentHooks(display_name="")
    )

    # initialize the conversation
    history: list[TResponseInputItem] = []
    # run the loop!
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            break
        history.append({"role": "user", "content": prompt})
        try:
            result = await Runner.run(
                starting_agent=agent,
                input=history,
                context=context
            )
            history = result.to_input_list()
            print(result.final_output)
        except UserDeniedToolCall as e:
            history.extend([
                {"role": "assistant",
                 "content": f"Please confirm the call to {e.tool_name}"},
                {"role": "user",
                 "content": "I changed my mind, please don't do it!"},
                {"role": "assistant",
                 "content": f"Sure, I cancelled the call to {e.tool_name}."
                 " What else can I do for you today?"
                 },
            ])
            print(history[-1]["content"])

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())