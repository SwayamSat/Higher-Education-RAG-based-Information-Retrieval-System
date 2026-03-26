# Frontend Workflow
## Self-Correcting Multi-Agent RAG — Frontend Tasks

> 14 work items across 4 phases. Uses **Stitch MCP** for design system and attractive, minimal UI generation.

---

## Phase 1 — Design System & UI Foundation (via Stitch MCP)

### Work 1.1: Create Project Design System with Stitch MCP
**Tool**: `mcp_StitchMCP_create_design_system`
**Goal**: Establish a cohesive, minimal, premium design system for the entire app.
**Steps**:
1. Use Stitch MCP `create_design_system` to define:
   - **Color Palette**: Deep navy primary (`#1E293B`), bright indigo accent (`#6366F1`), clean white surfaces — professional government aesthetic
   - **Typography**: Inter font family (already used in [layout.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/layout.tsx))
   - **Shape**: Medium corner roundness (12-16px for cards, 24px for chat bubbles)
   - **Appearance**: Light mode with subtle gray backgrounds; optional dark mode toggle
   - **Design MD**: "Minimal, professional government information system. Clean cards, clear typography hierarchy, generous whitespace. No clutter. Every element serves a purpose."
2. Use `update_design_system` to apply it to the project

**Acceptance**: Design system is created in Stitch with consistent tokens.

---

### Work 1.2: Redesign Chat Page with Stitch MCP
**Tool**: `mcp_StitchMCP_generate_screen_from_text` / `mcp_StitchMCP_edit_screens`
**File**: [frontend/src/app/page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx)
**Goal**: Generate a premium, minimal chat interface design.
**Steps**:
1. Use Stitch MCP `generate_screen_from_text` with prompt:
   > "A minimal, professional government document assistant chat interface. 
   > Clean header with app logo and title 'Smart Retrieval RAG'. 
   > Main chat area with alternating user/assistant message bubbles. 
   > Assistant messages have expandable source citation cards and color-coded confidence/verification badges. 
   > Bottom input bar with textarea and send button. 
   > Left sidebar showing chat history sessions. 
   > Design should feel like a premium SaaS tool — clean whites, subtle shadows, indigo accents."
2. Generate variants using `generate_variants` to explore 2-3 design directions
3. Pick the best variant and translate the design into the Next.js [page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx) component
4. Update [globals.css](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/globals.css) with the design system tokens

**Acceptance**: Chat page matches the Stitch-generated design; looks polished and minimal.

---

### Work 1.3: Create Shared Component Library
**Files**: Create `frontend/src/components/` directory:
- `components/Badge.tsx` — Confidence & verification badges
- `components/SourceCard.tsx` — Expandable source citation
- `components/PipelineStep.tsx` — Agent step visualization
- `components/MessageBubble.tsx` — Chat message (extracted from page.tsx)
- `components/Sidebar.tsx` — Chat history sidebar
- `components/FileUpload.tsx` — Drag-and-drop upload zone
- `components/FeedbackButtons.tsx` — Thumbs up/down

