import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Route } from '../routes/playlists'
import { playlistService, type Track } from '../api/playlist'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock the API service
vi.mock('../api/playlist', () => ({
  playlistService: {
    generate: vi.fn(),
  },
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const PlaylistsComponent = Route.options.component!

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('Playlists Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('renders the AI Generator form', () => {
    renderWithClient(<PlaylistsComponent />)
    expect(screen.getByText('AI Generator')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Late night synthwave/)).toBeInTheDocument()
  })

  it('submits the prompt and shows generated tracks', async () => {
    const mockTracks = [
      { artist: 'The Midnight', track: 'Deep Blue', version: 'studio' }
    ]
    // Use a delayed promise to ensure isPending state is visible
    let resolveMock: (value: Track[]) => void
    const promise = new Promise<Track[]>((resolve) => {
      resolveMock = resolve
    })
    vi.mocked(playlistService.generate).mockReturnValue(promise)

    renderWithClient(<PlaylistsComponent />)

    const input = screen.getByPlaceholderText(/Late night synthwave/)
    fireEvent.change(input, { target: { value: 'Synthwave mood' } })

    const button = screen.getByRole('button', { name: /Generate Playlist/ })
    fireEvent.click(button)

    // Check loading state with waitFor to handle React state updates
    await waitFor(() => {
      expect(button).toBeDisabled()
      expect(screen.getByText(/Generating.../)).toBeInTheDocument()
    })

    // Resolve the promise
    resolveMock!(mockTracks)

    await waitFor(() => {
      expect(screen.getByText('Review Generated Tracks')).toBeInTheDocument()
    })

    expect(screen.getByText('The Midnight')).toBeInTheDocument()
    expect(screen.getByText('Deep Blue')).toBeInTheDocument()
  })

  it('does not submit if prompt is empty', () => {
    renderWithClient(<PlaylistsComponent />)
    const button = screen.getByRole('button', { name: /Generate Playlist/ })
    fireEvent.click(button)
    expect(playlistService.generate).not.toHaveBeenCalled()
  })
})
