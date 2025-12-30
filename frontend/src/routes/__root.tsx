import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { authService } from '../api/auth'
import { useEffect, useState } from 'react'
import { UserCheck } from 'lucide-react'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  const [isAuth, setIsAuth] = useState(false)

  useEffect(() => {
    // Check auth status once on mount
    const checkStatus = async () => {
      const authenticated = await authService.checkAuth()
      setIsAuth(authenticated)
    }

    checkStatus()
  }, [])

  const handleLogout = () => {
    authService.logout()
    setIsAuth(false)
  }

  return (
    <>
      <nav className="p-6 bg-retro-dark text-retro-cream border-b-8 border-retro-teal sticky top-0 z-50 shadow-retro">
        <div className="max-w-7xl mx-auto flex items-center gap-10">
          <Link
            to="/"
            className="font-display text-5xl tracking-widest text-retro-pink transform -rotate-2 hover:rotate-0 transition-transform cursor-pointer drop-shadow-[2px_2px_0px_rgba(0,0,0,1)]"
          >
            VIB-O-MAT
          </Link>
          <div className="flex gap-6 mt-2">
            <Link
              to="/"
              className="px-4 py-2 font-display text-xl uppercase hover:text-retro-teal [&.active]:text-retro-teal transition-colors"
            >
              Home
            </Link>
            <Link
              to="/playlists"
              className="px-4 py-2 font-display text-xl uppercase hover:text-retro-teal [&.active]:text-retro-teal transition-colors"
            >
              Generator
            </Link>
          </div>

          <div className="flex-grow" />

          <div className="flex gap-6 items-center mt-2">
            {isAuth && (
              <div className="flex items-center gap-2 px-4 py-1 bg-retro-teal/20 rounded-lg border-2 border-retro-teal/50 text-retro-teal font-display text-sm tracking-widest uppercase">
                <UserCheck className="w-4 h-4" />
                Verified Citizen
              </div>
            )}
            <Link
              to="/settings"
              className="font-display text-xl uppercase hover:text-retro-teal [&.active]:text-retro-teal transition-colors"
            >
              Settings
            </Link>
            {isAuth ? (
              <button
                onClick={handleLogout}
                className="px-8 py-2 rounded-full bg-retro-pink text-retro-dark text-xl font-display uppercase border-4 border-retro-dark hover:bg-red-400 transition-all shadow-retro-sm active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
              >
                Logout
              </button>
            ) : (
              <Link
                to="/login"
                className="px-8 py-2 rounded-full bg-retro-teal text-retro-dark text-xl font-display uppercase border-4 border-retro-dark hover:bg-retro-pink transition-all shadow-retro-sm active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </nav>

      <main className="container mx-auto p-12 max-w-7xl">
        <Outlet />
      </main>
      <TanStackRouterDevtools />
    </>
  )
}
