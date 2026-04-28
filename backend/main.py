from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai_agent import run_agent, run_voice_agent
from database import SessionLocal
from sqlalchemy import text
import tempfile
import whisper
import os



model = whisper.load_model("base")


app = FastAPI(title="AI CRM HCP Module")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    current_form: dict = {}


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "AI CRM HCP Backend"
    }

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        result = run_agent(
            user_text=req.message,
            current_form=req.current_form
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    
    from database import SessionLocal
from sqlalchemy import text

@app.post("/save")
def save_interaction(data: dict):
    print("Saving to DB:", data)   

    try:
        db = SessionLocal()

        query = text("""
        INSERT INTO interactions (
            hcp_name, interaction_type, date, time,
            attendees, topics, materials, samples,
            sentiment, outcomes, follow_up
        ) VALUES (
            :hcp_name, :interaction_type, :date, :time,
            :attendees, :topics, :materials, :samples,
            :sentiment, :outcomes, :follow_up
        )
        """)

        db.execute(query, data)
        db.commit()
        db.close()

        return {"success": True}

    except Exception as e:
        print("DB ERROR:", str(e))
        return {"success": False, "error": str(e)}


@app.post("/voice-summary")
async def voice_summary(file: UploadFile = File(...)):
    try:
        temp_file = f"temp_{file.filename}"

        with open(temp_file, "wb") as f:
            f.write(await file.read())

        result = model.transcribe(
            temp_file,
            language="en",
            fp16=False
        )

        transcript = result["text"]

        print("RAW TRANSCRIPT:", transcript)

        ai = run_voice_agent(transcript)

        os.remove(temp_file)

        return {
            "success": True,
            "data": ai,
            "transcript": transcript
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@app.post("/save")
def save_interaction(data: dict):
    print("Saving to DB:", data)   

    try:
        db = SessionLocal()

        query = text("""
        INSERT INTO interactions (
            hcp_name, interaction_type, date, time,
            attendees, topics, materials, samples,
            sentiment, outcomes, follow_up
        ) VALUES (
            :hcp_name, :interaction_type, :date, :time,
            :attendees, :topics, :materials, :samples,
            :sentiment, :outcomes, :follow_up
        )
        """)

        db.execute(query, data)
        db.commit()
        db.close()

        result = db.execute(query, data)
        db.commit()

        # get inserted id
        new_id = result.lastrowid

        db.close()

        return {"success": True, "id": new_id}

    except Exception as e:
        print("DB ERROR:", str(e))
        return {"success": False, "error": str(e)}
    

@app.put("/update/{interaction_id}")
def update_interaction(interaction_id: int, data: dict):
    print("Updating DB:", interaction_id, data)

    try:
        db = SessionLocal()

        query = text("""
        UPDATE interactions SET
            hcp_name = :hcp_name,
            interaction_type = :interaction_type,
            date = :date,
            time = :time,
            attendees = :attendees,
            topics = :topics,
            materials = :materials,
            samples = :samples,
            sentiment = :sentiment,
            outcomes = :outcomes,
            follow_up = :follow_up
        WHERE id = :id
        """)

        data["id"] = interaction_id

        db.execute(query, data)
        db.commit()
        db.close()

        return {"success": True}

    except Exception as e:
        print("UPDATE ERROR:", str(e))
        return {"success": False, "error": str(e)}

@app.get("/health")
def health():
    return {
        "ok": True
    }
