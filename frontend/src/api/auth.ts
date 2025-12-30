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
      const response = await fetch('/api/v1/users/me', {
        credentials: 'include'
      })
      return response.ok
    } catch {
      return false
    }
  },
  getCurrentUser: async () => {
    try {
      const response = await fetch('/api/v1/users/me', {
        credentials: 'include'
      })
      if (response.ok) {
        return await response.json()
      }
    } catch (e) {
      console.error("Auth check failed", e)
    }
    return null
  }
}
