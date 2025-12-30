import { createFileRoute } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { playlistService, type Track } from '../api/playlist'
import { useState } from 'react'
import { Loader2, X, Music2, Zap } from 'lucide-react'

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
    <div className="space-y-12 max-w-5xl mx-auto px-4">
      {/* Generator Section - styled like an Automat window */}
      <section className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro relative overflow-hidden">
        {/* Machine Head */}
        <div className="absolute top-0 left-0 w-full h-8 bg-retro-teal border-b-4 border-retro-dark flex items-center justify-around px-12">
          <div className="w-3 h-3 rounded-full bg-retro-dark/30"></div>
          <div className="w-3 h-3 rounded-full bg-retro-dark/30"></div>
          <div className="w-3 h-3 rounded-full bg-retro-dark/30"></div>
          <div className="w-3 h-3 rounded-full bg-retro-dark/30"></div>
        </div>

        <div className="flex items-center gap-6 mb-8 mt-6">
          <div className="bg-retro-pink p-4 rounded-2xl border-4 border-retro-dark shadow-retro-sm transform -rotate-3">
            <Music2 className="w-10 h-10 text-retro-dark" />
          </div>
          <div>
            <h2 className="text-5xl font-display text-retro-dark tracking-tighter uppercase italic">
              Vib-O-Matic
            </h2>
            <p className="font-display text-retro-teal text-xl tracking-widest">SERIES 2000 • FULLY AUTOMATED</p>
          </div>
        </div>

        <form onSubmit={handleGenerate} className="space-y-8">
          <div className="space-y-3">
            <label className="block text-2xl font-display text-retro-dark uppercase tracking-wide">
              Enter Desired Vibe
            </label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Midnight coffee in a rainy city"
              className="w-full bg-retro-cream rounded-xl border-4 border-retro-dark p-6 text-2xl placeholder-retro-dark/30 focus:outline-none focus:ring-8 focus:ring-retro-teal/20 shadow-retro-sm transition-all font-body font-bold"
            />
          </div>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full sm:w-auto px-12 py-5 bg-retro-pink hover:bg-pink-400 text-retro-dark text-3xl font-display rounded-2xl border-4 border-retro-dark shadow-retro active:shadow-none active:translate-x-2 active:translate-y-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-4 group"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="animate-spin w-8 h-8" />
                CRUNCHING DATA...
              </>
            ) : (
              <>
                INSERT COIN & START <Zap className="group-hover:fill-retro-yellow transition-colors" />
              </>
            )}
          </button>
        </form>
      </section>

      {generatedTracks.length > 0 && (
        <section className="bg-retro-yellow p-10 rounded-2xl border-8 border-retro-dark shadow-retro animate-in fade-in slide-in-from-bottom-8 duration-700 relative">
          {/* Decorative rivets */}
          <div className="absolute top-6 left-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute top-6 right-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute bottom-6 left-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute bottom-6 right-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>

          <h3 className="text-4xl font-display text-retro-dark mb-8 text-center border-b-4 border-retro-dark pb-6 border-dashed">
            OUTPUT RESULTS
          </h3>

          <div className="bg-white rounded-xl border-4 border-retro-dark overflow-hidden shadow-retro">
            <table className="min-w-full divide-y-4 divide-retro-dark">
              <thead className="bg-retro-teal">
                <tr>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Artist</th>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Track</th>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Version</th>
                  <th className="px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y-4 divide-retro-dark bg-retro-cream">
                {generatedTracks.map((track, i) => (
                  <tr key={i} className="hover:bg-retro-teal/10 transition-colors">
                    <td className="px-6 py-5 text-xl text-retro-dark font-body font-bold border-r-4 border-retro-dark">{track.artist}</td>
                    <td className="px-6 py-5 text-xl text-retro-dark font-body border-r-4 border-retro-dark italic">"{track.track}"</td>
                    <td className="px-6 py-5 text-xl text-retro-dark font-body border-r-4 border-retro-dark">{track.version || 'Original'}</td>
                    <td className="px-6 py-5 text-right">
                      <button className="text-retro-dark hover:text-white hover:bg-retro-pink transition-all p-2 rounded-lg border-2 border-transparent hover:border-retro-dark">
                        <X className="h-8 w-8" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-10 flex justify-center gap-8">
             <button className="px-10 py-4 text-xl font-display text-retro-dark bg-white border-4 border-retro-dark rounded-2xl hover:bg-gray-100 shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase">
               Discard
             </button>
             <button className="px-10 py-4 text-xl font-display text-retro-dark bg-retro-teal border-4 border-retro-dark rounded-2xl hover:bg-teal-400 shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase">
               Save to Service
             </button>
          </div>
        </section>
      )}
    </div>
  )
}
