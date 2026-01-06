import { apiClient, UnauthorizedError } from './client'

export interface Album {
  name: string
  artist: string
}

export interface ServiceConnection {
  provider_name: string
  is_connected: boolean
  client_id?: string
  has_secret: boolean
  scopes?: string[]
}

export interface User {
  id: string
  email: string
  handle?: string
  first_name?: string
  last_name?: string
  display_name: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  is_public: boolean
  favorite_artists: unknown[] // Keep unknown[] here for flexibility in the API schema
  unskippable_albums: Album[]
  service_connections: ServiceConnection[]
}

export const authService = {
  logout: async () => {
    try {
      await fetch('/api/v1/auth/jwt/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } finally {
      window.location.href = '/login'
    }
  },
  checkAuth: async () => {
    try {
      await apiClient<User>('/users/me')
      return true
    } catch {
      return false
    }
  },
  getCurrentUser: async () => {
    try {
      return await apiClient<User>('/users/me')
    } catch (e) {
      if (e instanceof UnauthorizedError) {
        return null
      }
      console.error("Auth check failed", e)
    }
    return null
  }
}
