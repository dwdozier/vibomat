import { createFileRoute } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { playlistService, type Track } from '../api/playlist'
import { useState } from 'react'
import { Loader2, X } from 'lucide-react'

export const Route = createFileRoute('/playlists')({
  component: Playlists,
})

function Playlists() {
  const [prompt, setPrompt] = useState('')
  const [generatedTracks, setGeneratedTracks] = useState<Track[]>([])

  const mutation = useMutation({
    mutationFn: playlistService.generate,
    onSuccess: (data) => {
      setGeneratedTracks(data)
    },
  })

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt) return
    mutation.mutate({ prompt })
  }

  return (
    <div className="space-y-8">
      <section className="bg-white p-6 rounded-lg shadow-md border border-slate-200">
        <h2 className="text-2xl font-bold mb-4">AI Generator</h2>
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Mood or Theme
            </label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Late night synthwave coding session"
              className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-2 border"
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                Generating...
              </>
            ) : (
              'Generate Playlist'
            )}
          </button>
        </form>
      </section>

      {generatedTracks.length > 0 && (
        <section className="bg-white p-6 rounded-lg shadow-md border border-slate-200 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <h3 className="text-xl font-semibold mb-4">Review Generated Tracks</h3>
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
            <table className="min-w-full divide-y divide-slate-300">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Artist</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Track</th>
                  <th className="px-3 py-3.5 text-left text-sm font-semibold text-slate-900">Version</th>
                  <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {generatedTracks.map((track, i) => (
                  <tr key={i}>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{track.artist}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{track.track}</td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-slate-500">{track.version || 'studio'}</td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <button className="text-red-600 hover:text-red-900 ml-4">
                        <X className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-6 flex justify-end gap-4">
             <button className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50">
               Discard
             </button>
             <button className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 shadow-sm">
               Save to My Playlists
             </button>
          </div>
        </section>
      )}
    </div>
  )
}