**Steps**:
1. Extract [MessageBubble](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx#175-218) and [MessageMetadata](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx#219-318) from current [page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx) into separate components
2. Create each component with proper TypeScript types
3. Use the design system colors/spacing from Work 1.1 throughout
4. Each component should be self-contained with its own styles

**Acceptance**: [page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx) imports from `components/`; no inline component definitions in pages.

---

## Phase 2 — Core UI Features

### Work 2.1: SSE Streaming Chat
**File**: [frontend/src/app/page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx)
**Goal**: Token-by-token typewriter effect for responses.
**Steps**:
1. Replace `axios.post("/query")` with an `EventSource` / `fetch` SSE connection to `/query/stream`
2. Handle SSE event types:
   - `token` → append text character by character to current message
   - `sources` → populate source cards panel
   - `verification` → show verification badge
   - `done` → mark message as complete
   - `error` → show error state
3. Show a blinking cursor while streaming
4. Auto-scroll to bottom as tokens arrive
5. Disable input while streaming; show "Stop" button to cancel
6. Fallback to regular POST if SSE connection fails

**Acceptance**: User sees response text appearing word-by-word; sources and verification appear after text is done.

---

### Work 2.2: Document Upload Page
**Tool**: `mcp_StitchMCP_generate_screen_from_text` for design
**File**: New `frontend/src/app/upload/page.tsx`
**Goal**: Drag-and-drop document upload with indexing status.
**Steps**:
1. Use Stitch MCP to generate the upload page design:
   > "A minimal document upload page for a government RAG system. 
   > Large drag-and-drop zone in the center with dashed border and upload icon. 
   > Department selector dropdown. 
   > Upload progress bar. 
   > Below the upload zone: a table listing recently uploaded documents with filename, department, chunk count, status (indexing/indexed/failed), and delete button. 
   > Clean, professional design matching the chat page style."
2. Implement the component:
   - Drag-and-drop zone using native HTML5 drag events
   - `POST /documents/upload` with `FormData` (file + department)
   - Progress indicator during upload
   - Table showing documents from `GET /documents`
   - Delete button calling `DELETE /documents/{doc_id}`
   - Auto-refresh documents list after upload/delete
3. Add navigation link in the header/sidebar

**Acceptance**: User can drag a PDF → see upload progress → document appears in list as "indexing" → changes to "indexed".

---

### Work 2.3: Chat History Sidebar
**File**: [frontend/src/app/page.tsx](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx), `components/Sidebar.tsx`
**Goal**: Persist chats in localStorage; show session list in sidebar.
**Steps**:
1. Define session data structure:
   ```typescript
   type ChatSession = {
     id: string;
     title: string;        // Auto-generated from first query
     messages: Message[];
     createdAt: string;
     updatedAt: string;
   };
   ```
2. Save messages to `localStorage` keyed by session ID after each response
3. Build sidebar component:
   - "New Chat" button at top
   - List of past sessions sorted by `updatedAt`
   - Session title = first 50 chars of first user query
   - Click to load session messages
   - Delete session button (with confirmation)
4. Collapse sidebar on mobile (hamburger toggle)
5. Use Stitch MCP to design the sidebar layout:
   > "Minimal left sidebar for chat history. 'New Chat' button at top. 
   > List of past chat sessions with title and timestamp. 
   > Hover highlights. Selected session has accent border. Compact design."

**Acceptance**: Chats persist across page refresh; clicking a past session loads its messages.

---

### Work 2.4: Feedback Buttons
**File**: `components/FeedbackButtons.tsx`, update `MessageBubble.tsx`
**Goal**: Thumbs up/down on each assistant response.
**Steps**:
1. Create `FeedbackButtons` component:
   - Two icon buttons: 👍 (thumbs up) and 👎 (thumbs down)
   - Optional comment textarea on thumbs down
   - Sends `POST /feedback` with `{ query_id, rating, comment }`
   - Visually locks after selection (can't change)
2. Add below each assistant message (after verification badge)
3. Style: subtle, small icons that highlight on hover
4. Show a brief "Thanks for feedback" toast on submit

**Acceptance**: User can rate each response; rating appears locked after submission.

---

### Work 2.5: Pipeline Visualization Panel
**Tool**: `mcp_StitchMCP_generate_screen_from_text` for design
**File**: New `components/PipelineVisualization.tsx`
**Goal**: Show the multi-agent pipeline steps for each response.
**Steps**:
1. Use Stitch MCP to design the component:
   > "A horizontal pipeline visualization showing agent steps: Router → Relevance → Generator → Fact-Check → (optional) Correction loops. 
   > Each step is a rounded card with agent name, duration in ms, and a status icon (checkmark or warning). 
   > Connected by arrows or lines. 
   > Correction iterations shown as loops below. 
   > Compact, fits below a chat message. Minimal design."
2. Implement the component:
   - Reads `pipeline_steps` from the response
   - Renders each step as a card with:
     - Agent name icon (🔍 Retrieval, ✍️ Generator, ✅ Fact-Check, 🔄 Correction)
     - Duration in ms
     - Green/yellow/red dot for status
   - Correction loops shown as indented sub-steps with iteration number
3. Make it collapsible (default collapsed) — toggle button: "Show Pipeline"
4. Add to [MessageBubble](file:///d:/Projects/Smart%20Retrival%20of%20Education%20System%20%28RAG%29/frontend/src/app/page.tsx#175-218) component, below the source panel

**Acceptance**: Each response has a collapsible pipeline view showing which agents ran and how long each took.

---

## Phase 3 — Additional Pages

### Work 3.1: Documents Library Page
**Tool**: `mcp_StitchMCP_generate_screen_from_text`
**File**: New `frontend/src/app/documents/page.tsx`
**Goal**: Browse all indexed documents.
**Steps**:
1. Stitch MCP prompt:
   > "A document library page with a grid of document cards. 
   > Each card shows: PDF icon, filename, department badge, chunk count, and indexed date. 
   > Search/filter bar at top. Department filter dropdown. 
   > Clean card layout with subtle shadows. Professional minimal style."
2. Implement:
   - Fetch from `GET /documents`
   - Grid of document cards
   - Filter by department
   - Search by filename
   - Click to see document details (metadata, chunk count)
3. Add to main navigation

**Acceptance**: User can browse all indexed documents, filter by department, and search by name.

---

### Work 3.2: Analytics Dashboard
**Tool**: `mcp_StitchMCP_generate_screen_from_text`
**File**: New `frontend/src/app/analytics/page.tsx`
**Goal**: Simple stats page showing system performance.
**Steps**:
1. Stitch MCP prompt:
   > "A minimal analytics dashboard for a RAG system. 
   > Top row: 4 stat cards (Total Queries, Avg Latency, Verification Pass Rate, Positive Feedback %). 
   > Below: simple bar chart showing queries per day. 
   > Clean, data-focused, no clutter. Government professional style."
2. Implement:
   - Fetch from `GET /analytics`
   - 4 stat cards at top with large numbers and labels
   - Simple bar chart (use a lightweight chart library like `recharts`)
   - Auto-refresh every 30 seconds

**Acceptance**: Dashboard shows real data from the API; updates automatically.

---

### Work 3.3: Landing / Welcome Page
**Tool**: `mcp_StitchMCP_generate_screen_from_text`
**File**: New `frontend/src/app/welcome/page.tsx` or update root page
**Goal**: A polished landing screen before the user starts chatting.
**Steps**:
1. Stitch MCP prompt:
   > "A hero landing page for 'Smart Retrieval RAG — Government Scheme Assistant'. 
   > Centered hero section with title, subtitle ('AI-powered document search for government policies'), and a 'Start Asking' CTA button. 
   > Below: 3 feature cards (Multi-Agent Pipeline, Self-Correcting Answers, Source-Backed Responses) with icons. 
   > Clean, minimal, inspiring. Indigo accent color. White background."
2. Implement:
   - Hero with animated gradient text or subtle motion (framer-motion — already installed)
   - 3 feature highlight cards
   - "Start Asking" button → navigates to `/chat`
3. Reorganize routes:
   - `/` → Landing page
   - `/chat` → Chat interface
   - `/upload` → Document upload
   - `/documents` → Document library
   - `/analytics` → Dashboard

**Acceptance**: Opening the app shows an impressive landing page; "Start Asking" takes user to chat.

---

## Phase 4 — Polish & Demo Prep

### Work 4.1: Responsive / Mobile Design
**Goal**: App works well on mobile screens for demo versatility.
**Steps**:
1. Test all pages at 375px (mobile), 768px (tablet), 1440px (desktop)
2. Sidebar becomes a slide-out drawer on mobile
3. Chat input is always accessible (sticky bottom)
4. Document cards switch from grid to single column on mobile
5. Use Stitch MCP `edit_screens` to refine mobile layouts:
   > "Optimize this screen for mobile (375px width). 
   > Stack elements vertically. Collapse sidebar into hamburger menu."

**Acceptance**: All pages usable on mobile without horizontal scrolling.

---

### Work 4.2: Loading States & Micro-Animations
**File**: Various components
**Goal**: Polished feel with smooth transitions.
**Steps**:
1. Add `framer-motion` (already installed) animations:
   - Message bubbles: slide in from bottom with fade
   - Badges: pop-in scale animation
   - Pipeline steps: sequential reveal (left to right)
   - Page transitions: fade between routes
2. Skeleton loading states:
   - Chat history sidebar: shimmer placeholders while loading
   - Documents list: card skeleton shapes
   - Analytics: pulsing placeholder numbers
3. Hover effects on all interactive elements
4. Smooth scroll in chat area

**Acceptance**: UI feels alive and polished; no jarring layout shifts.

---

### Work 4.3: Demo Screenshots & Final Review
**Tool**: `mcp_StitchMCP_generate_variants` for final design review
**Steps**:
1. Capture screenshots of all pages for presentation slides
2. Use Stitch MCP to generate any final design variants if something looks off
3. Test the complete user journey:
   - Land on welcome page → Start Asking → Ask a question → See streaming response → View sources → See pipeline → Give feedback → Upload a document → Query the uploaded document → Check analytics
4. Fix any visual inconsistencies
5. Verify all Stitch MCP design system tokens are consistently applied

**Acceptance**: Complete user journey works flawlessly; all pages are visually consistent and showcase-ready.

---

## Navigation Structure (Final)

```
┌─────────────────────────────────────────┐
│  Header: Logo + Nav Links               │
│  [Home] [Chat] [Upload] [Docs] [Stats]  │
└─────────────────────────────────────────┘

Routes:
  /            → Landing page (hero + features)
  /chat        → Chat interface + sidebar history
  /upload      → Document upload (drag & drop)
  /documents   → Document library (browse & filter)
  /analytics   → Simple dashboard with stats
```

---

## Stitch MCP Usage Summary

| Work Item | MCP Tool | Purpose |
|---|---|---|
| 1.1 | `create_design_system` + `update_design_system` | Create & apply visual theme |
| 1.2 | `generate_screen_from_text` + `generate_variants` | Design chat interface |
| 2.2 | `generate_screen_from_text` | Design upload page |
| 2.3 | `generate_screen_from_text` | Design sidebar |
| 2.5 | `generate_screen_from_text` | Design pipeline visualization |
| 3.1 | `generate_screen_from_text` | Design documents library |
| 3.2 | `generate_screen_from_text` | Design analytics dashboard |
| 3.3 | `generate_screen_from_text` | Design landing page |
| 4.1 | `edit_screens` | Optimize for mobile |
| 4.3 | `generate_variants` | Final design review |
