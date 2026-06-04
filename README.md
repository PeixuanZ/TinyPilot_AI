# TinyPilot_AI

A Multi-Agenet AI copilot for Infant Care and Development

## Project Summary

TinyPilot is a privacy-first multi-agent AI system designed to help parents manage and understand their child's devlopmental journey through personalized long-term memory, context-aware reasoning, and proactive assistance.

Unlike traditional parenting applications that rely heavily on cloud services and isolated features, TinyPilot maintains a persistent, personalized memory of a child's growth hisotry, feeding records, sleep patterns, milestones, appointments, and famiy observations directly on the user's device.

The system is built around a collection of specialized agents that collaborate to organize information, retrieve relevant historical context, answer parenting questions, generate personalized recommendations, and proactively identify important events that may require attention.

By combing long-term memory, retrieval-augmented reasoning, and multi-agent coordination, TinyPiot functions as an AI parenting copilot that continuously learns froma family's unique experiences while preserving privacy through local-first data storage andn on-device intelligence.

## Key features

- Long-term personlized memory of infant development
- Local-first architecture with privacy-preserving data storage
- Context-aware question answering using personal history
- Appointment and milestone tracking
- Feeding, sleep, and growth monitoring
- Multi-agent collaboration for memory scheduling, health tracking, and reasoning
- Proactive recommendations and reminders
- Extensible framework for future family knowledge management

**Example Use Cases**
>Parent: "How has my baby's sleep changed over the past month?"
>TinyPilot: "Retrieve historical sleep records, analyzes trends, compares recent patterns with the child's baseline behavior, and generates a personazlied summary".

## System Architecture

## Core Components

### 1. Orchestrator Agent

Responsiblity: acts as the central coordinator of the system

Tasks: 
- interpret user intent
- Select appropriate downstream agents
- Manage multi-agent workflows
- Aggregate agent outputs
- Generate final response

### 2. Memory Agent

Responsiblity: retrieves personalized historical information from InfantGPT.

Tasks:
- Semantic search
- Timeline retrieval
- Event lookup
- Context summarization

### 3. Analytics Agent

Responsiblity: detects trends and patterns from historical records.

Tasks:
- Sleep trend analysis
- Feeding diversity analysis
- Growth tracking
- Milestone progression analysis

Example outputs
> Night wakings increased by 35% over the past two weeks.

### 4. Planning Agent

Responsibility: generates actionable recommendations and future plans.

Tasks:
- Appointment reminders
- Vaccination reminders
- Feeding suggestions
- Developmental activity recommendations

Example
> Upcoming pediatric appointment in 3 days.
>
### 5. InfantGPT Memory Layer
Responsiblity: provides persistent long-term memory for the system.

Components:
- Structured Event Store
- Vectpr Database
- Retrieval Engine

Supported Memories:
- Feeding records
- Sleep records
- Growth measurements
- Medical visits
- Developmental milestones
- Parent notes
  
Stores
```json
{
  "event_type":"feeding",
  "food":"salmon",
  "date":"2026-06-01"
}
```

This memory layer serves as the shared knowledge foundation for all TinyPilot agents. 

## Technologies
- LLM layer
  - GPT-4o / GPT -5
  - Function Calling
  - Structured Outputs
- Agent Framework
  - PydanticAI
  - LangGraph
- Memory Layer
  - ChromaDB
  - SQLite
  - Vector Search
- Backend
  - FastAPI
- Fronted
  - Streamlit
## Key AI features
1. Personalized Memory Retrieval. E.g. "What foods has my baby tried"
2. Context-Aware Reasoning. E.g. "Is my baby's sleep getting worse"
3. Multi-step agent planning. E.g. "What should I focus on this week"
4. Proactive assistance. E.g. Automatic reminders and suggestions without explicit user requests.

# Future Extensions
**Multimodal Understanding**
Input: Baby photos, growth charts, pediatric reports.

**Smart Camera Integration**
Track: Bottle locations, toy locations, daily activities.

**Family Knowledge Graph**
Connect: Events, appointments, milestone, photos, medical nots, family members.


