import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'

export const Route = createFileRoute('/auth/callback')({
  component: AuthCallback,
})

function AuthCallback() {
  const navigate = useNavigate()
  const search = Route.useSearch() as { error?: string }
  const error = search.error || null

  useEffect(() => {
    if (!search.error) {
      // Success! Cookie should be set.
      navigate({ to: '/' })
    }
  }, [search.error, navigate])

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="text-4xl font-display text-retro-dark mb-4">ACCESS DENIED</h2>
        <p className="text-xl text-retro-pink font-bold">{error}</p>
        <button
          onClick={() => navigate({ to: '/login' })}
          className="mt-8 px-8 py-3 bg-retro-teal rounded-xl border-4 border-retro-dark shadow-retro"
        >
          RETURN TO IDENTIFICATION
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Loader2 className="w-16 h-16 animate-spin text-retro-teal" />
      <h2 className="mt-6 text-3xl font-display text-retro-dark uppercase">
        Verifying Credentials...
      </h2>
    </div>
  )
}
