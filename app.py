import os
import re
import base64
import asyncio
import random
import httpx  
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    file_data: Optional[str] = None  
    file_mime: Optional[str] = None  

USER_SESSION_CONTEXT = []

# --- EXTENSIVELY UPGRADED PREMIUM LIGHT/DARK MONOCHROME USER INTERFACE ---
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
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        
        /* Dark Theme Scrollbars */
        .theme-dark ::-webkit-scrollbar-thumb { background: #262626; border-radius: 9999px; }
        .theme-dark ::-webkit-scrollbar-thumb:hover { background: #404040; }
        
        /* Light Theme Scrollbars */
        .theme-light ::-webkit-scrollbar-thumb { background: #d4d4d4; border-radius: 9999px; }
        .theme-light ::-webkit-scrollbar-thumb:hover { background: #a3a3a3; }

        .prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .prose th, .prose td { border: 1px solid #404040; padding: 0.6rem; text-align: left; }
        .theme-light .prose th, .theme-light .prose td { border: 1px solid #e5e5e5; }
        .prose th { background-color: #171717; color: #ffffff; }
        .theme-light .prose th { background-color: #f5f5f5; color: #171717; }
        .prose ul { list-style-type: disc; padding-left: 1.5rem; margin: 0.5rem 0; }
        .prose ol { list-style-type: decimal; padding-left: 1.5rem; margin: 0.5rem 0; }
        
        /* Dynamic Theme Transitions */
        .theme-transition { transition: background-color 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s ease, color 0.2s ease; }
    </style>
</head>
<body id="appBody" class="theme-dark bg-[#0D0D0D] text-[#ECECEC] font-sans antialiased h-screen flex overflow-hidden theme-transition">

    <!-- Sidebar Layout -->
    <aside id="sidebar" class="fixed inset-y-0 left-0 z-30 w-[260px] bg-[#171717] border-r border-[#262626] flex flex-col justify-between transition-transform duration-300 ease-in-out transform md:relative md:translate-x-0 -translate-x-full shrink-0 theme-transition">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            <!-- New Chat / Close Mobile Menu Header Row -->
            <div class="flex items-center gap-2 w-full">
                <button onclick="clearChatLog()" class="flex items-center justify-between flex-1 px-3 py-2 text-sm font-medium rounded-lg text-neutral-200 dark:text-neutral-800 hover:bg-[#212121] dark:hover:bg-neutral-200 border border-[#262626] dark:border-neutral-300 transition-all group bg-transparent">
                    <div class="flex items-center gap-2.5">
                        <svg class="w-4 h-4 text-neutral-200 dark:text-neutral-800 fill-none stroke-current" viewBox="0 0 100 100" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M15 85 L50 15 L70 55" />
                            <path d="M50 15 L85 15" />
                            <path d="M30 60 L60 60" />
                            <path d="M52 45 C65 45, 65 60, 80 60" />
                        </svg>
                        <span>New chat</span>
                    </div>
                    <span class="text-xs text-neutral-500 opacity-0 group-hover:opacity-100 transition-opacity">Reset</span>
                </button>
                
                <!-- Explicit Close Button on Mobile Sidebar View -->
                <button onclick="toggleMobileSidebar()" class="md:hidden p-2 rounded-lg border border-[#262626] dark:border-neutral-300 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black hover:bg-[#212121] dark:hover:bg-neutral-200 transition-all" aria-label="Close Sidebar">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                </button>
            </div>

            <div class="mt-6 space-y-1">
                <p class="px-3 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider mb-2">History</p>
                <div id="historyLogs" class="space-y-1"></div>
            </div>
        </div>
        
        <!-- Bottom Controls Dashboard -->
        <div class="p-3 border-t border-[#262626] dark:border-neutral-200 flex flex-col gap-2 bg-[#171717] dark:bg-[#F9F9F9] theme-transition">
            <button onclick="toggleThemeConfig()" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black hover:bg-[#212121] dark:hover:bg-neutral-200 border border-[#262626] dark:border-neutral-300 transition-all bg-transparent">
                <span>Interface Theme</span>
                <span id="themeBtnLabel" class="px-2 py-0.5 rounded text-[10px] bg-[#262626] dark:bg-neutral-200 text-white dark:text-neutral-900 font-mono font-bold uppercase tracking-wider transition-colors">Dark</span>
            </button>
            
            <!-- Branding Panel -->
            <div class="flex items-center gap-3 p-2 rounded-lg bg-[#212121]/50 dark:bg-neutral-200/60 border border-[#262626] dark:border-neutral-300 theme-transition">
                <div class="w-8 h-8 rounded-md bg-white dark:bg-black flex items-center justify-center shrink-0 transition-colors">
                    <svg class="w-5 h-5 text-black dark:text-white fill-none stroke-current" viewBox="0 0 100 100" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M15 85 L50 15 L70 55" />
                        <path d="M50 15 L85 15" />
                        <path d="M30 60 L60 60" />
                        <path d="M52 45 C65 45, 65 60, 80 60" />
                    </svg>
                </div>
                <div class="flex flex-col truncate">
                    <span class="text-xs font-bold text-white dark:text-neutral-900 tracking-wider uppercase">ATOM-FLOW</span>
                    <span class="text-[9px] text-neutral-400 dark:text-neutral-500 font-mono tracking-widest uppercase">AI Core v3</span>
                </div>
            </div>
        </div>
    </aside>

    <!-- Sidebar overlay for closing clickout triggers -->
    <div id="sidebarOverlay" onclick="toggleMobileSidebar()" class="fixed inset-0 bg-black/60 z-20 hidden backdrop-blur-xs transition-opacity duration-300"></div>

    <!-- Main Workspace Frame -->
    <main class="flex-1 flex flex-col h-full relative overflow-hidden bg-[#212121]/10 dark:bg-[#F4F4F4]/40 theme-transition">
        
        <!-- Workspace Header Platform -->
        <header id="mainHeader" class="h-14 flex items-center px-4 justify-between border-b border-[#262626] dark:border-neutral-200 z-10 bg-[#0D0D0D]/90 dark:bg-white/90 backdrop-blur-md theme-transition">
            <button onclick="toggleMobileSidebar()" class="p-2 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black rounded-lg hover:bg-[#212121] dark:hover:bg-neutral-200 transition-colors focus:outline-none md:hidden">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" /></svg>
            </button>
            <div id="hubIndicator" class="text-xs font-semibold tracking-wider text-neutral-400 dark:text-neutral-500 uppercase">System Hub</div>
            <div class="w-9"></div>
        </header>

        <!-- Main Workspace Flow Stream Feed container -->
        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-8 space-y-8 max-w-2xl w-full mx-auto flex flex-col z-10 scroll-smooth">
            <!-- Welcome Core Prompt Card -->
            <div class="flex gap-4 items-start text-base">
                <div id="systemAvatar" class="w-8 h-8 rounded-md bg-white dark:bg-neutral-900 text-black dark:text-white border dark:border-neutral-800 flex items-center justify-center shrink-0 shadow-md">
                    <svg class="w-5 h-5 fill-none stroke-current" viewBox="0 0 100 100" stroke-width="10" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M15 85 L50 15 L70 55" />
                        <path d="M50 15 L85 15" />
                        <path d="M30 60 L60 60" />
                        <path d="M52 45 C65 45, 65 60, 80 60" />
                    </svg>
                </div>
                <div class="space-y-2 flex-1 pt-0.5">
                    <p id="systemLabelText" class="font-bold text-neutral-200 dark:text-neutral-800 text-sm tracking-wide uppercase">ATOM-FLOW Core</p>
                    <p id="systemGreetingText" class="text-neutral-400 dark:text-neutral-600 text-[15px] leading-relaxed">System online. Submit an objective or text stream link to synthesize workflows, interactive slides, or technical study documentation.</p>
                </div>
            </div>
        </div>

        <!-- Input Actions Matrix Deck -->
        <footer class="p-4 bg-gradient-to-t from-[#0D0D0D] via-[#0D0D0D] to-transparent dark:from-[#FFFFFF] dark:via-[#FFFFFF] z-10 theme-transition" id="mainFooter">
            <div class="max-w-2xl w-full mx-auto relative flex flex-col items-center">
                
                <!-- Quick Action Prompt Hooks -->
                <div class="flex flex-wrap gap-1.5 mb-3 justify-start w-full px-1">
                    <button onclick="applyQuickAction('Explain this concept simply with examples: ')" class="px-3 py-1 text-xs font-medium rounded-md bg-[#171717] dark:bg-white border border-[#262626] dark:border-neutral-300 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-all">Simplify Concept</button>
                    <button onclick="applyQuickAction('Give me a 3-question conceptual quiz on this topic: ')" class="px-3 py-1 text-xs font-medium rounded-md bg-[#171717] dark:bg-white border border-[#262626] dark:border-neutral-300 text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black transition-all">Quiz Assessment</button>
                    <button onclick="applyQuickAction('Create a professional presentation on ')" class="px-3 py-1 text-xs font-semibold rounded-md bg-white dark:bg-neutral-900 border border-white dark:border-neutral-900 text-black dark:text-white hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-sm">Create Slides</button>
                </div>

                <!-- Attached File Metadata View Badge -->
                <div id="filePreviewBar" class="hidden w-full bg-[#171717] dark:bg-neutral-100 border-x border-t border-[#262626] dark:border-neutral-300 px-4 py-2 rounded-t-xl flex items-center justify-between text-xs text-neutral-300 dark:text-neutral-700">
                    <div class="flex items-center gap-2 truncate">
                        <span class="text-neutral-400 dark:text-neutral-500">📎</span>
                        <span id="fileNameDisplay" class="truncate font-mono">source.data</span>
                    </div>
                    <button onclick="removeAttachedFile()" class="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black underline font-semibold px-1">Discard</button>
                </div>

                <!-- Main Context Entry Console Box -->
                <div id="inputContainer" class="w-full relative flex items-center bg-[#171717] dark:bg-white rounded-xl border border-[#262626] dark:border-neutral-300 group transition-all shadow-xs focus-within:border-neutral-400 dark:focus-within:border-neutral-500">
                    <input type="file" id="filePayloadInput" class="hidden" onchange="handleFilePayloadSelection(event)" accept="image/*,application/pdf">
                    <button onclick="document.getElementById('filePayloadInput').click()" class="absolute left-3.5 p-1.5 text-neutral-500 dark:text-neutral-400 hover:text-white dark:hover:text-black transition-colors" aria-label="Attach File">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" /></svg>
                    </button>
                    <textarea id="messageInput" rows="1" placeholder="Type a message or paste a link..." class="w-full bg-transparent text-white dark:text-black placeholder-neutral-600 dark:placeholder-neutral-400 pl-12 pr-14 py-3.5 resize-none focus:outline-none text-[15px] max-h-40 overflow-y-auto" onkeydown="handleKeyDown(event)"></textarea>
                    <button onclick="commitMessageToSend()" class="absolute right-3 p-1.5 bg-white dark:bg-neutral-900 text-black dark:text-white border border-transparent dark:border-neutral-700 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-xs" aria-label="Send message">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
            </div>
        </footer>
    </main>

    <!-- Modal Interactive Slides Deck Frame View -->
    <div id="presentationModal" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-4 backdrop-blur-md transition-opacity duration-300">
        <div class="bg-[#171717] dark:bg-white border border-[#262626] dark:border-neutral-200 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden shadow-2xl relative">
            
            <!-- Slides View Header Context Controls -->
            <div class="px-5 py-3 border-b border-[#262626] dark:border-neutral-200 flex items-center justify-between bg-[#0D0D0D] dark:bg-neutral-50">
                <div class="flex items-center gap-2">
                    <h3 class="font-bold text-white dark:text-neutral-800 text-xs tracking-widest uppercase">ATOM-FLOW Presentation Hub</h3>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="downloadPresentationFile()" class="px-3 py-1 text-xs font-semibold bg-white dark:bg-neutral-900 text-black dark:text-white border dark:border-neutral-700 rounded-md hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-all shadow-sm">Download Deck</button>
                    
                    <!-- Highly Visible Desktop Modal Window Close Element -->
                    <button onclick="closePresentationWorkspace()" class="text-neutral-400 dark:text-neutral-600 hover:text-white dark:hover:text-black text-xs bg-[#262626] dark:bg-neutral-200 px-3 py-1 rounded-md transition-all font-medium">Close Deck</button>
                </div>
            </div>
            
            <!-- Embedded Core Slide Output Window Content -->
            <div class="flex-1 bg-black relative">
                <iframe id="presentationFrame" class="w-full h-full border-none"></iframe>
            </div>

            <!-- Mobile Gesture Close Prompt Strip Anchor -->
            <div onclick="closePresentationWorkspace()" class="bg-[#0D0D0D] dark:bg-neutral-50 text-center py-2 text-xs border-t border-[#262626] dark:border-neutral-200 text-neutral-500 hover:text-neutral-300 dark:hover:text-black cursor-pointer select-none font-semibold uppercase tracking-wider transition-colors">
                ↑ Click here or Swipe up to exit workspace preview ↑
            </div>
        </div>
    </div>

    <script>
        let isDarkMode = true;
        let attachedFileB64 = null;
        let attachedFileMime = null;
        let currentPresentationHtml = "";

        // Establish core markdown styling variables
        marked.setOptions({ gfm: true, breaks: true });

        // Touch Interaction Variables for Slide-out Navigation & Dismissals
        let touchStartX = 0;
        let touchEndX = 0;
        let touchStartY = 0;
        let touchEndY = 0;

        // Mobile Sidebar Management Framework
        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            
            if (sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.remove('-translate-x-full');
                overlay.classList.remove('hidden');
            } else {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            }
        }

        // --- FULL-SCALE LIGHT MODE VS DARK MODE GRAPHIC REBUILD ---
        function toggleThemeConfig() {
            isDarkMode = !isDarkMode;
            const body = document.getElementById('appBody');
            const themeBtnLabel = document.getElementById('themeBtnLabel');
            const mainHeader = document.getElementById('mainHeader');
            const mainFooter = document.getElementById('mainFooter');
            const sidebar = document.getElementById('sidebar');
            
            if (!isDarkMode) {
                // Apply Light Mode Classes
                body.classList.replace('theme-dark', 'theme-light');
                body.classList.replace('bg-[#0D0D0D]', 'bg-[#FFFFFF]');
                body.classList.replace('text-[#ECECEC]', 'text-[#171717]');
                
                mainHeader.classList.replace('bg-[#0D0D0D]/90', 'bg-white/90');
                mainHeader.classList.replace('border-[#262626]', 'border-neutral-200');
                
                themeBtnLabel.innerHTML = "Light";
                themeBtnLabel.classList.replace('bg-[#262626]', 'bg-neutral-200');
                themeBtnLabel.classList.replace('text-white', 'text-neutral-900');
                
                // Regenerate Dynamic Feed Items for Light Mode contrast
                document.querySelectorAll('.user-bubble').forEach(el => {
                    if (el) {
                        el.classList.replace('bg-[#171717]', 'bg-neutral-100');
                        el.classList.replace('text-neutral-100', 'text-neutral-900');
                        el.classList.replace('border-[#262626]', 'border-neutral-200');
                    }
                });
                
                document.querySelectorAll('.model-text-container').forEach(el => {
                    if (el) el.classList.replace('text-neutral-300', 'text-neutral-800');
                });

            } else {
                // Revert to Dark Mode Classes
                body.classList.replace('theme-light', 'theme-dark');
                body.classList.replace('bg-[#FFFFFF]', 'bg-[#0D0D0D]');
                body.classList.replace('text-[#171717]', 'text-[#ECECEC]');
                
                mainHeader.classList.replace('bg-white/90', 'bg-[#0D0D0D]/90');
                mainHeader.classList.replace('border-neutral-200', 'border-[#262626]');
                
                themeBtnLabel.innerHTML = "Dark";
                themeBtnLabel.classList.replace('bg-neutral-200', 'bg-[#262626]');
                themeBtnLabel.classList.replace('text-neutral-900', 'text-white');
                
                document.querySelectorAll('.user-bubble').forEach(el => {
                    if (el) {
                        el.classList.replace('bg-neutral-100', 'bg-[#171717]');
                        el.classList.replace('text-neutral-900', 'text-neutral-100');
                        el.classList.replace('border-neutral-200', 'border-[#262626]');
                    }
                });
                
                document.querySelectorAll('.model-text-container').forEach(el => {
                    if (el) el.classList.replace('text-neutral-800', 'text-neutral-300');
                });
            }
        }

        function handleFilePayloadSelection(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                attachedFileB64 = e.target.result.split(',')[1];
                attachedFileMime = file.type;
                document.getElementById('fileNameDisplay').innerText = file.name;
                document.getElementById('filePreviewBar').classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        function removeAttachedFile() {
            attachedFileB64 = null; attachedFileMime = null;
            document.getElementById('filePayloadInput').value = "";
            document.getElementById('filePreviewBar').classList.add('hidden');
        }

        function applyQuickAction(prefixText) {
            const input = document.getElementById('messageInput');
            input.value = prefixText;
            input.focus();
        }

        function clearChatLog() {
            fetch('/clear', { method: 'POST' }).then(() => {
                document.getElementById('chatFeed').innerHTML = '';
            });
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                commitMessageToSend();
            }
        }

        // Refactored Message DOM Builder supporting semantic light mode context rules
        function appendMessageRow(text, isUser) {
            const feed = document.getElementById('chatFeed');
            let contentHtml = isUser ? text : marked.parse(text);
            
            let userBg = isDarkMode ? "bg-[#171717] text-neutral-100 border-[#262626]" : "bg-neutral-100 text-neutral-900 border-neutral-200";
            let modelColor = isDarkMode ? "text-neutral-300" : "text-neutral-800";
            
            let row = isUser ? 
                `<div class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto"><div class="user-bubble border rounded-2xl px-4 py-2.5 text-[15px] shadow-xs theme-transition ${userBg}">${contentHtml}</div></div>` :
                `<div class="flex gap-4 items-start text-base border-t border-neutral-800/10 dark:border-neutral-200/40 pt-6"><div class="w-8 h-8 rounded-md bg-white dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 flex items-center justify-center shrink-0 shadow-xs"><svg class="w-5 h-5 text-black dark:text-white fill-none stroke-current" viewBox="0 0 100 100" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"><path d="M15 85 L50 15 L70 55" /><path d="M50 15 L85 15" /><path d="M30 60 L60 60" /><path d="M52 45 C65 45, 65 60, 80 60" /></svg></div><div class="space-y-1 flex-1 pt-0.5"><p class="font-bold text-xs tracking-wider uppercase text-neutral-400 dark:text-neutral-500">ATOM-FLOW Core</p><div class="model-text-container prose text-[15px] leading-relaxed theme-transition ${modelColor}">${contentHtml}</div></div></div>`;
            
            feed.insertAdjacentHTML('beforeend', row);
            feed.scrollTop = feed.scrollHeight;
        }

        // Open Presentation Slide Modal Layer
        function openPresentationWorkspace(rawSlideCode) {
            if (!rawSlideCode) return;
            currentPresentationHtml = rawSlideCode;
            document.getElementById('presentationModal').classList.remove('hidden');
            document.getElementById('presentationFrame').srcdoc = rawSlideCode;
        }

        // Close Deck Action Handler
        function closePresentationWorkspace() {
            document.getElementById('presentationModal').classList.add('hidden');
            document.getElementById('presentationFrame').srcdoc = "";
        }

        function downloadPresentationFile() {
            if (!currentPresentationHtml) return;
            const blob = new Blob([currentPresentationHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'ATOM-FLOW-Presentation.html';
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText && !attachedFileB64) return;

            appendMessageRow(attachedFileB64 ? "📸 [Attached File] " + messageText : messageText, true);
            input.value = '';

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText, file_data: attachedFileB64, file_mime: attachedFileMime })
            })
            .then(res => res.json())
            .then(data => {
                appendMessageRow(data.reply, false);
                if (data.presentation_html) openPresentationWorkspace(data.presentation_html);
            })
            .catch(() => appendMessageRow("System connection error.", false));
            removeAttachedFile();
        }

        // --- GESTURE NAVIGATION AND SWIPE ROUTINES ---
        document.addEventListener('touchstart', e => {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }, false);

        document.addEventListener('touchend', e => {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleGlobalSwipeGestures();
        }, false);

        function handleGlobalSwipeGestures() {
            const horizontalSwipeLength = touchEndX - touchStartX;
            const verticalSwipeLength = touchEndY - touchStartY;
            const sidebar = document.getElementById('sidebar');
            const presentationModal = document.getElementById('presentationModal');

            // 1. Sidebar Left/Right Swipe Navigation
            if (Math.abs(horizontalSwipeLength) > 100 && Math.abs(verticalSwipeLength) < 60) {
                if (horizontalSwipeLength > 0 && sidebar.classList.contains('-translate-x-full')) {
                    toggleMobileSidebar();
                } else if (horizontalSwipeLength < 0 && !sidebar.classList.contains('-translate-x-full')) {
                    toggleMobileSidebar();
                }
            }

            // 2. Slide View Modal Upward Dismissal Swipe Action
            if (!presentationModal.classList.contains('hidden')) {
                if (verticalSwipeLength < -80) {
                    closePresentationWorkspace();
                }
            }
        }
    </script>
</body>
</html>
"""

# --- REVEAL.JS MONOCHROME PRESENTATION COMPILER ---
def extract_presentation_template(raw_llm_markdown: str) -> Optional[str]:
    match = re.search(r'```slides\s*(.*?)\n```', raw_llm_markdown, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
        
    slide_content_markdown = match.group(1)
    raw_slides = slide_content_markdown.split("---")
    slide_sections = ""
    
    for slide in raw_slides:
        if slide.strip():
            clean_slide = slide.strip()
            html_lines = []
            for line in clean_slide.split('\n'):
                line = line.strip()
                if not line: continue
                if line.startswith('### '): html_lines.append(f"<h3>{line[4:]}</h3>")
                elif line.startswith('## '): html_lines.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith('# '): html_lines.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith('* ') or line.startswith('- '): html_lines.append(f"<li>{line[2:]}</li>")
                else:
                    processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                    html_lines.append("<p>" + processed_line + "</p>")
            
            final_content = ""
            in_list = False
            for item in html_lines:
                if item.startswith('<li>'):
                    if not in_list: final_content += "<ul>"; in_list = True
                    final_content += item
                else:
                    if in_list: final_content += "</ul>"; in_list = False
                    final_content += item
            if in_list: final_content += "</ul>"
            slide_sections += f"<section data-background-color='#000000'>\n{final_content}\n</section>\n"

    if not slide_sections:
        return None

    presentation_base = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css">
        <style>
            .reveal h1, .reveal h2, .reveal h3 { color: #FFFFFF !important; font-weight: bold; text-transform: none; }
            .reveal li, .reveal p { color: #A3A3A3 !important; font-size: 24px; line-height: 1.5; }
            .reveal ul { display: inline-block; text-align: left; }
        </style>
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                __SLIDE_PLACEHOLDER__
            </div>
        </div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"></script>
        <script>
            setTimeout(() => {
                Reveal.initialize({ controls: true, progress: true, center: true, embedded: true });
            }, 200);
        </script>
    </body>
    </html>
    """
    return presentation_base.replace("__SLIDE_PLACEHOLDER__", slide_sections)

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global USER_SESSION_CONTEXT
    user_prompt = request.message.strip()
    
    if not ai_client:
        return {"reply": "API Key configuration error."}

    content_parts = []
    if request.file_data and request.file_mime:
        try:
            content_parts.append(types.Part.from_bytes(data=base64.b64decode(request.file_data), mime_type=request.file_mime))
        except Exception:
            raise HTTPException(status_code=400, detail="Mime payload processing error.")

    url_pattern = re.compile(r'https?://[^\s]+')
    found_urls = url_pattern.findall(user_prompt)
    if found_urls:
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(found_urls[0], headers=headers, timeout=10.0)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style"]): tag.decompose()
            user_prompt = f"Scraped Context:\n\"\"\"\n{(' '.join(soup.get_text().split()))[:3000]}\n\"\"\"\n\nUser Message: {user_prompt}"
        except Exception: pass

    content_parts.append(types.Part.from_text(text=user_prompt))
    is_presentation_request = any(k in user_prompt.lower() for k in ["presentation", "slide deck", "slides"])

    system_instruction = (
        "You are ATOM-FLOW, a context-aware multi-modal workspace assistant. Provide beautiful markdown responses.\n\n"
        "CRITICAL FOR PRESENTATIONS/SLIDES:\n"
        "If requested, provide the presentation block wrapped EXACTLY inside a ```slides custom block format. Use '---' to separate slides.\n"
        "Example:\n```slides\n# Slide One\n## Subtitle\n* Bullet point\n---\n# Slide Two\n```"
    )

    temp_context = list(USER_SESSION_CONTEXT)
    temp_context.append(types.Content(role="user", parts=content_parts))

    max_retries = 3
    base_delay = 5.0  
    
    for attempt in range(max_retries + 1):
        try:
            response = await ai_client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=temp_context,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            response_text = response.text

            USER_SESSION_CONTEXT.append(types.Content(role="user", parts=content_parts))
            USER_SESSION_CONTEXT.append(types.Content(role="model", parts=[types.Part.from_text(text=response_text)]))

            return_data = {"reply": response_text}
            if is_presentation_request:
                presentation_html = extract_presentation_template(response_text)
                if presentation_html: return_data["presentation_html"] = presentation_html

            return return_data

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt < max_retries:
                    wait_match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    sleep_time = float(wait_match.group(1)) if wait_match else (base_delay * (2 ** attempt) + random.uniform(0, 1))
                    await asyncio.sleep(sleep_time + 0.5)
                    continue
            return {"reply": f"Handshake Generation Exception Failure Channel: {error_msg}"}

@app.post("/clear")
async def clear_context():
    global USER_SESSION_CONTEXT
    USER_SESSION_CONTEXT.clear()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))