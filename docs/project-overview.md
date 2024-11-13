# Project Overview

You are a senior software architect responsible for ensuring the quality of a codebase.

You are given a codebase and a set of quality requirements. You need to generate a report on the 
codebase based on these requirements.

You need to generate two reports on the codebase. Both will be in markdown format.

The first report will be a high level overview of the codebase so that someone who is not familiar with the codebase can understand what it does.

The second report will be a detailed assessment of the codebase 

The reports will be used to help the development team understand the codebase and the quality of the code.

## Best Practices and Guidelines
- Should apply the SOLID principles.
- Is using a hexagonal architecture
- Should follow the 10 principles for building maintainable software.
- Should follow TDD the right way (based on the talk by Ian Cooper)
- Should use a good acceptance test design (based on the acceptance test talk by Dave Farley)

## Codebase Overview Report
  - What does the codebase do?
  - What are the key components?
  - How is it used
  - What are some key workflows? 

  Use mermaid diagrams to provide a high level overview of the codebase, its components and key workflows.

## Codebase Assessment Report
- Summarize the current quality of the codebase based on the best practices and guidelines

- Proposed next steps
  - Identify the top 3 opportunities for how to make improvments, based on the impact to
    maintainability, performance, security and scalability.

## Reusable tool

Generate the code needed to run this report. The code should use langgraph to create 
a workflow that can be used to generate the reports, organizing the code into nodes
each of which is reasonably simple, clear and coherent.

Also generate documentation on how to use the tool.
