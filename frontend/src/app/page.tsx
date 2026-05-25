"use client";

import React, { useState, useEffect, useRef } from "react";
import gsap from "gsap";
import { 
  UploadCloud, 
  User, 
  Briefcase, 
  Settings, 
  Send, 
  CheckCircle, 
  Download, 
  FileText, 
  MessageSquare, 
  Award, 
  TrendingUp, 
  AlertTriangle, 
  HelpCircle,
  RefreshCw
} from "lucide-react";

// Types mapping matching Pydantic schemas
interface ResumeProfile {
  candidate_name?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  github?: string;
  estimated_job_role: string;
  experience_level: string;
  skills: string[];
  work_experience_summaries: string[];
  education_summaries: string[];
  key_strengths: string[];
}

interface Message {
  role: "system" | "user" | "assistant";
  content: string;
}

interface AnswerEvaluation {
  question: string;
  answer: string;
  clarity_score: number;
  depth_score: number;
  relevance_score: number;
  confidence_score: number;
  missing_concepts: string[];
  improvement_tips: string[];
}

interface FeedbackReport {
  session_id: string;
  estimated_job_role: string;
  experience_level: string;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  summary_feedback: string;
  evaluations: AnswerEvaluation[];
}

export default function MockInterviewApp() {
  // App Router Steps States
  const [step, setStep] = useState<"upload" | "profile" | "room" | "feedback">("upload");
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Resume Ingestion details
  const [file, setFile] = useState<File | null>(null);
  const [resumeSessionId, setResumeSessionId] = useState("");
  const [resumeProfile, setResumeProfile] = useState<ResumeProfile | null>(null);

  // Custom configurations
  const [interviewMode, setInterviewMode] = useState<"HR" | "Technical" | "Behavioral">("Technical");
  const [difficultyLevel, setDifficultyLevel] = useState<string>("Auto-Detect");
  const [totalQuestions, setTotalQuestions] = useState(5);

  // Interview state details
  const [interviewSessionId, setInterviewSessionId] = useState("");
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(1);
  const [messages, setMessages] = useState<Message[]>([]);
  const [answerInput, setAnswerInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [interviewCompleted, setInterviewCompleted] = useState(false);

  // Evaluation details
  const [feedbackReport, setFeedbackReport] = useState<FeedbackReport | null>(null);

  // UI Refs for GSAP animations
  const uploadCardRef = useRef<HTMLDivElement>(null);
  const profileCardRef = useRef<HTMLDivElement>(null);
  const chatMessagesRef = useRef<HTMLDivElement>(null);
  const voiceCircleRef = useRef<HTMLDivElement>(null);

  // Apply entrance reveals on steps shift
  useEffect(() => {
    if (step === "upload" && uploadCardRef.current) {
      gsap.fromTo(
        uploadCardRef.current,
        { opacity: 0, y: 30, scale: 0.98 },
        { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power2.out" }
      );
    } else if (step === "profile" && profileCardRef.current) {
      gsap.fromTo(
        profileCardRef.current,
        { opacity: 0, scale: 0.96, y: 20 },
        { opacity: 1, scale: 1, y: 0, duration: 0.6, ease: "back.out(1.2)" }
      );
    }
  }, [step]);

  // Scroll chat window to bottom on new messages
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages]);

  // Trigger floating pulse voice pulse while streaming
  useEffect(() => {
    if (isStreaming && voiceCircleRef.current) {
      gsap.to(voiceCircleRef.current, {
        scale: 1.15,
        opacity: 0.8,
        repeat: -1,
        yoyo: true,
        duration: 0.8,
        ease: "power1.inOut"
      });
    } else if (voiceCircleRef.current) {
      gsap.killTweensOf(voiceCircleRef.current);
      gsap.to(voiceCircleRef.current, { scale: 1, opacity: 0.4, duration: 0.3 });
    }
  }, [isStreaming]);

  // Handle file drops
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const ext = droppedFile.name.split(".").pop()?.toLowerCase();
      if (ext === "pdf" || ext === "docx") {
        setFile(droppedFile);
        setError(null);
      } else {
        setError("Unsupported file format. Please upload a PDF or DOCX file.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  // Upload and Parse Resume (Phase 2)
  const uploadResume = async () => {
    if (!file) return;
    setLoading(true);
    setLoadingText("Groq Llama-3.3 is analyzing your resume...");
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/resume/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || "Failed to parse document.");
      }

      const data = await response.json();
      setResumeSessionId(data.session_id);
      setResumeProfile(data.profile);
      setStep("profile");
    } catch (e: any) {
      setError(e.message || "Failed to upload file. Make sure the FastAPI server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  // Start Interview Session (Phase 3)
  const startInterview = async () => {
    if (!resumeSessionId) return;
    setLoading(true);
    setLoadingText("AI Recruiter Alex is entering the room...");
    setError(null);

    const payload = {
      resume_session_id: resumeSessionId,
      interview_mode: interviewMode,
      difficulty_level: difficultyLevel === "Auto-Detect" ? null : difficultyLevel,
      total_questions: totalQuestions,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/interview/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json_stringify(payload),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || "Failed to initiate session.");
      }

      const data = await response.json();
      setInterviewSessionId(data.interview_session_id);
      setDifficultyLevel(data.difficulty_level); // Sync difficulty level if auto-detected
      setTotalQuestions(data.total_questions);
      setMessages([{ role: "assistant", content: data.first_question }]);
      setStep("room");
    } catch (e: any) {
      setError(e.message || "Failed to start interview.");
    } finally {
      setLoading(false);
    }
  };

  // Helper stringify
  const json_stringify = (obj: any) => {
    return JSON.stringify(obj);
  };

  // Submit Answer & Handle SSE Stream (Phase 3)
  const submitAnswer = async () => {
    if (!answerInput.trim() || isStreaming) return;
    setError(null);
    const candidateAnswer = answerInput.trim();
    setAnswerInput("");

    // 1. Append candidate's answer response to dialogues history
    const updatedMessages = [...messages, { role: "user" as const, content: candidateAnswer }];
    setMessages(updatedMessages);

    // 2. Set streaming placeholder
    const streamMessageIndex = updatedMessages.length;
    setMessages([...updatedMessages, { role: "assistant" as const, content: "" }]);
    setIsStreaming(true);

    const payload = {
      session_id: interviewSessionId,
      answer: candidateAnswer,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/interview/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json_stringify(payload),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || "Server error progressing turn.");
      }

      // Read ReadableStream chunks
      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      let accumulatedResponseText = "";

      if (!reader) {
        throw new Error("Failed to initialize SSE reader.");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkStr = decoder.decode(value, { stream: true });
        
        // Parse SSE data: prefix lines
        const lines = chunkStr.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const token = line.slice(6);
            
            // Check for potential stream failures
            if (token.startsWith("[STREAM_ERROR:")) {
              throw new Error(token);
            }
            
            accumulatedResponseText += token;

            // Stream state updater
            setMessages((prev) => {
              const copy = [...prev];
              if (copy[streamMessageIndex]) {
                copy[streamMessageIndex] = { role: "assistant", content: accumulatedResponseText };
              }
              return copy;
            });
          }
        }
      }

      // Check if interview concluded
      if (currentQuestionIndex >= totalQuestions) {
        setInterviewCompleted(true);
      } else {
        setCurrentQuestionIndex((prev) => prev + 1);
      }

    } catch (e: any) {
      setError(e.message || "An error occurred during communication.");
      // Rollback placeholder
      setMessages(updatedMessages);
    } finally {
      setIsStreaming(false);
    }
  };

  // Compile Grade & End Interview (Phase 4)
  const compileReport = async () => {
    setLoading(true);
    setLoadingText("Groq is generating your performance report card...");
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/interview/end", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json_stringify({ session_id: interviewSessionId }),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || "Failed to generate assessment report.");
      }

      const report = await response.json();
      setFeedbackReport(report);
      setStep("feedback");
    } catch (e: any) {
      setError(e.message || "Failed to compile report.");
    } finally {
      setLoading(false);
    }
  };

  // Restart Flow
  const restartFlow = () => {
    setStep("upload");
    setFile(null);
    setResumeSessionId("");
    setResumeProfile(null);
    setInterviewSessionId("");
    setCurrentQuestionIndex(1);
    setMessages([]);
    setAnswerInput("");
    setInterviewCompleted(false);
    setFeedbackReport(null);
    setError(null);
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden px-4 py-8 md:px-8 bg-[#0b0f19]">
      
      {/* Decorative ambient glowing backdrops (GSAP floating) */}
      <div className="cosmic-orb absolute -top-20 -left-20 w-96 h-96 rounded-full bg-cyan-900/10 pointer-events-none" />
      <div className="cosmic-orb absolute -bottom-40 -right-20 w-[450px] h-[450px] rounded-full bg-teal-900/10 pointer-events-none" />

      {/* Main Container */}
      <main className="mx-auto max-w-5xl">

        {/* Global Loading Spinner */}
        {loading && (
          <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-950/80 backdrop-blur-md">
            <RefreshCw className="w-12 h-12 text-[#005571] animate-spin mb-4" />
            <p className="text-gray-300 font-medium text-lg animate-pulse">{loadingText}</p>
          </div>
        )}

        {/* Error Notification Bar */}
        {error && (
          <div className="glass-panel border-red-500/30 bg-red-950/10 text-red-400 p-4 rounded-xl mb-6 flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Execution Warning:</span>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* STEP 1: RESUME DRAG-AND-DROP UPLOAD */}
        {step === "upload" && (
          <div ref={uploadCardRef} className="glass-panel p-8 md:p-12 rounded-3xl text-center max-w-2xl mx-auto shadow-2xl">
            <div className="flex justify-center mb-6">
              <div className="p-4 rounded-2xl bg-cyan-950/30 border border-cyan-500/20 text-[#005571]">
                <UploadCloud className="w-12 h-12" />
              </div>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
              Steps AI Mock Interview Room 🚀
            </h1>
            <p className="text-gray-400 text-sm md:text-base max-w-md mx-auto mb-8">
              Practice mock interviews under context-aware LLM recruiter models.
              Upload your PDF or Word resume to configure personalized syllabus loops.
            </p>

            {/* Ingestion Drag target */}
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-gray-700 hover:border-[#005571] rounded-2xl p-8 mb-8 cursor-pointer transition-colors duration-200 bg-gray-900/20"
            >
              <input
                type="file"
                id="file-selector"
                accept=".pdf,.docx"
                className="hidden"
                onChange={handleFileChange}
              />
              <label htmlFor="file-selector" className="cursor-pointer">
                <FileText className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                <span className="block text-gray-300 font-medium mb-1">
                  {file ? file.name : "Drag & Drop Resume here"}
                </span>
                <span className="text-xs text-gray-500 block">
                  Supports PDF or MS Word (.docx) formats
                </span>
              </label>
            </div>

            <button
              onClick={uploadResume}
              disabled={!file}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-white tracking-wide transition-all ${
                file
                  ? "bg-[#005571] hover:bg-[#004055] hover:shadow-lg cursor-pointer"
                  : "bg-gray-800 text-gray-500 cursor-not-allowed"
              }`}
            >
              Ingest & Profile Resume Details
            </button>
          </div>
        )}

        {/* STEP 2: PROFILE PROFILE SUMMARY & CONFIGURATION */}
        {step === "profile" && resumeProfile && (
          <div ref={profileCardRef} className="glass-panel p-8 rounded-3xl shadow-2xl">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-800">
              <User className="w-8 h-8 text-[#005571]" />
              <div>
                <h2 className="text-2xl font-bold text-white">Extracted Candidate Profile</h2>
                <p className="text-xs text-gray-400">Deterministic profiling derived via Groq JSON Mode</p>
              </div>
            </div>

            {/* Profile Grid Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              
              {/* Left Column: Basic profiles Info */}
              <div className="md:col-span-1 p-5 rounded-2xl bg-cyan-950/10 border border-cyan-500/10">
                <h3 className="font-semibold text-cyan-400 mb-4 text-sm tracking-wider uppercase">Contact Profiles</h3>
                <div className="space-y-3 text-sm text-gray-300">
                  <p><span className="text-gray-500 block text-xs">Full Name</span> {resumeProfile.candidate_name || "Applicant"}</p>
                  <p><span className="text-gray-500 block text-xs">Email Address</span> {resumeProfile.email || "N/A"}</p>
                  <p><span className="text-gray-500 block text-xs">Phone</span> {resumeProfile.phone || "N/A"}</p>
                </div>
              </div>

              {/* Right Column: Roles & Skills */}
              <div className="md:col-span-2 space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-gray-900/30 border border-gray-800">
                    <span className="text-xs text-gray-500 uppercase font-semibold">Job Role Tag</span>
                    <p className="text-white font-medium mt-1">{resumeProfile.estimated_job_role}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-gray-900/30 border border-gray-800">
                    <span className="text-xs text-gray-500 uppercase font-semibold">Experience Level</span>
                    <p className="text-white font-medium mt-1">{resumeProfile.experience_level}</p>
                  </div>
                </div>

                <div>
                  <span className="text-xs text-gray-500 uppercase font-semibold block mb-2">Technologies & Frameworks</span>
                  <div className="flex flex-wrap gap-2">
                    {resumeProfile.skills.map((skill, index) => (
                      <span key={index} className="px-3 py-1 rounded-full text-xs font-medium bg-gray-800 text-gray-300 border border-gray-700">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

            </div>

            {/* Dynamic syllabus mock setting configuration options */}
            <div className="p-6 rounded-2xl bg-gray-900/20 border border-gray-800/80 mb-8">
              <h3 className="flex items-center gap-2 font-bold text-white mb-4 text-sm uppercase tracking-wider">
                <Settings className="w-4 h-4 text-[#005571]" />
                Mock Room Configurations
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-2">INTERVIEW MODE</label>
                  <select
                    value={interviewMode}
                    onChange={(e) => setInterviewMode(e.target.value as any)}
                    className="w-full p-3 rounded-lg cosmic-input border border-gray-700 focus:border-[#005571] text-sm"
                  >
                    <option value="Technical">Technical (System Design & Code)</option>
                    <option value="HR">HR & Cultural Alignment</option>
                    <option value="Behavioral">Behavioral (STAR Method)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-2">DIFFICULTY LEVEL</label>
                  <select
                    value={difficultyLevel}
                    onChange={(e) => setDifficultyLevel(e.target.value)}
                    className="w-full p-3 rounded-lg cosmic-input border border-gray-700 focus:border-[#005571] text-sm"
                  >
                    <option value="Auto-Detect">Auto-Detect Seniority</option>
                    <option value="Junior">Junior Tier</option>
                    <option value="Mid">Mid-Level Tier</option>
                    <option value="Senior">Senior Tier</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs text-gray-400 font-semibold block mb-2">QUESTIONS LIMIT: {totalQuestions}</label>
                  <input
                    type="range"
                    min="3"
                    max="10"
                    value={totalQuestions}
                    onChange={(e) => setTotalQuestions(Number(e.target.value))}
                    className="w-full accent-[#005571] mt-3"
                  />
                  <span className="text-[10px] text-gray-500 block text-center mt-1">Syllabus consists of {totalQuestions} turns</span>
                </div>

              </div>
            </div>

            <button
              onClick={startInterview}
              className="w-full py-4 px-6 rounded-xl font-semibold bg-[#005571] hover:bg-[#004055] hover:shadow-lg transition-all tracking-wide text-white cursor-pointer"
            >
              Enter Mock Interview Room
            </button>
          </div>
        )}

        {/* STEP 3: MOCK INTERVIEW ROOM (SSE STREAM) */}
        {step === "room" && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            
            {/* Left Column: Recruiter Meta Panel */}
            <div className="md:col-span-1 glass-panel p-6 rounded-2xl flex flex-col items-center justify-between text-center min-h-[300px] md:min-h-0">
              
              <div className="space-y-4">
                <div className="relative flex justify-center mt-4">
                  {/* Glowing Pulse visuals */}
                  <div ref={voiceCircleRef} className="absolute inset-0 w-24 h-24 rounded-full bg-cyan-900/40 pointer-events-none scale-105 blur-sm opacity-40 pulse-visualizer" />
                  <div className="w-24 h-24 rounded-full bg-gray-900 border-2 border-[#005571] flex items-center justify-center text-white font-extrabold text-3xl shadow-xl relative z-10">
                    Alex
                  </div>
                </div>

                <div>
                  <h3 className="font-bold text-white text-lg">AI Recruiter Alex</h3>
                  <span className="text-xs text-cyan-400 font-semibold">{interviewMode} Recruiter</span>
                </div>
              </div>

              <div className="w-full space-y-4 my-6">
                <div>
                  <span className="text-[10px] text-gray-500 font-bold block uppercase mb-1">INTERVIEW TIERS</span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-800 text-gray-200 uppercase">
                    {difficultyLevel}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-gray-500 font-bold block uppercase mb-1">PROGRESS SYLLABUS</span>
                  <div className="text-sm font-semibold text-white">
                    Question {currentQuestionIndex} of {totalQuestions}
                  </div>
                  <div className="w-full bg-gray-800 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div 
                      className="bg-[#005571] h-1.5 transition-all duration-300"
                      style={{ width: `${(currentQuestionIndex / totalQuestions) * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <button
                onClick={restartFlow}
                className="text-xs text-gray-500 hover:text-red-400 underline cursor-pointer"
              >
                Quit Assessment Session
              </button>

            </div>

            {/* Right Column: Conversational History */}
            <div className="md:col-span-3 flex flex-col h-[550px] glass-panel rounded-2xl overflow-hidden">
              
              {/* Chat Message Lists */}
              <div 
                ref={chatMessagesRef}
                className="flex-1 p-6 overflow-y-auto space-y-4 scroll-smooth"
              >
                {messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div 
                      className={`max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-[#005571] text-white rounded-tr-none shadow-md"
                          : "bg-gray-900/60 border border-gray-800 text-gray-200 rounded-tl-none"
                      }`}
                    >
                      <span className="block text-[9px] uppercase tracking-wider text-cyan-400 font-bold mb-1">
                        {msg.role === "user" ? "Candidate" : "Recruiter Alex"}
                      </span>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}

                {/* Conclude Action button once completed */}
                {interviewCompleted && (
                  <div className="flex justify-center pt-6">
                    <button
                      onClick={compileReport}
                      className="py-4 px-8 rounded-xl font-bold bg-cyan-900 border border-cyan-500 text-cyan-200 hover:bg-cyan-950 hover:shadow-cyan-900/50 hover:shadow-lg transition-all text-sm tracking-wider uppercase animate-bounce cursor-pointer"
                    >
                      Compile Grade & Get Performance Report Card
                    </button>
                  </div>
                )}
              </div>

              {/* Chat Textbox Input Field */}
              {!interviewCompleted && (
                <div className="p-4 border-t border-gray-800 bg-gray-950/40 flex items-center gap-3">
                  <textarea
                    rows={2}
                    value={answerInput}
                    onChange={(e) => setAnswerInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        submitAnswer();
                      }
                    }}
                    placeholder={isStreaming ? "Recruiter Alex is replying..." : "Type your response here... (Press Enter to send)"}
                    disabled={isStreaming}
                    className="flex-1 p-3 rounded-xl bg-gray-900/60 border border-gray-800 outline-none text-sm text-gray-200 placeholder-gray-500 focus:border-[#005571] resize-none"
                  />
                  <button
                    onClick={submitAnswer}
                    disabled={isStreaming || !answerInput.trim()}
                    className={`p-4 rounded-xl text-white transition-all ${
                      answerInput.trim() && !isStreaming
                        ? "bg-[#005571] hover:bg-[#004055] cursor-pointer"
                        : "bg-gray-800 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              )}

            </div>

          </div>
        )}

        {/* STEP 4: PERFORMANCE FEEDBACK SCORECARD REPORT */}
        {step === "feedback" && feedbackReport && (
          <div className="space-y-8 pb-12">
            
            {/* Executive summary banner card */}
            <div className="glass-panel p-8 rounded-3xl shadow-2xl relative overflow-hidden">
              
              <div className="absolute top-0 right-0 p-8 opacity-5">
                <Award className="w-40 h-40" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 items-center">
                
                {/* Huge Grade circular panel */}
                <div className="md:col-span-1 flex flex-col items-center">
                  <div className="w-36 h-36 rounded-full border-4 border-cyan-500/20 flex flex-col items-center justify-center bg-cyan-950/20 shadow-xl shadow-cyan-950/10">
                    <span className="text-3xl font-extrabold text-white">{feedbackReport.overall_score}%</span>
                    <span className="text-[10px] text-gray-500 font-bold uppercase mt-1">Consolidated Grade</span>
                  </div>
                </div>

                {/* Feedback metadata summaries */}
                <div className="md:col-span-3 space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-800 text-cyan-400">
                      {feedbackReport.estimated_job_role}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-800 text-gray-300">
                      {feedbackReport.experience_level} Tier
                    </span>
                  </div>

                  <h2 className="text-2xl font-bold text-white">Assessment Complete. Exceptional Job!</h2>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {feedbackReport.summary_feedback}
                  </p>
                  
                  {/* PDF report download floating button */}
                  <div className="pt-2">
                    <a
                      href={`http://127.0.0.1:8000/api/v1/report/${feedbackReport.session_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 py-3 px-6 rounded-xl font-semibold bg-[#005571] hover:bg-[#004055] text-white text-sm shadow-md transition-all cursor-pointer"
                    >
                      <Download className="w-4 h-4" />
                      Download Assessment Report PDF
                    </a>
                  </div>
                </div>

              </div>

            </div>

            {/* Split Strengths & Weakness Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Strengths Card */}
              <div className="glass-panel p-6 rounded-2xl border-green-500/20">
                <h3 className="flex items-center gap-2 font-bold text-green-400 mb-4 text-sm uppercase tracking-wider">
                  <TrendingUp className="w-4 h-4" />
                  Key Strengths
                </h3>
                <ul className="space-y-3">
                  {feedbackReport.strengths.map((str_item, index) => (
                    <li key={index} className="text-sm text-gray-300 flex items-start gap-2 bg-green-950/10 p-3 rounded-lg border border-green-950/20">
                      <span className="text-green-500 text-lg leading-none mt-0.5">•</span>
                      <span>{str_item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Weaknesses Card */}
              <div className="glass-panel p-6 rounded-2xl border-red-500/20">
                <h3 className="flex items-center gap-2 font-bold text-red-400 mb-4 text-sm uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4" />
                  Areas for Development
                </h3>
                <ul className="space-y-3">
                  {feedbackReport.weaknesses.map((weak_item, index) => (
                    <li key={index} className="text-sm text-gray-300 flex items-start gap-2 bg-red-950/10 p-3 rounded-lg border border-red-950/20">
                      <span className="text-red-500 text-lg leading-none mt-0.5">•</span>
                      <span>{weak_item}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>

            {/* Detailed Question breakdown panel list */}
            <div className="space-y-6">
              <h3 className="font-bold text-white text-lg tracking-wide">Question-by-Question Diagnostics</h3>
              
              {feedbackReport.evaluations.map((eval_item, idx) => (
                <div key={idx} className="glass-panel p-6 rounded-2xl bg-gray-900/10 hover:border-gray-800 transition-colors">
                  
                  {/* Header Question asked */}
                  <div className="mb-4">
                    <span className="text-[10px] text-cyan-400 font-bold block uppercase mb-1">Recruiter Question {idx}</span>
                    <p className="text-white font-semibold text-sm md:text-base leading-relaxed">
                      {eval_item.question}
                    </p>
                  </div>

                  {/* Candidate Answer response */}
                  <div className="mb-6 p-4 rounded-xl bg-gray-950/40 border border-gray-900 text-gray-400 text-sm italic leading-relaxed">
                    <span className="text-[9px] text-gray-600 font-bold block uppercase mb-1 not-italic">Your Response</span>
                    "{eval_item.answer}"
                  </div>

                  {/* Diagnostic scores grid metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="p-3 rounded-xl bg-gray-900/30 border border-gray-800/80">
                      <span className="text-[10px] text-gray-500 block">Communication Clarity</span>
                      <div className="text-white font-bold text-lg mt-1">{eval_item.clarity_score}/10</div>
                    </div>
                    <div className="p-3 rounded-xl bg-gray-900/30 border border-gray-800/80">
                      <span className="text-[10px] text-gray-500 block">Technical Depth</span>
                      <div className="text-white font-bold text-lg mt-1">{eval_item.depth_score}/10</div>
                    </div>
                    <div className="p-3 rounded-xl bg-gray-900/30 border border-gray-800/80">
                      <span className="text-[10px] text-gray-500 block">Contextual Relevance</span>
                      <div className="text-white font-bold text-lg mt-1">{eval_item.relevance_score}/10</div>
                    </div>
                    <div className="p-3 rounded-xl bg-gray-900/30 border border-gray-800/80">
                      <span className="text-[10px] text-gray-500 block">Confidence Tone</span>
                      <div className="text-white font-bold text-lg mt-1">{eval_item.confidence_score}/10</div>
                    </div>
                  </div>

                  {/* Gaps and Tips block split */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-900">
                    
                    <div>
                      <span className="text-[10px] text-red-400 font-bold block uppercase mb-2">Omitted Core Keywords</span>
                      {eval_item.missing_concepts.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {eval_item.missing_concepts.map((concept, c_idx) => (
                            <span key={c_idx} className="px-2.5 py-1 rounded bg-red-950/10 text-red-400 text-xs border border-red-950/20 font-medium">
                              {concept}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-500 italic">None detected. Keywords usage was complete.</span>
                      )}
                    </div>

                    <div>
                      <span className="text-[10px] text-green-400 font-bold block uppercase mb-2">Diagnostic Coaching Tips</span>
                      <ul className="space-y-1 text-xs text-gray-300 list-disc list-inside">
                        {eval_item.improvement_tips.map((tip, t_idx) => (
                          <li key={t_idx}>{tip}</li>
                        ))}
                      </ul>
                    </div>

                  </div>

                </div>
              ))}
            </div>

            {/* Restart button */}
            <div className="flex justify-center">
              <button
                onClick={restartFlow}
                className="py-4 px-8 rounded-xl font-bold bg-cyan-900/10 border border-cyan-500/20 hover:border-cyan-500/40 text-cyan-400 transition-all text-sm tracking-wider uppercase cursor-pointer"
              >
                Restart Mock Assessment Practice
              </button>
            </div>

          </div>
        )}

      </main>

    </div>
  );
}
