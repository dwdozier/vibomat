import { apiClient } from './client'

export interface Track {
  artist: string
  track: string
  album?: string
  version?: string
  duration_ms?: number
}

export interface GenerationRequest {
  prompt: string
  count?: number
  artists?: string
}

export interface VerificationRequest {
  tracks: Track[]
}

export interface VerificationResponse {
  verified: Track[]
  rejected: string[]
}

export interface BuildResponse {
  status: string
  playlist_id: string
  url: string
  failed_tracks: string[]
}

export const playlistService = {
  generate: (req: GenerationRequest) =>
    apiClient<Track[]>('/playlists/generate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  verify: (req: VerificationRequest) =>
    apiClient<VerificationResponse>('/playlists/verify', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  build: (req: { name: string; description?: string; public?: boolean; tracks: Track[] }) =>
    apiClient<BuildResponse>('/playlists/build', {
      method: 'POST',
      body: JSON.stringify(req),
    }),
}
