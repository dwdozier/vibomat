import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

export const Route = createRootRoute({
  component: () => (
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
            <Link
              to="/settings"
              className="font-display text-xl uppercase hover:text-retro-teal [&.active]:text-retro-teal transition-colors"
            >
              Settings
            </Link>
            <Link
              to="/login"
              className="px-8 py-2 rounded-full bg-retro-teal text-retro-dark text-xl font-display uppercase border-4 border-retro-dark hover:bg-retro-pink transition-all shadow-retro-sm active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
            >
              Login
            </Link>
          </div>
        </div>
      </nav>

      <main className="container mx-auto p-12 max-w-7xl">
        <Outlet />
      </main>
      <TanStackRouterDevtools />
    </>
  ),
})
