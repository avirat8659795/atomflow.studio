import os
import re
import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

app = FastAPI(
    title="ATOM-FLOW Engine",
    description="Context-Aware Multi-Modal Workspace with Live Slides Engine",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None

class ChatRequest(BaseModel):
    message: str
    file_data: Optional[str] = None  # Base64 encoded string
    file_mime: Optional[str] = None  # e.g., image/jpeg, image/png, application/pdf

# Holds active thread content pieces safely
USER_SESSION_CONTEXT = []

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATOM-FLOW AI Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        .theme-dark::-webkit-scrollbar-thumb { background: #1f293d; border-radius: 9999px; }
        .theme-light::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 9999px; }
        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .prose th, .prose td { border: 1px solid #334155; padding: 0.5rem; text-align: left; }
        .prose th { background-color: #0f172a; }
    </style>
</head>
<body id="appBody" class="theme-dark bg-[#0b0f19] text-[#e2e8f0] font-sans antialiased h-screen flex overflow-hidden transition-colors duration-300">

    <aside id="sidebar" class="fixed inset-y-0 left-0 z-30 w-[260px] bg-[#070a10] border-r border-[#1e293b]/40 flex flex-col justify-between transition-transform duration-300 transform md:relative md:translate-x-0 -translate-x-full shrink-0">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            <button onclick="clearChatLog()" class="flex items-center justify-between w-full px-4 py-2.5 text-sm font-semibold rounded-xl bg-[#0f172a] border-2 border-[#10b981] text-white shadow-[0_0_15px_rgba(16,185,129,0.15)] mb-6 hover:bg-[#10b981]/10 transition-all">
                <div class="flex items-center gap-2.5"><span class="text-base text-[#10b981]">⚛️</span> New chat</div>
                <span class="text-xs text-[#64748b]">Reset</span>
            </button>

            <div class="space-y-1">
                <p class="px-3 text-xs font-bold text-[#475569] uppercase tracking-wider mb-2.5">Core Chat Logs</p>
                <div id="historyLogs" class="space-y-1"></div>
            </div>
        </div>

        <div class="p-4 border-t border-[#1e293b]/30 flex flex-col gap-3 bg-[#05070b]">
            <div>
                <span class="text-xs font-semibold text-[#475569] uppercase tracking-wider block mb-2 px-1">Console Settings</span>
                <button onclick="toggleThemeConfig()" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg bg-[#0f172a] border border-[#1e293b]/50 text-slate-300 hover:text-white transition-all">
                    <span>Theme Mode</span>
                    <span id="themeBtnLabel" class="text-[#10b981] font-bold">🌙 Dark</span>
                </button>
            </div>
            <div class="flex items-center gap-3 p-2 rounded-xl bg-[#0f172a]/40 border border-[#1e293b]/20">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center shadow-md shrink-0"><span class="text-xs">⚛️</span></div>
                <div class="flex flex-col truncate">
                    <span class="text-sm font-bold text-white tracking-wide">ATOM-FLOW</span>
                    <span class="text-[10px] text-[#10b981] font-mono tracking-widest uppercase">Multi-Modal Core</span>
                </div>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleMobileSidebar()" class="fixed inset-0 bg-black/50 z-20 hidden md:hidden"></div>

    <main class="flex-1 flex flex-col h-full relative overflow-hidden">
        <header id="mainHeader" class="h-14 flex items-center px-4 justify-between border-b border-[#1e293b]/30 z-10 bg-[#0b0f19]/80 backdrop-blur-md transition-colors">
            <button onclick="toggleMobileSidebar()" class="p-2 text-[#64748b] hover:text-white rounded-lg hover:bg-[#1e293b]/40 transition-colors focus:outline-none">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
            </button>
            <div class="text-sm font-medium text-[#94a3b8]">Engine: <span id="modelLabel" class="text-white font-bold tracking-wide">ATOM-CORE (Multimodal)</span></div>
            <div class="w-9"></div>
        </header>

        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-3xl w-full mx-auto flex flex-col z-10">
            <div class="flex gap-4 items-start text-base">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                    <p class="font-bold text-white text-sm tracking-wide">ATOM-FLOW Core</p>
                    <p class="text-[#cbd5e1] text-[15px]">Multi-modal engine online. Upload diagrams, use quick action chips, or say **"Create a presentation on [topic]"** to unlock the live presentation player.</p>
                </div>
            </div>
        </div>

        <footer class="p-4 bg-gradient-to-t from-[#0b0f19] via-[#0b0f19] to-transparent z-10" id="mainFooter">
            <div class="max-w-3xl w-full mx-auto relative flex flex-col items-center">
                
                <div class="flex flex-wrap gap-2 mb-3 justify-start w-full px-1">
                    <button onclick="applyQuickAction('Explain this concept simply with examples: ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#1e293b]/60 text-[#94a3b8] hover:text-white hover:border-[#10b981] transition-all">📝 Simplify Concept</button>
                    <button onclick="applyQuickAction('Give me a 3-question conceptual quiz on this topic: ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#1e293b]/60 text-[#94a3b8] hover:text-white hover:border-[#10b981] transition-all">🧪 Quiz Me</button>
                    <button onclick="applyQuickAction('Create a professional presentation on ')" class="px-3 py-1.5 text-xs font-medium rounded-full bg-[#0f172a] border border-[#10b981]/80 text-[#10b981] hover:bg-[#10b981]/10 transition-all">📊 Create Presentation</button>
                </div>

                <div id="filePreviewBar" class="hidden w-full bg-[#0f172a] border-x border-t border-[#1e293b]/60 px-4 py-2 rounded-t-2xl flex items-center justify-between text-xs text-slate-300">
                    <div class="flex items-center gap-2 truncate">
                        <span class="text-[#10b981]">📎</span>
                        <span id="fileNameDisplay" class="truncate font-mono">file.jpg</span>
                    </div>
                    <button onclick="removeAttachedFile()" class="text-rose-400 hover:text-rose-300 font-bold px-1">Remove</button>
                </div>

                <div id="inputContainer" class="w-full relative flex items-center bg-[#0f172a] rounded-2xl border border-[#1e293b]/60 group transition-all">
                    <input type="file" id="filePayloadInput" class="hidden" onchange="handleFilePayloadSelection(event)" accept="image/*,application/pdf">
                    
                    <button onclick="document.getElementById('filePayloadInput').click()" class="absolute left-3 p-2 text-[#475569] hover:text-[#10b981] transition-colors" title="Upload Image or Document">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" /></svg>
                    </button>

                    <textarea id="messageInput" rows="1" placeholder="Message Atom-Flow Matrix..." class="w-full bg-transparent text-white placeholder-[#475569] pl-12 pr-14 py-4 resize-none focus:outline-none text-[15px] max-h-40 overflow-y-auto leading-relaxed" oninput="autoGrow(this)" onkeydown="handleKeyDown(event)"></textarea>
                    
                    <button onclick="commitMessageToSend()" class="absolute right-3.5 p-2 bg-[#070a10] border border-[#1e293b]/40 hover:bg-white text-white hover:text-black rounded-xl transition-all duration-200">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
            </div>
        </footer>
    </main>

    <div id="presentationModal" class="fixed inset-0 bg-black/80 z-50 hidden flex items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-[#0f172a] border border-[#1e293b] rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div class="px-6 py-4 border-b border-[#1e293b] flex items-center justify-between bg-[#070a10]">
                <div class="flex items-center gap-2">
                    <span class="text-[#10b981] text-lg">📊</span>
                    <h3 class="font-bold text-white tracking-wide">ATOM-FLOW Interactive Presentation Engine</h3>
                </div>
                <div class="flex items-center gap-3">
                    <button onclick="downloadPresentationFile()" class="px-4 py-1.5 text-xs font-bold bg-[#10b981] text-black rounded-lg hover:bg-[#0d9668] transition-all flex items-center gap-1.5">
                        📥 Download Slide Deck
                    </button>
                    <button onclick="closePresentationWorkspace()" class="text-slate-400 hover:text-white font-bold text-sm bg-slate-800/60 px-3 py-1.5 rounded-lg">Close</button>
                </div>
            </div>
            <div class="flex-1 bg-black relative">
                <iframe id="presentationFrame" class="w-full h-full border-none"></iframe>
            </div>
        </div>
    </div>

    <script>
        let isDarkMode = true;
        let attachedFileB64 = null;
        let attachedFileMime = null;
        let currentPresentationHtml = "";

        marked.setOptions({ gfm: true, breaks: true });

        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.toggle('-translate-x-full');
            overlay.classList.toggle('hidden');
        }

        function toggleThemeConfig() {
            isDarkMode = !isDarkMode;
            const body = document.getElementById('appBody');
            const themeBtnLabel = document.getElementById('themeBtnLabel');
            if (!isDarkMode) {
                body.classList.replace('theme-dark', 'theme-light');
                body.classList.replace('bg-[#0b0f19]', 'bg-[#f8fafc]');
                body.classList.replace('text-[#e2e8f0]', 'text-[#334155]');
                themeBtnLabel.innerHTML = "☀️ Light";
            } else {
                body.classList.replace('theme-light', 'theme-dark');
                body.classList.replace('bg-[#f8fafc]', 'bg-[#0b0f19]');
                body.classList.replace('text-[#334155]', 'text-[#e2e8f0]');
                themeBtnLabel.innerHTML = "🌙 Dark";
            }
        }

        function handleFilePayloadSelection(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                attachedFileB64 = e.target.result.split(',')[1];
                attachedFileMime = file.type;
                
                document.getElementById('fileNameDisplay').innerText = `${file.name} (${Math.round(file.size/1024)} KB)`;
                document.getElementById('filePreviewBar').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        function removeAttachedFile() {
            attachedFileB64 = null;
            attachedFileMime = null;
            document.getElementById('filePayloadInput').value = "";
            document.getElementById('filePreviewBar').classList.add('hidden');
        }

        function applyQuickAction(prefixText) {
            const input = document.getElementById('messageInput');
            input.value = prefixText;
            input.focus();
            autoGrow(input);
        }

        function clearChatLog() {
            fetch('/clear', { method: 'POST' }).then(() => {
                document.getElementById('chatFeed').innerHTML = '';
                document.getElementById('historyLogs').innerHTML = '';
            });
        }

        function autoGrow(element) {
            element.style.height = "auto";
            element.style.height = (element.scrollHeight) + "px";
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                commitMessageToSend();
            }
        }

        function appendMessageRow(text, isUser) {
            const feed = document.getElementById('chatFeed');
            let contentHtml = isUser ? text : marked.parse(text);
            let row = '';

            if(isUser) {
                row = `<div class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto">
                        <div class="${isDarkMode ? 'bg-[#1e293b]/60 text-white' : 'bg-slate-200 text-slate-800'} rounded-2xl px-4 py-3 shadow-md">${contentHtml}</div>
                       </div>`;
            } else {
                row = `<div class="flex gap-4 items-start text-base">
                        <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                        <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                            <p class="font-bold ${isDarkMode ? 'text-white' : 'text-slate-800'} text-sm">ATOM-FLOW Core</p>
                            <div class="prose ${isDarkMode ? 'text-[#cbd5e1]' : 'text-slate-600'} text-[15px]">${contentHtml}</div>
                        </div>
                       </div>`;
            }
            feed.insertAdjacentHTML('beforeend', row);
            feed.scrollTop = feed.scrollHeight;
        }

        function openPresentationWorkspace(rawSlideCode) {
            currentPresentationHtml = rawSlideCode;
            const modal = document.getElementById('presentationModal');
            const iframe = document.getElementById('presentationFrame');
            
            modal.classList.remove('hidden');
            iframe.srcdoc = rawSlideCode;
        }

        function closePresentationWorkspace() {
            document.getElementById('presentationModal').classList.add('hidden');
            document.getElementById('presentationFrame').srcdoc = "";
        }

        function downloadPresentationFile() {
            if (!currentPresentationHtml) return;
            const blob = new Blob([currentPresentationHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ATOM-FLOW-Presentation.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText && !attachedFileB64) return;

            let displayPrompt = messageText;
            if(attachedFileB64) {
                displayPrompt = `📸 [Attached File] ${messageText}`;
            }

            appendMessageRow(displayPrompt, true);
            input.value = '';
            input.style.height = 'auto';

            const payload = {
                message: messageText,
                file_data: attachedFileB64,
                file_mime: attachedFileMime
            };

            removeAttachedFile();

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                appendMessageRow(data.reply, false);
                if (data.presentation_html) {
                    openPresentationWorkspace(data.presentation_html);
                }
            })
            .catch(() => {
                appendMessageRow("System tracking exception failure channel link down.", false);
            });
        }
    </script>
</body>
</html>
"""

def extract_presentation_template(slide_content_markdown: str) -> str:
    """Wraps generated structural markdown cleanly inside an isolated single-file Reveal.js workspace framework."""
    raw_slides = slide_content_markdown.split("---")
    slide_sections = ""
    for slide in raw_slides:
        if slide.strip():
            # Strips metadata tags if model leaves them around raw text fields
            clean_slide = re.sub(r'```markdown|```', '', slide).strip()
            slide_sections += f"<section data-markdown><script type='text/template'>\n{clean_slide}\n</script></section>\n"

    template = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>ATOM-FLOW Engine Presentation</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/black.css">
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                {slide_sections}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/plugin/markdown/markdown.js"></script>
        <script>
            Reveal.initialize({{
                plugins: [ RevealMarkdown ],
                controls: true,
                progress: true,
                center: true,
                hash: true
            }});
        </script>
    </body>
    </html>
    """
    return template

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global USER_SESSION_CONTEXT
    user_prompt = request.message.strip()
    
    if not ai_client:
        return {"reply": "API Key initialization missing tracking configuration vectors."}

    content_parts = []
    
    if request.file_data and request.file_mime:
        try:
            raw_bytes = base64.b64decode(request.file_data)
            content_parts.append(
                types.Part.from_bytes(data=raw_bytes, mime_type=request.file_mime)
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail="Mime payload sequence corruption.")

    url_pattern = re.compile(r'https?://[^\s]+')
    found_urls = url_pattern.findall(user_prompt)
    if found_urls:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            res = requests.get(found_urls[0], headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style"]): tag.decompose()
            scraped_text = " ".join(soup.get_text().split())[:3000]
            user_prompt = f"Scraped Data:\n\"\"\"\n{scraped_text}\n\"\"\"\n\nUser Message: {user_prompt}"
        except:
            pass

    content_parts.append(types.Part.from_text(text=user_prompt))

    is_presentation_request = any(keyword in user_prompt.lower() for keyword in ["presentation", "slide deck", "create a presentation", "slides"])

    system_instruction = (
        "You are ATOM-FLOW, a professional workspace engineer. "
        "Always render detailed, helpful responses using clear Markdown. "
        "CRITICAL: If the user requests a presentation or slide deck, provide a beautiful outline in markdown inside your regular chat text, "
        "but also ensure each slide block is clearly divided with a '---' separator line so the sub-engine can render it."
    )

    # Append current input pieces directly to current thread log stack
    USER_SESSION_CONTEXT.append(types.Content(role="user", parts=content_parts))

    try:
        # Fixed tracking logic loop to prevent system rule resets across cycles
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=USER_SESSION_CONTEXT,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        response_text = response.text

        # Track model feedback state
        USER_SESSION_CONTEXT.append(types.Content(role="model", parts=[types.Part.from_text(text=response_text)]))

        return_data = {"reply": response_text}

        if is_presentation_request:
            presentation_html = extract_presentation_template(response_text)
            return_data["presentation_html"] = presentation_html

        return return_data

    except Exception as e:
        # Gracefully handle validation drops by popping invalid content segments out
        if USER_SESSION_CONTEXT:
            USER_SESSION_CONTEXT.pop()
        return {"reply": f"Handshake Error Matrix: {str(e)}"}

@app.post("/clear")
async def clear_context():
    global USER_SESSION_CONTEXT
    USER_SESSION_CONTEXT.clear()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)