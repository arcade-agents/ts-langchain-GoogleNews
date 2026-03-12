---
title: "Build a GoogleNews agent with LangChain (TypeScript) and Arcade"
slug: "ts-langchain-GoogleNews"
framework: "langchain-ts"
language: "typescript"
toolkits: ["GoogleNews"]
tools: []
difficulty: "beginner"
generated_at: "2026-03-12T01:34:58Z"
source_template: "ts_langchain"
agent_repo: ""
tags:
  - "langchain"
  - "typescript"
  - "googlenews"
---

# Build a GoogleNews agent with LangChain (TypeScript) and Arcade

In this tutorial you'll build an AI agent using [LangChain](https://js.langchain.com/) with [LangGraph](https://langchain-ai.github.io/langgraphjs/) in TypeScript and [Arcade](https://arcade.dev) that can interact with GoogleNews tools — with built-in authorization and human-in-the-loop support.

## Prerequisites

- The [Bun](https://bun.com) runtime
- An [Arcade](https://arcade.dev) account and API key
- An OpenAI API key

## Project Setup

First, create a directory for this project, and install all the required dependencies:

````bash
mkdir googlenews-agent && cd googlenews-agent
bun install @arcadeai/arcadejs @langchain/langgraph @langchain/core langchain chalk
````

## Start the agent script

Create a `main.ts` script, and import all the packages and libraries. Imports from 
the `"./tools"` package may give errors in your IDE now, but don't worry about those
for now, you will write that helper package later.

````typescript
"use strict";
import { getTools, confirm, arcade } from "./tools";
import { createAgent } from "langchain";
import {
  Command,
  MemorySaver,
  type Interrupt,
} from "@langchain/langgraph";
import chalk from "chalk";
import * as readline from "node:readline/promises";
````

## Configuration

In `main.ts`, configure your agent's toolkits, system prompt, and model. Notice
how the system prompt tells the agent how to navigate different scenarios and
how to combine tool usage in specific ways. This prompt engineering is important
to build effective agents. In fact, the more agentic your application, the more
relevant the system prompt to truly make the agent useful and effective at
using the tools at its disposal.

````typescript
// configure your own values to customize your agent

// The Arcade User ID identifies who is authorizing each service.
const arcadeUserID = process.env.ARCADE_USER_ID;
if (!arcadeUserID) {
  throw new Error("Missing ARCADE_USER_ID. Add it to your .env file.");
}
// This determines which MCP server is providing the tools, you can customize this to make a Slack agent, or Notion agent, etc.
// all tools from each of these MCP servers will be retrieved from arcade
const toolkits=['GoogleNews'];
// This determines isolated tools that will be
const isolatedTools=[];
// This determines the maximum number of tool definitions Arcade will return
const toolLimit = 100;
// This prompt defines the behavior of the agent.
const systemPrompt = "Below is a ready-to-use ReAct-style prompt you can give to an AI agent that will call the GoogleNews_SearchNewsStories tool. It explains the agent\u2019s purpose, gives clear instructions and formatting rules, and defines concrete workflows (with tool sequences and examples) so the agent uses the tool effectively and safely.\n\nIntroduction\n------------\nYou are an information-gathering ReAct agent whose purpose is to find, synthesize, and present up-to-date news stories using the GoogleNews_SearchNewsStories tool. Your outputs should be accurate, concise, and well-cited. You will use the tool to retrieve news articles and then reason, summarize, compare, or monitor topics for the user.\n\nInstructions\n------------\n- Follow the ReAct format precisely. For every reasoning/action step use the structured blocks shown in the examples below:\n  - Thought: (concise, non-sensitive reasoning about the next step \u2014 do NOT reveal private chain-of-thought)\n  - Action: (the tool name to call, or \"Answer\" when returning final output)\n  - Action Input: (JSON object of parameters when calling a tool)\n  - Observation: (the tool output \u2014 filled automatically after the tool runs)\n  - Final Answer: (deliver the user-facing summary, with citations)\n- Keep \"Thought\" entries short and functional (one sentence max). Do not produce extended internal chain-of-thought.\n- Always call GoogleNews_SearchNewsStories to obtain news content before making factual claims about recent events.\n- When calling the tool, use these parameters as appropriate:\n  - keywords (required): concise keyword string for the search\n  - language_code (optional, default \"en\"): 2-letter language code\n  - country_code (optional): 2-letter country code to bias results (e.g., \"us\")\n  - limit (optional): max number of articles to fetch (recommended 3\u201310 for summaries)\n- After receiving Observation(s) from the tool:\n  - Extract article title, source, publish date (if available), and URL for each item.\n  - Summarize key facts in 2\u20134 bullet points.\n  - Mark uncertain facts explicitly (e.g., \"date not provided in results\").\n  - Provide direct citations (title + source + URL). If the tool returns no results, ask the user to clarify or broaden the query.\n- If the user asks for analysis (comparison, trends, sentiment), synthesize only from the articles returned by the tool or explicitly state if you need more articles.\n- Do not hallucinate article content. If a claim is not supported by the observed articles, state that you could not confirm it.\n- Error handling:\n  - If the tool returns an error or empty set, produce an Observation that reflects the error and respond with a clarifying question or a suggested broadened query.\n  - If rate-limited, inform the user and suggest retry intervals.\n- Respect user preferences for language, country, and number of articles; if not provided, ask a clarification question.\n\nWorkflows\n---------\nBelow are common workflows and the specific sequence of actions/tools the agent should follow in each case.\n\n1) Single-query News Summary\n   Purpose: Retrieve the latest articles about a single topic and provide a concise summary.\n   Sequence:\n     - Thought: Decide a precise keywords string and parameters (language/country/limit).\n     - Action: GoogleNews_SearchNewsStories\n     - Action Input: { \"keywords\": \"...\", \"language_code\": \"en\", \"country_code\": \"us\", \"limit\": 5 }\n     - Observation: (tool response)\n     - Thought: Synthesize the top findings and prepare citations.\n     - Action: Answer\n     - Final Answer: Provide a short summary, 2\u20134 bullets, and list of cited articles (title \u2014 source \u2014 URL).\n   Example:\n   ```\n   Thought: Search for news about \"Apple launches new iPhone\" in US English, top 5 articles.\n   Action: GoogleNews_SearchNewsStories\n   Action Input: { \"keywords\": \"Apple launches new iPhone\", \"language_code\": \"en\", \"country_code\": \"us\", \"limit\": 5 }\n   Observation: \u003ctool output\u003e\n   Thought: Summarize differences and cite articles.\n   Action: Answer\n   Final Answer: \u003csummary + citations\u003e\n   ```\n\n2) Comparative Analysis (e.g., Company A vs Company B)\n   Purpose: Collect recent reporting about two or more entities and highlight differences.\n   Sequence:\n     - Thought: Construct separate searches for each entity and choose a limit per search.\n     - Action: GoogleNews_SearchNewsStories\n     - Action Input: { \"keywords\": \"Company A news\", \"language_code\": \"...\", \"limit\": 5 }\n     - Observation: \u003cresults A\u003e\n     - Thought: Search for Company B.\n     - Action: GoogleNews_SearchNewsStories\n     - Action Input: { \"keywords\": \"Company B news\", \"language_code\": \"...\", \"limit\": 5 }\n     - Observation: \u003cresults B\u003e\n     - Thought: Compare factual claims across retrieved articles.\n     - Action: Answer\n     - Final Answer: Provide side-by-side bullets, claim-level citations to articles for each side, and a short conclusion about differences/overlap.\n   Notes: If coverage is uneven, explicitly state which side had fewer articles and recommend additional searches.\n\n3) Topic Monitoring / Alerting (ongoing)\n   Purpose: Monitor a topic over time and surface new items or trends.\n   Sequence for a single monitoring run:\n     - Thought: Use keywords and sensible limit to capture new reports.\n     - Action: GoogleNews_SearchNewsStories\n     - Action Input: { \"keywords\": \"\u003ctopic\u003e\", \"language_code\": \"\u003clang\u003e\", \"limit\": 10 }\n     - Observation: \u003cresults\u003e\n     - Thought: Identify which items are new vs previously seen (requires external state from the orchestrator).\n     - Action: Answer\n     - Final Answer: Return list of newly found articles with short summaries and timestamps.\n   Notes:\n     - The agent should request the orchestrator/user to provide previously seen article URLs or IDs to deduplicate.\n     - For long-running monitoring, schedule periodic runs and report deltas only.\n\n4) Trend Analysis and Topic Clustering\n   Purpose: Find emerging themes across multiple articles.\n   Sequence:\n     - Thought: Pull a broader set of articles (limit 10\u201320) for the specified keywords or related queries.\n     - Action: GoogleNews_SearchNewsStories\n     - Action Input: { \"keywords\": \"\u003ctopic OR related terms\u003e\", \"language_code\": \"en\", \"limit\": 15 }\n     - Observation: \u003cresults\u003e\n     - Thought: Group articles by subtopics (policy, product, finance, etc.) and extract representative citations.\n     - Action: Answer\n     - Final Answer: Provide 3\u20136 clusters, 1\u20132 bullet summary per cluster, and 1\u20132 representative citations per cluster.\n\n5) Clarifying Ambiguous Queries\n   Purpose: Ask targeted questions before searching when the user\u2019s query is ambiguous.\n   Process:\n     - Thought: Detect ambiguity (multiple meanings, missing time/country/language).\n     - Action: Answer\n     - Final Answer: Ask one targeted clarifying question (e.g., which country/timeframe/language or whether to compare vs monitor).\n   Example clarifier: \"Do you want worldwide coverage or a specific country? Also, what time window and how many articles should I retrieve?\"\n\nTool Use Examples (format)\n--------------------------\n- Example call with JSON parameters:\n  ```\n  Action: GoogleNews_SearchNewsStories\n  Action Input: { \n    \"keywords\": \"Microsoft CEO interview antitrust\", \n    \"language_code\": \"en\", \n    \"country_code\": \"us\", \n    \"limit\": 5 \n  }\n  ```\n- After the tool returns Observation, produce a concise Final Answer with explicit citations:\n  - Title \u2014 Source \u2014 URL\n  - If an article field is missing (e.g., date), indicate \"date not provided in result.\"\n- When summarizing, include only facts supported by the cited articles. For connections or inference, label them as analysis or interpretation.\n\nOutput Quality Checklist\n------------------------\nBefore returning the Final Answer, ensure:\n- Each factual claim is supported by at least one cited article from Observation.\n- You provide direct citations (title, source, URL).\n- The user can quickly see the most important facts in 2\u20134 bullets.\n- You asked clarifying questions if the user\u2019s request is ambiguous or under-specified.\n- You kept \"Thought\" entries short and purposeful and did not leak internal chain-of-thought.\n\nFailure Modes \u0026 Recovery\n------------------------\n- No results found: Ask the user to broaden keywords, remove country restriction, or confirm time/language preferences.\n- Partial info / missing fields: Report which fields were missing and avoid asserting missing details as facts.\n- API error or rate limit: Report the error in Observation and ask to retry; propose a backoff (e.g., \"I\u0027ll retry in X seconds\" if automated retry is allowed).\n\nSample Full Interaction (illustrative)\n--------------------------------------\n```\nThought: User asked for latest news about \"heatwaves in Europe\" \u2014 search in English, limit 6.\nAction: GoogleNews_SearchNewsStories\nAction Input: { \"keywords\": \"heatwaves Europe 2026\", \"language_code\": \"en\", \"limit\": 6 }\nObservation: \u003ctool result \u2014 list of articles\u003e\nThought: Summarize main impacts and cite top 3 articles.\nAction: Answer\nFinal Answer:\n- Key points:\n  1) Several EU countries reported record temperatures and wildfires (supported by Article A \u2014 Source \u2014 URL).\n  2) Power grid stress and water shortages mentioned in Article B \u2014 Source \u2014 URL.\n  3) Governments issued health advisories; adaptation policy debate noted in Article C \u2014 Source \u2014 URL.\n- Citations:\n  - \"Title A\" \u2014 Source A \u2014 https://...\n  - \"Title B\" \u2014 Source B \u2014 https://...\n  - \"Title C\" \u2014 Source C \u2014 https://...\n```\n\nUse this prompt as the agent\u2019s operating instructions. It makes explicit the expected ReAct structure, how to call the GoogleNews_SearchNewsStories tool, how to synthesize results, how to cite them, and provides workflows for common user requests.";
// This determines which LLM will be used inside the agent
const agentModel = process.env.OPENAI_MODEL;
if (!agentModel) {
  throw new Error("Missing OPENAI_MODEL. Add it to your .env file.");
}
// This allows LangChain to retain the context of the session
const threadID = "1";
````

Set the following environment variables in a `.env` file:

````bash
ARCADE_API_KEY=your-arcade-api-key
ARCADE_USER_ID=your-arcade-user-id
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-mini
````

## Implementing the `tools.ts` module

The `tools.ts` module fetches Arcade tool definitions and converts them to LangChain-compatible tools using Arcade's Zod schema conversion:

### Create the file and import the dependencies

Create a `tools.ts` file, and add import the following. These will allow you to build the helper functions needed to convert Arcade tool definitions into a format that LangChain can execute. Here, you also define which tools will require human-in-the-loop confirmation. This is very useful for tools that may have dangerous or undesired side-effects if the LLM hallucinates the values in the parameters. You will implement the helper functions to require human approval in this module.

````typescript
import { Arcade } from "@arcadeai/arcadejs";
import {
  type ToolExecuteFunctionFactoryInput,
  type ZodTool,
  executeZodTool,
  isAuthorizationRequiredError,
  toZod,
} from "@arcadeai/arcadejs/lib/index";
import { type ToolExecuteFunction } from "@arcadeai/arcadejs/lib/zod/types";
import { tool } from "langchain";
import {
  interrupt,
} from "@langchain/langgraph";
import readline from "node:readline/promises";

// This determines which tools require human in the loop approval to run
const TOOLS_WITH_APPROVAL = [];
````

### Create a confirmation helper for human in the loop

The first helper that you will write is the `confirm` function, which asks a yes or no question to the user, and returns `true` if theuser replied with `"yes"` and `false` otherwise.

````typescript
// Prompt user for yes/no confirmation
export async function confirm(question: string, rl?: readline.Interface): Promise<boolean> {
  let shouldClose = false;
  let interface_ = rl;

  if (!interface_) {
      interface_ = readline.createInterface({
          input: process.stdin,
          output: process.stdout,
      });
      shouldClose = true;
  }

  const answer = await interface_.question(`${question} (y/n): `);

  if (shouldClose) {
      interface_.close();
  }

  return ["y", "yes"].includes(answer.trim().toLowerCase());
}
````

Tools that require authorization trigger a LangGraph interrupt, which pauses execution until the user completes authorization in their browser.

### Create the execution helper

This is a wrapper around the `executeZodTool` function. Before you execute the tool, however, there are two logical checks to be made:

1. First, if the tool the agent wants to invoke is included in the `TOOLS_WITH_APPROVAL` variable, human-in-the-loop is enforced by calling `interrupt` and passing the necessary data to call the `confirm` helper. LangChain will surface that `interrupt` to the agentic loop, and you will be required to "resolve" the interrupt later on. For now, you can assume that the reponse of the `interrupt` will have enough information to decide whether to execute the tool or not, depending on the human's reponse.
2. Second, if the tool was approved by the human, but it doesn't have the authorization of the integration to run, then you need to present an URL to the user so they can authorize the OAuth flow for this operation. For this, an execution is attempted, that may fail to run if the user is not authorized. When it fails, you interrupt the flow and send the authorization request for the harness to handle. If the user authorizes the tool, the harness will reply with an `{authorized: true}` object, and the system will retry the tool call without interrupting the flow.

````typescript
export function executeOrInterruptTool({
  zodToolSchema,
  toolDefinition,
  client,
  userId,
}: ToolExecuteFunctionFactoryInput): ToolExecuteFunction<any> {
  const { name: toolName } = zodToolSchema;

  return async (input: unknown) => {
    try {

      // If the tool is on the list that enforces human in the loop, we interrupt the flow and ask the user to authorize the tool

      if (TOOLS_WITH_APPROVAL.includes(toolName)) {
        const hitl_response = interrupt({
          authorization_required: false,
          hitl_required: true,
          tool_name: toolName,
          input: input,
        });

        if (!hitl_response.authorized) {
          // If the user didn't approve the tool call, we throw an error, which will be handled by LangChain
          throw new Error(
            `Human in the loop required for tool call ${toolName}, but user didn't approve.`
          );
        }
      }

      // Try to execute the tool
      const result = await executeZodTool({
        zodToolSchema,
        toolDefinition,
        client,
        userId,
      })(input);
      return result;
    } catch (error) {
      // If the tool requires authorization, we interrupt the flow and ask the user to authorize the tool
      if (error instanceof Error && isAuthorizationRequiredError(error)) {
        const response = await client.tools.authorize({
          tool_name: toolName,
          user_id: userId,
        });

        // We interrupt the flow here, and pass everything the handler needs to get the user's authorization
        const interrupt_response = interrupt({
          authorization_required: true,
          authorization_response: response,
          tool_name: toolName,
          url: response.url ?? "",
        });

        // If the user authorized the tool, we retry the tool call without interrupting the flow
        if (interrupt_response.authorized) {
          const result = await executeZodTool({
            zodToolSchema,
            toolDefinition,
            client,
            userId,
          })(input);
          return result;
        } else {
          // If the user didn't authorize the tool, we throw an error, which will be handled by LangChain
          throw new Error(
            `Authorization required for tool call ${toolName}, but user didn't authorize.`
          );
        }
      }
      throw error;
    }
  };
}
````

### Create the tool retrieval helper

The last helper function of this module is the `getTools` helper. This function will take the configurations you defined in the `main.ts` file, and retrieve all of the configured tool definitions from Arcade. Those definitions will then be converted to LangGraph `Function` tools, and will be returned in a format that LangChain can present to the LLM so it can use the tools and pass the arguments correctly. You will pass the `executeOrInterruptTool` helper you wrote in the previous section so all the bindings to the human-in-the-loop and auth handling are programmed when LancChain invokes a tool.


````typescript
// Initialize the Arcade client
export const arcade = new Arcade();

export type GetToolsProps = {
  arcade: Arcade;
  toolkits?: string[];
  tools?: string[];
  userId: string;
  limit?: number;
}


export async function getTools({
  arcade,
  toolkits = [],
  tools = [],
  userId,
  limit = 100,
}: GetToolsProps) {

  if (toolkits.length === 0 && tools.length === 0) {
      throw new Error("At least one tool or toolkit must be provided");
  }

  // Todo(Mateo): Add pagination support
  const from_toolkits = await Promise.all(toolkits.map(async (tkitName) => {
      const definitions = await arcade.tools.list({
          toolkit: tkitName,
          limit: limit
      });
      return definitions.items;
  }));

  const from_tools = await Promise.all(tools.map(async (toolName) => {
      return await arcade.tools.get(toolName);
  }));

  const all_tools = [...from_toolkits.flat(), ...from_tools];
  const unique_tools = Array.from(
      new Map(all_tools.map(tool => [tool.qualified_name, tool])).values()
  );

  const arcadeTools = toZod({
    tools: unique_tools,
    client: arcade,
    executeFactory: executeOrInterruptTool,
    userId: userId,
  });

  // Convert Arcade tools to LangGraph tools
  const langchainTools = arcadeTools.map(({ name, description, execute, parameters }) =>
    (tool as Function)(execute, {
      name,
      description,
      schema: parameters,
    })
  );

  return langchainTools;
}
````

## Building the Agent

Back on the `main.ts` file, you can now call the helper functions you wrote to build the agent.

### Retrieve the configured tools

Use the `getTools` helper you wrote to retrieve the tools from Arcade in LangChain format:

````typescript
const tools = await getTools({
  arcade,
  toolkits: toolkits,
  tools: isolatedTools,
  userId: arcadeUserID,
  limit: toolLimit,
});
````

### Write an interrupt handler

When LangChain is interrupted, it will emit an event in the stream that you will need to handle and resolve based on the user's behavior. For a human-in-the-loop interrupt, you will call the `confirm` helper you wrote earlier, and indicate to the harness whether the human approved the specific tool call or not. For an auth interrupt, you will present the OAuth URL to the user, and wait for them to finishe the OAuth dance before resolving the interrupt with `{authorized: true}` or `{authorized: false}` if an error occurred:

````typescript
async function handleInterrupt(
  interrupt: Interrupt,
  rl: readline.Interface
): Promise<{ authorized: boolean }> {
  const value = interrupt.value;
  const authorization_required = value.authorization_required;
  const hitl_required = value.hitl_required;
  if (authorization_required) {
    const tool_name = value.tool_name;
    const authorization_response = value.authorization_response;
    console.log("⚙️: Authorization required for tool call", tool_name);
    console.log(
      "⚙️: Please authorize in your browser",
      authorization_response.url
    );
    console.log("⚙️: Waiting for you to complete authorization...");
    try {
      await arcade.auth.waitForCompletion(authorization_response.id);
      console.log("⚙️: Authorization granted. Resuming execution...");
      return { authorized: true };
    } catch (error) {
      console.error("⚙️: Error waiting for authorization to complete:", error);
      return { authorized: false };
    }
  } else if (hitl_required) {
    console.log("⚙️: Human in the loop required for tool call", value.tool_name);
    console.log("⚙️: Please approve the tool call", value.input);
    const approved = await confirm("Do you approve this tool call?", rl);
    return { authorized: approved };
  }
  return { authorized: false };
}
````

### Create an Agent instance

Here you create the agent using the `createAgent` function. You pass the system prompt, the model, the tools, and the checkpointer. When the agent runs, it will automatically use the helper function you wrote earlier to handle tool calls and authorization requests.

````typescript
const agent = createAgent({
  systemPrompt: systemPrompt,
  model: agentModel,
  tools: tools,
  checkpointer: new MemorySaver(),
});
````

### Write the invoke helper

This last helper function handles the streaming of the agent’s response, and captures the interrupts. When the system detects an interrupt, it adds the interrupt to the `interrupts` array, and the flow interrupts. If there are no interrupts, it will just stream the agent’s to your console.

````typescript
async function streamAgent(
  agent: any,
  input: any,
  config: any
): Promise<Interrupt[]> {
  const stream = await agent.stream(input, {
    ...config,
    streamMode: "updates",
  });
  const interrupts: Interrupt[] = [];

  for await (const chunk of stream) {
    if (chunk.__interrupt__) {
      interrupts.push(...(chunk.__interrupt__ as Interrupt[]));
      continue;
    }
    for (const update of Object.values(chunk)) {
      for (const msg of (update as any)?.messages ?? []) {
        console.log("🤖: ", msg.toFormattedString());
      }
    }
  }

  return interrupts;
}
````

### Write the main function

Finally, write the main function that will call the agent and handle the user input.

Here the `config` object configures the `thread_id`, which tells the agent to store the state of the conversation into that specific thread. Like any typical agent loop, you:

1. Capture the user input
2. Stream the agent's response
3. Handle any authorization interrupts
4. Resume the agent after authorization
5. Handle any errors
6. Exit the loop if the user wants to quit

````typescript
async function main() {
  const config = { configurable: { thread_id: threadID } };
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log(chalk.green("Welcome to the chatbot! Type 'exit' to quit."));
  while (true) {
    const input = await rl.question("> ");
    if (input.toLowerCase() === "exit") {
      break;
    }
    rl.pause();

    try {
      let agentInput: any = {
        messages: [{ role: "user", content: input }],
      };

      // Loop until no more interrupts
      while (true) {
        const interrupts = await streamAgent(agent, agentInput, config);

        if (interrupts.length === 0) {
          break; // No more interrupts, we're done
        }

        // Handle all interrupts
        const decisions: any[] = [];
        for (const interrupt of interrupts) {
          decisions.push(await handleInterrupt(interrupt, rl));
        }

        // Resume with decisions, then loop to check for more interrupts
        // Pass single decision directly, or array for multiple interrupts
        agentInput = new Command({ resume: decisions.length === 1 ? decisions[0] : decisions });
      }
    } catch (error) {
      console.error(error);
    }

    rl.resume();
  }
  console.log(chalk.red("👋 Bye..."));
  process.exit(0);
}

// Run the main function
main().catch((err) => console.error(err));
````

## Running the Agent

### Run the agent

```bash
bun run main.ts
```

You should see the agent responding to your prompts like any model, as well as handling any tool calls and authorization requests.

## Next Steps

- Clone the [repository](https://github.com/arcade-agents/ts-langchain-GoogleNews) and run it
- Add more toolkits to the `toolkits` array to expand capabilities
- Customize the `systemPrompt` to specialize the agent's behavior
- Explore the [Arcade documentation](https://docs.arcade.dev) for available toolkits

