import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { authService } from './api/auth'
import './index.css'

// Import the generated route tree
import { routeTree } from './routeTree.gen'

const queryClient = new QueryClient()

// Create a new router instance
const router = createRouter({
  routeTree,
  context: {
    auth: undefined! // We'll inject this in the RouterProvider
  }
})

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} context={{ auth: authService }} />
    </QueryClientProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
