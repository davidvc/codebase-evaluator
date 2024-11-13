# Project Plan: Codebase Evaluator System

## Design
Have one agent that reads the codebase using a github URL and loads it
into a Chroma DB database

Have another agent that reads the database and generates the reports.

Have a third agent that creates a Chat UI for the codebase using Streamlit. The Chat
UI should be able to ask questions about the codebase and get answers.

When generating the code, you do not need to use a hexagonal architecture. Instead,
keep it simple and straightforward. Focus on getting it to work quickly rather
than making it maintainable. We can refactor it later.

## Execution Steps

[x] Create an agent that reads the codebase using a github URL and loads it into a Chroma DB database
[ ] Create an agent that reads the database and generates the codebase summary report
[ ] Create an agent that reads the database and generates the codebase evaluation report
[ ] Create a Chat UI for the codebase using Streamlit
