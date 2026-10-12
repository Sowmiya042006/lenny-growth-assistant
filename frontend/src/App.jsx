import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";


const API_BASE_URL = "http://127.0.0.1:8000";


function safeSourceUrl(value) {
  try {
    const url = new URL(value);

    if (
      url.protocol === "https:" &&
      url.hostname === "github.com" &&
      url.pathname.startsWith(
        "/ChatPRD/lennys-podcast-transcripts/blob/"
      )
    ) {
      return url.href;
    }
  } catch {
    return null;
  }

  return null;
}


function SourceList({ sources = [] }) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return null;
  }

  return (
    <div style={{ marginTop: "16px" }}>
      <h3>Sources</h3>

      {sources.map((source, index) => {
        const url = safeSourceUrl(source.source_url);

        return (
          <details
            key={`${source.chunk_id}-${index}`}
            style={{
              marginBottom: "10px",
              padding: "12px",
              border: "1px solid #dce2eb",
              borderRadius: "8px",
              background: "#ffffff",
            }}
          >
            <summary
              style={{
                cursor: "pointer",
                overflowWrap: "anywhere",
              }}
            >
              {source.citation} {source.transcript_id}
            </summary>

            {url && (
              <p>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open original transcript
                </a>
              </p>
            )}

            <blockquote
              style={{
                margin: "12px 0",
                paddingLeft: "14px",
                borderLeft: "3px solid #2455c7",
                whiteSpace: "pre-wrap",
                lineHeight: 1.6,
              }}
            >
              {source.excerpt}
            </blockquote>
          </details>
        );
      })}
    </div>
  );
}


function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <article
      style={{
        marginBottom: "16px",
        marginLeft: isUser ? "15%" : "0",
        marginRight: isUser ? "0" : "15%",
        padding: "16px",
        borderRadius: "12px",
        background: isUser ? "#2455c7" : "#f1f4f8",
        color: isUser ? "#ffffff" : "#172033",
      }}
    >
      <strong>{isUser ? "You" : "Assistant"}</strong>

      <div
        style={{
          marginTop: "8px",
          whiteSpace: "pre-wrap",
          lineHeight: 1.7,
        }}
      >
        {message.content}
      </div>

      {!isUser && message.model && (
        <p>
          <small>
            Provider: {message.provider || "saved session"}
            {" · "}
            Model: {message.model}
          </small>
        </p>
      )}

      {!isUser && (
        <SourceList sources={message.sources} />
      )}
    </article>
  );
}


