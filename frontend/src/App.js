import React, { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  updateField,
  updateForm
} from "./formSlice";
import "./App.css";
import { FaRobot, FaSearch, FaPlus } from "react-icons/fa";
import axios from "axios";


function App() {

  const form = useSelector((state) => state.form);
  const dispatch = useDispatch();

  const [chat, setChat] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const handleChange = (field, value) => {
  dispatch(updateField({ field, value }));
};
  

const handleAI = async () => {
  if (!chat.trim()) return;

  const userMessage = chat.trim();

  setLoading(true);

  setMessages((prev) => [
    ...prev,
    { role: "user", text: userMessage }
  ]);

  try {
  const res = await axios.post("http://127.0.0.1:8000/chat", {
    message: userMessage,
    current_form: form
  });

  if (!res.data.success) {
    throw new Error(res.data.error);
  }

  const data = res.data.data;

try {
  if (!data.insight) {
    await axios.post("http://127.0.0.1:8000/save", data);
    console.log("Saved to DB:", data);
  }
} catch (err) {
  console.error("DB Save Failed:", err);
}

dispatch(updateForm(data));

let aiReply = "";

if (data.insight) {
  aiReply = `📊 Insights Report:\n\n${data.insight}`;
}

else {
  aiReply = `✅ Interaction processed.

Doctor: ${data.hcp_name || "-"}
Date: ${data.date || "-"}
Sentiment: ${data.sentiment || "-"}

✔ Saved to database successfully

📌 AI Summary:
${
  data.follow_up
    ? `Doctor showed ${data.sentiment?.toLowerCase() || "neutral"} interest. Follow-up: ${data.follow_up}`
    : `${data.topics || "Interaction"} logged successfully.`
}`;
}

setMessages((prev) => [
  ...prev,
  { role: "ai", text: aiReply }
]);
} catch (error) {
  setMessages((prev) => [
    ...prev,
    {
      role: "ai",
      text: "⚠️ Backend connection failed or invalid response."
    }
  ]);

} finally {
  setLoading(false);
  setChat("");
}
};

const handleVoiceUpload = async (e) => {
  const file = e.target.files[0];

  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  setLoading(true);

  try {
    const res = await axios.post(
      "http://127.0.0.1:8000/voice-summary",
      formData
    );

    console.log(res.data);

    if (!res.data.success) {
      throw new Error(res.data.error);
    }

    const data = res.data.data;

    dispatch(
      updateForm({
        hcp_name: data.hcp_name || "",
        interaction_type: data.interaction_type || "Meeting",

        date: data.date || "",
        time: data.time || "",

        attendees: data.attendees || "",
        topics: data.topics || "",
        outcomes: data.outcomes || "",
        follow_up: data.follow_up || "",

        sentiment: data.sentiment || "Neutral",

        materials: data.materials || "",
        samples: data.samples || ""
      })
    );

    setMessages((prev) => [
      ...prev,
      {
        role: "ai",
        text:
          "🎙 Voice note summarized successfully.\n\nTranscript processed and CRM fields updated."
      }
    ]);
  } catch (err) {
    console.error(err);

    setMessages((prev) => [
      ...prev,
      {
        role: "ai",
        text: "⚠️ Voice processing failed."
      }
    ]);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="container">
      {/* LEFT PANEL */}
      <div className="left-panel">
        <h1>Log HCP Interaction</h1>

        <div className="section-title">Interaction Details</div>

        <div className="grid-2">
          <div>
            <label>HCP Name</label>
            <input
              placeholder="Search or select HCP..."
              value={form.hcp_name}
              onChange={(e) =>
                handleChange("hcp_name", e.target.value)
              }
            />
          </div>

          <div>
            <label>Interaction Type</label>
            <select
              value={form.interaction_type}
              onChange={(e) =>
                handleChange("interaction_type", e.target.value)
              }
            >
              <option>Meeting</option>
              <option>Call</option>
              <option>Email</option>
            </select>
          </div>
        </div>

        <div className="grid-2">
          <div>
            <label>Date</label>
            <input
              type="date"
              value={form.date}
              onChange={(e) =>
                dispatch(updateForm({ date: e.target.value }))
              }
            />
          </div>

          <div>
            <label>Time</label>
            <input
              type="time"
              value={form.time}
              onChange={(e) => handleChange("time", e.target.value)}
            />
          </div>
        </div>

        <label>Attendees</label>
        <input
          placeholder="Enter names or search..."
          value={form.attendees}
          onChange={(e) => handleChange("attendees", e.target.value)}
        />

        <label>Topics Discussed</label>

        <textarea
          placeholder="Enter key discussion points..."
          value={form.topics}
          onChange={(e) => handleChange("topics", e.target.value)}
        />

        <button
          type="button"
          className="voice-btn"
          onClick={() =>
            document.getElementById("voiceUpload").click()
          }
        >
          🎙 Summarize from Voice Note (Requires Consent)
        </button>

        <input
          type="file"
          id="voiceUpload"
          accept="audio/*"
          hidden
          onChange={handleVoiceUpload}
        />

        <div className="section-title">
          Materials Shared / Samples Distributed
        </div>

        <div className="small-box">
          <strong>Materials Shared</strong>
          <p>{form.materials || "No materials added."}</p>
          <button type="button">
            <FaSearch /> Search/Add
          </button>
        </div>

        <div className="small-box">
          <strong>Samples Distributed</strong>
          <p>{form.samples || "No samples added."}</p>
          <button type="button">
            <FaPlus /> Add Sample
          </button>
        </div>

        <div className="section-title">Observed/Inferred HCP Sentiment</div>

        <div className="sentiment">
          <label>
            <input
              type="radio"
              checked={form.sentiment === "Positive"}
              onChange={() => handleChange("sentiment", "Positive")}
            />
            😊 Positive
          </label>

          <label>
            <input
              type="radio"
              checked={form.sentiment === "Neutral"}
              onChange={() => handleChange("sentiment", "Neutral")}
            />
            😐 Neutral
          </label>

          <label>
            <input
              type="radio"
              checked={form.sentiment === "Negative"}
              onChange={() => handleChange("sentiment", "Negative")}
            />
            😟 Negative
          </label>
        </div>

        <label>Outcomes</label>
        <textarea
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={(e) => handleChange("outcomes", e.target.value)}
        />

        <label>Follow-up Actions</label>

        <textarea
          placeholder="Enter next steps or tasks..."
          value={form.follow_up}
          onChange={(e) =>
            handleChange("follow_up", e.target.value)
          }
        />

        {(form.hcp_name || form.topics || form.follow_up) && (
          <div className="ai-followups">
          <p>
            <strong>AI Suggested Follow-ups:</strong>
          </p>

          <ul>
            {form.follow_up && (
              <li
                onClick={() =>
                  handleChange("follow_up", form.follow_up)
                }
              >
                → {form.follow_up}
              </li>
            )}

            <li
              onClick={() =>
                handleChange(
                  "follow_up",
                  `Send ${form.materials || "product"} details to ${
                    form.hcp_name || "doctor"
                  }`
                )
              }
            >
              → Send {form.materials || "product"} details
            </li>

            <li
              onClick={() =>
                handleChange(
                  "follow_up",
                  `Share more information on ${
                    form.topics || "discussion topic"
                  }`
                )
              }
            >
              → Share more info on {form.topics || "discussion topic"}
            </li>

            {form.sentiment === "Positive" && (
              <li
                onClick={() =>
                  handleChange(
                    "follow_up",
                    "Schedule follow-up meeting next week"
                  )
                }
              >
                → Schedule follow-up meeting next week
              </li>
            )}

            {form.sentiment === "Negative" && (
              <li
                onClick={() =>
                  handleChange(
                    "follow_up",
                    "Address concerns and re-engage doctor"
                  )
                }
              >
                → Address concerns and re-engage
              </li>
            )}
          </ul>
        </div>
      )}

      </div>

        {/* RIGHT PANEL */}
        <div className="right-panel">
          <h2>
            <FaRobot /> AI Assistant
          </h2>

          <p>Log interaction details via chat</p>

          <div className="user helper-box">
            Log interaction details here (e.g. "Met Dr. Smith,
            discussed Product X efficacy, positive sentiment,
            shared brochure") or ask for help.
          </div>

          <div className="chat-box">
            {messages.map((msg, i) => (
              <div key={i} className={msg.role}>
                {msg.text}
              </div>
            ))}
          </div>

          <div className="chat-input">
            <textarea
              placeholder="Describe interaction..."
              value={chat}
              onChange={(e) => setChat(e.target.value)}
            />

            <button onClick={handleAI} disabled={loading}>
              {loading ? "Thinking..." : "Log"}
            </button>
          </div>
        </div>

        </div>
        );
        }

        export default App;
