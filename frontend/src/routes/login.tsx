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
      })

      if (response.ok) {
        if (isLogin) {
          const data = await response.json()
          localStorage.setItem('token', data.access_token)
          setMessage('Access Granted! Teleporting...')
          window.location.href = '/'
        } else {
          setMessage('Registration Successful! Please check your email (Mailpit).')
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

  const handleOAuth = (provider: string) => {
    const callbackUrl = `${window.location.origin}/api/v1/auth/${provider}/authorize`
    window.location.href = callbackUrl
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

        {/* Social Protocols Section - Always Visible */}
        <div className="mt-8 grid grid-cols-2 gap-4">
          <button
            onClick={() => handleOAuth('google')}
            className="flex items-center justify-center gap-2 p-3 bg-white border-4 border-retro-dark rounded-xl shadow-retro-sm hover:bg-gray-50 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all font-display text-sm uppercase"
          >
            <img src="https://www.google.com/favicon.ico" className="w-5 h-5 grayscale" alt="G" />
            Google
          </button>
          <button
            onClick={() => handleOAuth('github')}
            className="flex items-center justify-center gap-2 p-3 bg-white border-4 border-retro-dark rounded-xl shadow-retro-sm hover:bg-gray-50 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all font-display text-sm uppercase"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.421 2.865 8.154 6.839 9.495.5.088.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" /></svg>
            GitHub
          </button>
          <button
            onClick={() => handleOAuth('microsoft')}
            className="flex items-center justify-center gap-2 p-3 bg-white border-4 border-retro-dark rounded-xl shadow-retro-sm hover:bg-gray-50 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all font-display text-sm uppercase"
          >
            <svg className="w-5 h-5" viewBox="0 0 23 23"><path fill="#f3f3f3" d="M0 0h23v23H0z"/><path fill="#f35322" d="M1 1h10v10H1z"/><path fill="#80bb03" d="M12 1h10v10H12z"/><path fill="#00a1f1" d="M1 12h10v10H1z"/><path fill="#ffbb00" d="M12 12h10v10H12z"/></svg>
            Microsoft
          </button>
          <button
            onClick={() => handleOAuth('apple')}
            className="flex items-center justify-center gap-2 p-3 bg-white border-4 border-retro-dark rounded-xl shadow-retro-sm hover:bg-gray-50 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all font-display text-sm uppercase"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 384 512"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 21.8-88.5 21.8-11.4 0-51.1-20.8-82.3-20.2-41.2.8-78.9 24.5-101.4 65.7-47.1 86.2-12 215.1 33.9 285.8 22.5 32.6 49.3 69.8 84.2 68.7 33.2-1.1 45.9-21.1 85.8-21.1 39.9 0 52 21.1 86.1 20.4 34.8-.8 58.3-33.4 80.7-66.1 25.4-37.6 35.8-73.8 36.2-75.6-.7-.3-70.4-27.1-70.1-107.4zM263 75.9c16.4-20.2 27.4-48.2 24.4-75.9-24 1-52.9 16.1-70.1 36.9-15.4 18.5-28.9 47.3-25.3 74.1 26.9 2 54.1-14.9 71-35.1z"/></svg>
            Apple
          </button>
        </div>

        <div className="relative mt-8 mb-4">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t-4 border-retro-dark border-dashed"></div>
          </div>
          <div className="relative flex justify-center text-sm font-display uppercase tracking-widest">
            <span className="bg-white px-6 text-retro-dark italic">OR MANUAL INPUT</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
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
