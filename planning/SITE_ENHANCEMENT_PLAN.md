# Vib-O-Mat Site Enhancement & Cleanup Plan (Series 2000)

This plan outlines the next phase of development for the Vib-O-Mat, focusing on security,
intelligence-driven personalization, social collaboration, and aesthetic refinement.

## 1. Vision: The Social Music Network

Transform the Vib-O-Mat from a solitary tool into a community of Citizens sharing high-fidelity
tastes, powered by deep AI analysis and individual transponders.

---

## 2. Phase 1: Foundation, Security & Public Identity

**Objective:** Secure the machinery and allow Citizens to define their public presence.

* **Authentication Gating:**
  * Protect `/playlists`, `/settings`, and `/connections` via TanStack Router `beforeLoad` guards.
  * Strict `current_user` enforcement on all sensitive API endpoints.
* **Public vs. Private Profiles:**
  * Add a "Privacy Shield" toggle in Settings to control the visibility of the user's Profile.
  * **Public Profile View:** A landing page showing the Citizen's favorite artists, playlists,
        and "Favorited" source playlists from others.
* **Unskippable Archives:**
  * Feature to mark specific albums as "Unskippable" (The "Gold Standard" of albums).
  * These appear prominently on the Citizen's public profile.

## 3. Phase 2: Intelligence Ingestion (Taste Formulation)

**Objective:** The Vib-O-Mat learns the Citizen's preferences by scanning existing archives.

* **Playlist Ingestion:**
  * Implement logic to fetch and index a user's existing playlists from connected services
        (Spotify, etc.).
* **AI Taste Analysis:**
  * Use the backend AI (Gemini/OpenAI) to analyze ingested tracks and formulate "Taste Metadata"
        (e.g., preferred sub-genres, BPM ranges, lyrical themes).
* **Personalized Scoping:**
  * Incorporate this "Taste Metadata" into the `AIService` prompt engineering to generate
        excellently scoped playlists that feel "uniquely you."

## 4. Phase 3: Individual AI Transponders (User AI Keys)

**Objective:** Empower Citizens to use their own credentials while maintaining a global fallback.

* **User Keys (Transponders):**
  * Secure storage for user-supplied Gemini/OpenAI keys in the database (encrypted).
  * UI in Settings to manage these keys.
* **Logic Hierarchy:**
  * 1. User-supplied Key -> 2. Global System Key (Limited Quota) -> 3. Request Key Entry.
  * Implement strict daily generation limits for users on the Global Key.

## 5. Phase 4: Social Synthesis & Publishing

**Objective:** Allow Citizens to "Broadcast" their creations and collaborate.

* **Playlist Publishing:**
  * Option to "Publish to the Broadcast Network" (Make a generated playlist public).
* **Cross-Citizen Generation:**
  * Citizens can view another user's public playlist and click "Generate on my Service" to
        clonally build it on their own streaming provider.
* **Favoriting & Attribution:**
  * Track the "Original Source" of a playlist. When a Citizen favorites a published playlist,
        the original creator is credited on the favoriter's profile.

## 6. Phase 5: Aesthetic & UX Refinement (The "Series 2000" Look)

**Objective:** Elevate the sensory experience.

* **Nixie Tube Loaders:** Custom animations for background tasks and generation phases.
* **CRT Scanline Toggle:** Optional visual filter for the true retro-industrial enthusiast.
* **Real-time Progress:** Websocket-driven feedback (e.g., "Synthesizing Taste Metadata... 62%").
* **Custom Cover Art:** Integration for uploading unique artwork during the "Build" phase.

## 7. Phase 6: Connectivity & Evolution

**Objective:** Advanced infrastructure and cross-platform alignment.

* **Background Tasks:** Full `TaskIQ` + Redis integration for rock-solid async builds.
* **Multi-Service Sync:** Simultaneously push to Spotify, Apple Music, and YouTube Music.
* **CLI as a Thin Client:** Refactor the CLI to authenticate and interact via the Web API.

---

## 8. Logical Implementation Order

1. **Phase 1 (Security & Profiles):** Establish the gates and the "Citizen Identity."
2. **Phase 3 (AI Keys):** Set up the transponder logic before heavy AI usage begins.
3. **Phase 2 (Ingestion & Tastes):** Implement the "Learning" logic once keys are ready.
4. **Phase 4 (Social & Publishing):** Enable the community features once profiles and tastes
    exist.
5. **Phase 5 & 6 (Polish & Advanced):** Parallelize UX enhancements and infrastructure upgrades.
