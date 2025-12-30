import { createFileRoute } from '@tanstack/react-router'
import { Music2, Loader2, ArrowRight } from 'lucide-react'
import { useState } from 'react'

export const Route = createFileRoute('/login')({
  component: Login,
})

function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setMessage('')

    try {
      const endpoint = isLogin ? '/api/v1/auth/jwt/login' : '/api/v1/auth/register'

      const formData = new URLSearchParams()
      if (isLogin) {
        formData.append('username', email)
        formData.append('password', password)
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: isLogin
          ? { 'Content-Type': 'application/x-www-form-urlencoded' }
          : { 'Content-Type': 'application/json' },
        body: isLogin
          ? formData.toString()
          : JSON.stringify({ email, password }),
        credentials: 'include'
      })

      if (response.ok) {
        if (isLogin) {
          setMessage('Access Granted! Teleporting...')
          // Use window.location to ensure fresh state/cookies are picked up
          window.location.href = '/'
        } else {
          setMessage('Registration Successful! You may now authenticate.')
          setIsLogin(true)
        }
      } else {
        const error = await response.json()
        setMessage(`Error: ${error.detail || 'Access Denied'}`)
      }
    } catch (err) {
      setMessage('System Error: Communications failure.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-full max-w-lg bg-white p-12 rounded-2xl border-8 border-retro-dark shadow-retro relative overflow-hidden">
        {/* Machine Lights */}
        <div className="absolute top-0 left-0 w-full h-8 bg-retro-teal border-b-4 border-retro-dark flex items-center justify-around px-12">
          <div className={`w-3 h-3 rounded-full border-2 border-retro-dark ${isLoading ? 'animate-pulse bg-retro-pink' : 'bg-retro-dark/20'}`}></div>
          <div className={`w-3 h-3 rounded-full border-2 border-retro-dark ${isLoading ? 'animate-pulse bg-retro-yellow' : 'bg-retro-dark/20'}`}></div>
          <div className={`w-3 h-3 rounded-full border-2 border-retro-dark ${isLoading ? 'animate-pulse bg-retro-teal' : 'bg-retro-dark/20'}`}></div>
        </div>

        <div className="text-center mt-4">
          <div className="flex justify-center mb-6">
            <div className="bg-retro-pink p-4 rounded-2xl border-4 border-retro-dark shadow-retro-sm">
              <Music2 className="h-12 w-12 text-retro-dark" />
            </div>
          </div>
          <h2 className="text-5xl font-display tracking-tighter text-retro-dark uppercase italic">
            {isLogin ? 'Identification' : 'Registration'}
          </h2>
          <p className="mt-2 font-display text-retro-teal text-xl tracking-widest uppercase">
            {isLogin ? 'Vib-O-Mat Series 2000' : 'Join the Future'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-10 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-xl font-display text-retro-dark uppercase mb-2">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-retro-cream rounded-xl border-4 border-retro-dark p-4 text-xl font-body font-bold shadow-retro-sm focus:outline-none focus:ring-8 focus:ring-retro-teal/20"
                placeholder="citizen@example.com"
              />
            </div>
            <div>
              <label className="block text-xl font-display text-retro-dark uppercase mb-2">Security Cipher</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-retro-cream rounded-xl border-4 border-retro-dark p-4 text-xl font-body font-bold shadow-retro-sm focus:outline-none focus:ring-8 focus:ring-retro-teal/20"
                placeholder="••••••••"
              />
            </div>
          </div>

          {message && (
            <div className={`p-4 rounded-lg border-2 border-retro-dark font-body font-bold text-center ${message.startsWith('Error') ? 'bg-retro-pink' : 'bg-retro-yellow'}`}>
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-10 py-4 bg-retro-teal hover:bg-teal-400 text-retro-dark text-2xl font-display rounded-2xl border-4 border-retro-dark shadow-retro active:shadow-none active:translate-x-1 active:translate-y-1 transition-all disabled:opacity-50 flex items-center justify-center gap-3"
          >
            {isLoading ? <Loader2 className="animate-spin" /> : <>{isLogin ? 'AUTHENTICATE' : 'REGISTER'} <ArrowRight /></>}
          </button>
        </form>

        <div className="mt-8 text-center pt-6 border-t-4 border-retro-dark border-dashed">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-lg font-display text-retro-dark hover:text-retro-teal transition-colors uppercase tracking-widest"
          >
            {isLogin ? "Need a clearance level? Register" : "Already have clearance? Login"}
          </button>
        </div>
      </div>
    </div>
  )
}
