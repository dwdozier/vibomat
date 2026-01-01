import { createRootRouteWithContext, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { authService } from '../api/auth'
import { UserCheck, Settings, User, LogOut, ShieldAlert, Cpu } from 'lucide-react'

interface MyRouterContext {
  auth: typeof authService
}

export const Route = createRootRouteWithContext<MyRouterContext>()({
  loader: async ({ context }) => {
    const user = await context.auth.getCurrentUser()
    return { user }
  },
  component: RootLayout,
})

function RootLayout() {
  const { user } = Route.useLoaderData()
  const isAuth = !!user

  const handleLogout = () => {
    authService.logout()
  }

  return (
    <>
      <nav className="p-6 bg-retro-dark text-retro-cream border-b-8 border-retro-teal sticky top-0 z-50 shadow-retro">
        <div className="max-w-7xl mx-auto flex items-center gap-8">
          {/* Brand - The heart of the machine */}
          <Link
            to="/"
            data-play="nav-brand"
            className="font-display text-5xl tracking-widest text-retro-pink transform -rotate-2 hover:rotate-0 transition-transform cursor-pointer drop-shadow-[2px_2px_0px_rgba(0,0,0,1)] flex items-center gap-3"
          >
            VIB-O-MAT
          </Link>

          {/* Primary Operations */}
          {isAuth && (
            <div className="flex gap-4 items-center border-l-4 border-retro-teal/30 pl-8 h-12 mt-2">
              <Link
                to="/playlists"
                data-play="nav-generator"
                className="flex items-center gap-2 px-4 py-2 font-display text-xl uppercase hover:text-retro-teal [&.active]:text-retro-teal [&.active]:bg-retro-teal/10 rounded-lg transition-all"
              >
                <Cpu className="w-5 h-5" />
                Generator
              </Link>
            </div>
          )}

          <div className="flex-grow" />

          {/* Citizen/Admin Modules */}
          <div className="flex gap-6 items-center mt-2">
            {isAuth ? (
              <>
                {/* Identity Card */}
                <div className="flex items-center gap-1 bg-retro-teal/10 rounded-2xl border-4 border-retro-dark p-1 pr-4 shadow-retro-sm">
                  <Link
                    to="/profile/$userId"
                    params={{ userId: user.id }}
                    data-play="nav-profile"
                    className="flex items-center gap-2 px-3 py-1 bg-retro-teal text-retro-dark rounded-xl font-display text-sm uppercase hover:bg-teal-400 transition-colors"
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </Link>
                  <div className="flex items-center gap-2 pl-3 text-retro-teal font-display text-xs tracking-widest uppercase opacity-80">
                    <UserCheck className="w-4 h-4" />
                    Verified
                  </div>
                </div>

                {/* System Controls */}
                <div className="flex items-center gap-4 border-l-2 border-retro-teal/20 pl-6 ml-2">
                  {user?.is_superuser && (
                    <Link
                      to="/admin"
                      data-play="nav-admin"
                      className="flex items-center gap-2 px-4 py-2 bg-retro-yellow text-retro-dark font-display text-sm uppercase rounded-xl border-2 border-retro-dark hover:bg-yellow-400 transition-all shadow-retro-xs active:shadow-none translate-y-[-1px] active:translate-y-[1px]"
                    >
                      <ShieldAlert className="w-4 h-4" />
                      Admin
                    </Link>
                  )}

                  <Link
                    to="/settings"
                    data-play="nav-settings"
                    className="text-retro-cream hover:text-retro-teal transition-colors p-2 hover:bg-retro-teal/10 rounded-full"
                    title="Control Panel"
                  >
                    <Settings className="w-6 h-6" />
                  </Link>

                  <button
                    onClick={handleLogout}
                    data-play="nav-logout"
                    className="flex items-center gap-2 px-6 py-2 rounded-full bg-retro-pink text-retro-dark text-lg font-display uppercase border-4 border-retro-dark hover:bg-red-400 transition-all shadow-retro-sm active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
                  >
                    <LogOut className="w-5 h-5" />
                    Exit
                  </button>
                </div>
              </>
            ) : (
              <Link
                to="/login"
                data-play="nav-login"
                className="px-10 py-3 rounded-full bg-retro-teal text-retro-dark text-2xl font-display uppercase border-4 border-retro-dark hover:bg-retro-pink transition-all shadow-retro-sm active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
              >
                Identification Login
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