function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] =
    useState(null);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] =
    useState(true);
  const [providerConfig, setProviderConfig] =
    useState(null);

  const [essayTopic, setEssayTopic] = useState("");
  const [artifact, setArtifact] = useState(null);
  const [isGeneratingEssay, setIsGeneratingEssay] =
    useState(false);


  async function loadProviderConfig() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/config`
      );

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      setProviderConfig(data);
    } catch {
      setProviderConfig(null);
    }
  }


  async function loadSessions(selectFirst = false) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/sessions`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            "Could not load saved chats."
        );
      }

      const savedSessions = Array.isArray(data.sessions)
        ? data.sessions
        : [];

      setSessions(savedSessions);

      if (
        selectFirst &&
        savedSessions.length > 0
      ) {
        await openSession(savedSessions[0].id);
      }
    } catch (err) {
      setError(
        err.message || "Could not load saved chats."
      );
    } finally {
      setIsLoadingSessions(false);
    }
  }


  async function openSession(sessionId) {
    if (isSending || isGeneratingEssay) {
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/sessions/${sessionId}/messages`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            "Could not load this chat."
        );
      }

      setCurrentSessionId(sessionId);

      setMessages(
        Array.isArray(data.messages)
          ? data.messages
          : []
      );
    } catch (err) {
      setError(
        err.message || "Could not load this chat."
      );
    }
  }


  async function createNewChat() {
    if (isSending || isGeneratingEssay) {
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/sessions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: "New chat",
          }),
        }
      );

      const session = await response.json();

      if (!response.ok) {
        throw new Error(
          session.detail?.message ||
            "Could not create a new chat."
        );
      }

      setCurrentSessionId(session.id);
      setMessages([]);
      setMessage("");

      setSessions((previous) => [
        session,
        ...previous.filter(
          (item) => item.id !== session.id
        ),
      ]);
    } catch (err) {
      setError(
        err.message || "Could not create a new chat."
      );
    }
  }


  async function deleteCurrentChat() {
    if (
      !currentSessionId ||
      isSending ||
      isGeneratingEssay
    ) {
      return;
    }

    const confirmed = window.confirm(
      "Delete this chat and all its messages?"
    );

    if (!confirmed) {
      return;
    }

    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/sessions/${currentSessionId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            "Could not delete this chat."
        );
      }

      const remainingSessions = sessions.filter(
        (session) => session.id !== currentSessionId
      );

      setSessions(remainingSessions);
      setCurrentSessionId(null);
      setMessages([]);

      if (remainingSessions.length > 0) {
        await openSession(remainingSessions[0].id);
      }
    } catch (err) {
      setError(
        err.message || "Could not delete this chat."
      );
    }
  }


  async function generateEssay(event) {
    event.preventDefault();

    const topic = essayTopic.trim();

    if (
      !topic ||
      isGeneratingEssay ||
      isSending
    ) {
      return;
    }

    setIsGeneratingEssay(true);
    setArtifact(null);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/artifacts/essay`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            topic,
          }),
          signal: AbortSignal.timeout(900000),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            `Essay generation failed (HTTP ${response.status}).`
        );
      }

      setArtifact(data);
    } catch (err) {
      setError(
        err.name === "TimeoutError"
          ? "Essay generation took too long."
          : err.message ||
              "Could not generate the essay."
      );
    } finally {
      setIsGeneratingEssay(false);
    }
  }


  async function handleSubmit(event) {
    event.preventDefault();

    const question = message.trim();

    if (
      !question ||
      isSending ||
      isGeneratingEssay
    ) {
      return;
    }

    setIsSending(true);
    setError("");
    setMessage("");

    const temporaryUserMessage = {
      id: `temporary-${Date.now()}`,
      role: "user",
      content: question,
      model: null,
      provider: null,
      sources: [],
    };

    setMessages((previous) => [
      ...previous,
      temporaryUserMessage,
    ]);

    try {
      const response = await fetch(
        `${API_BASE_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: question,
            session_id: currentSessionId,
          }),
          signal: AbortSignal.timeout(420000),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            `Request failed (HTTP ${response.status}).`
        );
      }

      setCurrentSessionId(data.session_id);

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        provider: data.provider,
        model: data.model,
        sources: Array.isArray(data.sources)
          ? data.sources
          : [],
        grounding_status: data.grounding_status,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      await loadSessions(false);
    } catch (err) {
      setError(
        err.name === "TimeoutError"
          ? "The request took too long. Please try again."
          : err.message ||
              "Could not connect to the backend."
      );
    } finally {
      setIsSending(false);
    }
  }


  useEffect(() => {
    loadSessions(true);
    loadProviderConfig();
  }, []);


  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "260px 1fr",
        minHeight: "100vh",
        background: "#ffffff",
        color: "#172033",
      }}
    >
      <aside
        style={{
          padding: "20px",
          borderRight: "1px solid #dce2eb",
          background: "#f7f9fc",
          overflowY: "auto",
        }}
      >
        <button
          type="button"
          onClick={createNewChat}
          disabled={
            isSending ||
            isGeneratingEssay
          }
          style={{
            width: "100%",
            padding: "12px",
            marginBottom: "20px",
            cursor: "pointer",
          }}
        >
          + New Chat
        </button>

        <h2 style={{ fontSize: "18px" }}>
          Saved Chats
        </h2>

        {isLoadingSessions && (
          <p>
            <small>Loading chats...</small>
          </p>
        )}

        {!isLoadingSessions &&
          sessions.length === 0 && (
            <p>
              <small>No saved chats yet.</small>
            </p>
          )}

        {sessions.map((session) => (
          <button
            key={session.id}
            type="button"
            onClick={() => openSession(session.id)}
            disabled={
              isSending ||
              isGeneratingEssay
            }
            style={{
              width: "100%",
              padding: "10px",
              marginBottom: "8px",
              textAlign: "left",
              cursor: "pointer",
              border: "1px solid #dce2eb",
              borderRadius: "7px",
              background:
                session.id === currentSessionId
                  ? "#dce7ff"
                  : "#ffffff",
              color: "#172033",
            }}
          >
            {session.title || "New chat"}
          </button>
        ))}

        {currentSessionId && (
          <button
            type="button"
            onClick={deleteCurrentChat}
            disabled={
              isSending ||
              isGeneratingEssay
            }
            style={{
              width: "100%",
              padding: "10px",
              marginTop: "14px",
              cursor: "pointer",
              border: "1px solid #b42318",
              borderRadius: "7px",
              background: "#ffffff",
              color: "#b42318",
            }}
          >
            Delete Selected Chat
          </button>
        )}
      </aside>

      <main
        style={{
          width: "100%",
          maxWidth: "900px",
          margin: "0 auto",
          padding: "32px",
          boxSizing: "border-box",
        }}
      >
        <h1>The Lenny Growth Assistant</h1>

        <p>
          Ask product and growth questions supported by
          Lenny&apos;s Podcast transcripts.
        </p>

        {providerConfig && (
          <div
            style={{
              margin: "16px 0",
              padding: "12px",
              border: "1px solid #b7c9ee",
              borderRadius: "8px",
              background: "#eef4ff",
            }}
          >
            <strong>Active provider:</strong>{" "}
            {providerConfig.provider}
            {" · "}
            <strong>Model:</strong>{" "}
            {providerConfig.model}
            {" · "}
            <strong>Fallback:</strong>{" "}
            {providerConfig.fallback}
          </div>
        )}

        <p>
          <small>
            Chats are saved in PostgreSQL. Citation numbers are
            checked, but factual support is not yet automatically
            verified.
          </small>
        </p>

        <section
          aria-label="Essay generator"
          style={{
            margin: "24px 0",
            padding: "18px",
            border: "1px solid #dce2eb",
            borderRadius: "10px",
            background: "#fafbfe",
          }}
        >
          <h2>Ship 30 for 30 Essay</h2>

          <p>
            Generate a transcript-grounded Markdown essay with
            citations.
          </p>

          <form onSubmit={generateEssay}>
            <label htmlFor="essay-topic">
              Essay topic
            </label>

            <input
              id="essay-topic"
              type="text"
              value={essayTopic}
              onChange={(event) =>
                setEssayTopic(event.target.value)
              }
              placeholder="How activation improves customer retention"
              maxLength={500}
              required
              disabled={
                isGeneratingEssay ||
                isSending
              }
              style={{
                display: "block",
                width: "100%",
                boxSizing: "border-box",
                margin: "10px 0",
                padding: "11px",
                font: "inherit",
              }}
            />

            <button
              type="submit"
              disabled={
                isGeneratingEssay ||
                isSending ||
                !essayTopic.trim()
              }
              style={{
                padding: "11px 18px",
                cursor: isGeneratingEssay
                  ? "not-allowed"
                  : "pointer",
              }}
            >
              {isGeneratingEssay
                ? "Generating essay..."
                : "Generate Essay"}
            </button>
          </form>

          {isGeneratingEssay && (
            <p role="status">
              Generating a grounded long-form essay. This may
              take several minutes with the local model.
            </p>
          )}
        </section>

        {artifact && (
          <section
            aria-label="Artifact viewer"
            style={{
              margin: "24px 0",
              padding: "24px",
              border: "1px solid #b7c9ee",
              borderRadius: "12px",
              background: "#ffffff",
              boxShadow:
                "0 4px 16px rgba(0, 0, 0, 0.08)",
            }}
          >
            <div
              style={{
                marginBottom: "20px",
                paddingBottom: "12px",
                borderBottom: "1px solid #dce2eb",
              }}
            >
              <h2>{artifact.title}</h2>

              <small>
                Artifact type: {artifact.artifact_type}
                {" · "}
                Provider: {artifact.provider}
                {" · "}
                Model: {artifact.model}
              </small>
            </div>

            <div
              style={{
                lineHeight: 1.75,
                overflowWrap: "anywhere",
              }}
            >
              <ReactMarkdown>
                {artifact.content}
              </ReactMarkdown>
            </div>

            <SourceList sources={artifact.sources} />
          </section>
        )}

        <section
          aria-label="Conversation"
          style={{ margin: "28px 0" }}
        >
          <h2>Conversation</h2>

          {messages.length === 0 && (
            <p>
              Start a new conversation by asking a question.
            </p>
          )}

          {messages.map((item, index) => (
            <ChatMessage
              key={`${item.id || "message"}-${index}`}
              message={item}
            />
          ))}
        </section>

        <form onSubmit={handleSubmit}>
          <label htmlFor="question">
            Your question
          </label>

          <textarea
            id="question"
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder="How can activation help customer retention?"
            rows={4}
            maxLength={4000}
            required
            disabled={
              isSending ||
              isGeneratingEssay
            }
            style={{
              display: "block",
              width: "100%",
              margin: "12px 0",
              padding: "12px",
              font: "inherit",
              boxSizing: "border-box",
            }}
          />

          <button
            type="submit"
            disabled={
              isSending ||
              isGeneratingEssay ||
              !message.trim()
            }
            style={{
              padding: "11px 18px",
              cursor: isSending
                ? "not-allowed"
                : "pointer",
            }}
          >
            {isSending
              ? "Generating..."
              : "Send question"}
          </button>
        </form>

        <p role="status">
          {isSending
            ? "Searching transcripts and generating an answer..."
            : ""}
        </p>

        {error && (
          <p
            role="alert"
            style={{
              color: "#b42318",
              padding: "12px",
              border: "1px solid #f4b4ae",
              borderRadius: "7px",
              background: "#fff4f2",
            }}
          >
            {error}
          </p>
        )}
      </main>
    </div>
  );
}


export default App;