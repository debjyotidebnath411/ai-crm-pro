# AI CRM Pro – AI-First HCP Interaction Logging System

## Overview

This is an AI-first CRM system where AI is not an add-on, but a core component driving interaction logging and automation.

AI CRM Pro is a prototype CRM system for logging and managing Healthcare Professional (HCP) interactions. It supports two input methods:

* Structured Form Entry
* Conversational AI Chat Logging

The system uses LangGraph workflows and Groq-hosted LLMs to convert natural language interactions into structured CRM records.

---

## Real-World Use Case

This system is designed for pharmaceutical field representatives who interact with healthcare professionals (HCPs) daily.

Instead of manually filling CRM forms after meetings, reps can quickly log interactions using conversational input, allowing the AI to automatically structure and store the data.

This improves efficiency, reduces reporting time, and ensures accurate capture of key commercial insights such as HCP sentiment, product adoption signals, prescription behavior indicators, and follow-up commitments.

---

## Core Features

### Log Interaction Screen

Users can log HCP interactions through:

#### 1. Structured Form

Capture:

* HCP Name
* Interaction Type
* Date / Time
* Attendees
* Topics Discussed
* Materials Shared
* Samples Provided
* Sentiment
* Outcomes
* Follow-up Actions

#### 2. Conversational Chat

Example:

> Met Dr. Sharma today. Discussed diabetes therapy adoption. Positive response. Follow-up next week.

The AI extracts and structures the data automatically.

---

## Tech Stack

### Frontend

* React.js
* Redux Toolkit
* CSS
* Google Inter Font

### Backend

* Python
* FastAPI
* Uvicorn

### AI Layer

* LangGraph
* Groq API
* llama-3.3-70b-versatile 

### Database

* PostgreSQL

---

## LangGraph Role

LangGraph acts as the orchestration layer for managing HCP interaction workflows.

It interprets user intent from conversational input and dynamically routes requests to specialized tools such as logging interactions, editing records, sentiment analysis, and follow-up generation.

This enables the system to convert unstructured field notes into structured CRM data in real time, reducing manual data entry for field representatives.

Examples:

* Create interaction
* Edit interaction
* Analyze sentiment
* Generate follow-up
* Produce insights

---

## Tools Implemented

1. Log Interaction Tool  
   Captures interaction details from structured form input or conversational chat.  
   Uses LLM-based entity extraction to identify key fields such as HCP name, topics discussed, sentiment, and follow-up actions, and stores them in the database.

2. Edit Interaction Tool
   Updates previously logged entries.

3. Sentiment Tool
   Detects positive / neutral / negative tone.

4. Follow-up Tool
   Suggests next actions.

5. Insights Tool
   Summarizes patterns or recommendations.

6. Intent Detection Tool
   Routes requests inside LangGraph.

7. Voice Note Summary Tool
   Converts spoken notes into structured summaries.

---

## Project Structure

```text id="f1m8e2"
/backend   FastAPI APIs, LangGraph workflow, database logic
/frontend  React UI, Redux store, screens
```

---

## Run Locally

### Backend

```bash id="d9r2aq"
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash id="u2mx4v"
cd frontend
npm install
npm start
```

---

## Environment Variables

Create `backend/.env`

```env id="c8np3r"
GROQ_API_KEY=your_key_here
MODEL_NAME=gemma2-9b-it
DATABASE_URL=your_postgres_url
```

---

## API Endpoints

* `POST /chat`
* `POST /save`
* `POST /voice-summary`

---

## Screenshots

Add these images to improve submission quality:

* Main UI screen
* Chat interaction example
* Database table
* AI generated output

---

## Author

Debjyoti Debnath
