# Meta-Prompt for Blog Pipeline App Development with AI Agents

```
I need you to help me build a content pipeline using specialized AI agents in a structured, continuous workflow. The goal is to operate of publishing financial blog posts on ghost that deployed in zeabur.

## Context:
I have a repository of AI agents that can work together. Here's the agent data:
[PASTE AGENT REPOSITORY DATA HERE]

## How Agent Workflows Work:
Agents collaborate using this syntax:
> First use the [agent-name] to [task], then use the [agent-name] to [next task]

## Requirements:
1. I'll give you an app idea (which includes the tech stack), and YOU must:
   - Define the exact features and scope
   - Design an appropriate file structure for agent context sharing
   - Create a 2-phase development workflow

2. The phases should follow this pattern:
   - **Phase 1: Planning
   - **Phase 2: backend development

3. Key Constraints:
   - Each agent must save outputs and read from previous agents
   - Agents need clear handoff instructions
   - Include polished UI and micro-interactions
   - No web search allowed

## My Blog Pipeline App Idea:
[INSERT YOUR BLOG PIPELINE IDEA HERE - include content niche, platform, and specific requirements]

## What I Need From You:
1. Analyze the app idea and define:
   - EXACT features to be built (detailed scope)
   - Tech stack confirmation
   - Appropriate file structure for this project

2. Create an initial setup prompt for the file structure you design

3. Generate detailed prompts for each phase that include:
   - Which agents to use and in what order
   - Exactly what each agent should build (based on your scope)
   - Where to save their outputs
   - Where to read previous outputs
   - How to update handoff documentation

Make sure to lock the scope - agents should not add features beyond what you define. Give explicit instructions for file management and agent collaboration.
```

## How to Use This Meta-Prompt:

1. Copy the entire prompt above
2. Replace `[PASTE AGENT REPOSITORY DATA HERE]` with your agent descriptions
3. Replace `[INSERT YOUR APP IDEA HERE]` with:
   - Your app concept
   - Tech stack preferences
   - Any specific requirements
4. Submit to Claude
5. Claude will generate everything customized to your app

This is now flexible for any app type and tech stack while maintaining the agent workflow structure.