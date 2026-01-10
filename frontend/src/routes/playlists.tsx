import { createFileRoute, redirect, useNavigate } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { playlistService, type Track, type BuildResponse, type PlaylistGenerationResponse, type Playlist } from '../api/playlist'
import { useState, useEffect } from 'react'
import { Loader2, X, Music2, Zap, CheckCircle2, ExternalLink, Save } from 'lucide-react'
import { Modal } from '../components/Modal'
import { z } from 'zod'

// Helper to format milliseconds to MM:SS or HH:MM:SS
const formatDuration = (ms?: number) => {
  if (!ms) return '--:--'
  const seconds = Math.floor((ms / 1000) % 60)
  const minutes = Math.floor((ms / (1000 * 60)) % 60)
  const hours = Math.floor(ms / (1000 * 60 * 60))

  const parts = []
  if (hours > 0) parts.push(hours.toString().padStart(2, '0'))
  parts.push(minutes.toString().padStart(2, '0'))
  parts.push(seconds.toString().padStart(2, '0'))
  return parts.join(':')
}

const playlistsSearchSchema = z.object({
  edit: z.string().optional(),
})

export const Route = createFileRoute('/playlists')({
  validateSearch: playlistsSearchSchema,
  beforeLoad: async ({ context, location }) => {
    const user = await context.auth.getCurrentUser()
    if (!user) {
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      })
    }
  },
  component: Playlists,
})

function Playlists() {
  const navigate = useNavigate()
  const search = Route.useSearch()
  const queryClient = useQueryClient()

  const [prompt, setPrompt] = useState('')
  const [generatedPlaylist, setGeneratedPlaylist] = useState<PlaylistGenerationResponse | null>(null)
  const [savedDraft, setSavedDraft] = useState<Playlist | null>(null)
  const [buildResult, setBuildResult] = useState<BuildResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Fetch playlist for editing
  const { data: existingPlaylist } = useQuery({
    queryKey: ['playlist', search.edit],
    queryFn: () => playlistService.getPlaylist(search.edit!),
    enabled: !!search.edit,
  })

  // Populate state when existing playlist is loaded
  useEffect(() => {
    if (existingPlaylist) {
        setSavedDraft(existingPlaylist)
        setGeneratedPlaylist({
            title: existingPlaylist.name,
            description: existingPlaylist.description || "",
            tracks: existingPlaylist.content_json.tracks
        })
        setPrompt(existingPlaylist.name.replace("AI: ", "").replace("...", ""))
    }
  }, [existingPlaylist])

  const generateMutation = useMutation({
    mutationFn: playlistService.generate,
    onSuccess: (data) => {
      setGeneratedPlaylist(data)
      // If we are editing, we keep the savedDraft reference to update it later
      // unless user wants to treat this as a totally new thing?
      // Let's assume re-generating overwrites the draft content in UI but keeps ID linkage
    },
  })

  const saveMutation = useMutation({
    mutationFn: playlistService.create,
    onSuccess: (data) => {
      setSavedDraft(data)
      queryClient.invalidateQueries({ queryKey: ['my-playlists'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (vars: {id: string, data: any}) => playlistService.update(vars.id, vars.data),
    onSuccess: (data) => {
      setSavedDraft(data)
      queryClient.invalidateQueries({ queryKey: ['my-playlists'] })
    }
  })

  const buildMutation = useMutation({
    mutationFn: playlistService.build,
    onSuccess: (data) => {
      setBuildResult(data)
      setIsModalOpen(true)
      queryClient.invalidateQueries({ queryKey: ['my-playlists'] })
    },
  })

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt) return
    generateMutation.mutate({ prompt })
  }

  const handleRemoveTrack = (index: number) => {
    if (!generatedPlaylist) return
    const newTracks = generatedPlaylist.tracks.filter((_, i) => i !== index)
    setGeneratedPlaylist({ ...generatedPlaylist, tracks: newTracks })
  }

  const handleDiscard = () => {
    setGeneratedPlaylist(null)
    setSavedDraft(null)
    setPrompt('')
    navigate({ to: '/playlists', search: {} }) // Clear edit param
  }

  const handleSaveDraft = () => {
    if (!generatedPlaylist) return

    const payload = {
      name: generatedPlaylist.title,
      description: generatedPlaylist.description,
      public: false,
      tracks: generatedPlaylist.tracks,
    }

    if (savedDraft) {
        updateMutation.mutate({ id: savedDraft.id, data: payload })
    } else {
        saveMutation.mutate(payload)
    }
  }

  const handleTransmit = async () => {
    if (!generatedPlaylist) return

    // If already saved (or editing), ensure it's up to date then build
    if (savedDraft) {
      // Should we update first? Probably safer.
      try {
          await updateMutation.mutateAsync({
              id: savedDraft.id,
              data: {
                name: generatedPlaylist.title,
                description: generatedPlaylist.description,
                public: false,
                tracks: generatedPlaylist.tracks,
              }
          })
          buildMutation.mutate({ playlist_id: savedDraft.id })
      } catch(e) {
          console.error("Update failed before transmit", e)
      }
      return
    }

    // Otherwise create then build
    try {
      const draft = await saveMutation.mutateAsync({
        name: generatedPlaylist.title,
        description: generatedPlaylist.description,
        public: false,
        tracks: generatedPlaylist.tracks,
      })
      buildMutation.mutate({ playlist_id: draft.id })
    } catch (e) {
      console.error("Failed to auto-save before transmit", e)
    }
  }

  const isSaving = saveMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-12 max-w-5xl mx-auto px-4 pb-20">
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

        <div className="mb-10 p-6 bg-retro-cream/50 rounded-xl border-4 border-retro-dark border-dashed space-y-4">
          <p className="font-body text-xl text-retro-dark font-bold leading-relaxed">
            Welcome, Citizen. The <span className="text-retro-pink">Vib-O-Matic</span> uses advanced social-synthesis AI to curate high-fidelity playlists. Simply describe your desired mood, activity, or theme below.
          </p>

          <div className="grid md:grid-cols-2 gap-6 pt-2">
            <div className="space-y-2">
              <span className="font-display text-sm uppercase tracking-widest text-retro-teal">Simple Transmission</span>
              <p className="font-body text-sm italic text-retro-dark/70">"A 90s alternative rock workout."</p>
            </div>
            <div className="space-y-2">
              <span className="font-display text-sm uppercase tracking-widest text-retro-pink">Complex Broadcast</span>
              <p className="font-body text-sm italic text-retro-dark/70">"Melancholic jazz for a lonely rainy night in Tokyo, featuring saxophone and piano, no vocals."</p>
            </div>
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
            disabled={generateMutation.isPending}
            className="w-full sm:w-auto px-12 py-5 bg-retro-pink hover:bg-pink-400 text-retro-dark text-3xl font-display rounded-2xl border-4 border-retro-dark shadow-retro active:shadow-none active:translate-x-2 active:translate-y-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-4 group"
          >
            {generateMutation.isPending ? (
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

      {generatedPlaylist && (
        <section className="bg-retro-yellow p-10 rounded-2xl border-8 border-retro-dark shadow-retro animate-in fade-in slide-in-from-bottom-8 duration-700 relative">
          {/* Decorative rivets */}
          <div className="absolute top-6 left-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute top-6 right-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute bottom-6 left-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>
          <div className="absolute bottom-6 right-6 w-4 h-4 rounded-full bg-retro-dark opacity-30 shadow-inner"></div>

          <div className="mb-8 border-b-4 border-retro-dark pb-6 border-dashed">
            <div className="flex justify-between items-start gap-4 mb-4">
                <div>
                    <h3 className="text-4xl font-display text-retro-dark uppercase leading-tight">
                    {generatedPlaylist.title}
                    </h3>
                    <p className="text-xl font-body text-retro-dark/70 italic mt-2">
                        {generatedPlaylist.description}
                    </p>
                </div>
                <div className="bg-retro-dark text-retro-teal px-4 py-2 rounded-lg font-display text-lg shadow-retro-xs whitespace-nowrap">
                {formatDuration(generatedPlaylist.tracks?.reduce((acc: number, t: Track) => acc + (t.duration_ms || 0), 0) || 0)}
                </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border-4 border-retro-dark overflow-hidden shadow-retro">
            <table className="min-w-full divide-y-4 divide-retro-dark">
              <thead className="bg-retro-teal">
                <tr>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Artist</th>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Track</th>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Duration</th>
                  <th className="px-6 py-4 text-left text-lg font-display text-retro-dark uppercase tracking-widest border-r-4 border-retro-dark">Version</th>
                  <th className="px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y-4 divide-retro-dark bg-retro-cream">
                {(generatedPlaylist.tracks || []).map((track: Track, i: number) => (
                  <tr key={i} className="hover:bg-retro-teal/10 transition-colors">
                    <td className="px-6 py-5 text-xl text-retro-dark font-body font-bold border-r-4 border-retro-dark">{track.artist}</td>
                    <td className="px-6 py-5 text-xl text-retro-dark font-body border-r-4 border-retro-dark italic">"{track.track}"</td>
                    <td className="px-6 py-5 text-xl text-retro-dark font-body border-r-4 border-retro-dark">{formatDuration(track.duration_ms)}</td>
                    <td className="px-6 py-5 text-xl text-retro-dark font-body border-r-4 border-retro-dark">{track.version || 'Original'}</td>
                    <td className="px-6 py-5 text-right">
                      <button
                        onClick={() => handleRemoveTrack(i)}
                        className="text-retro-dark hover:text-white hover:bg-retro-pink transition-all p-2 rounded-lg border-2 border-transparent hover:border-retro-dark"
                      >
                        <X className="h-8 w-8" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-10 flex flex-col md:flex-row justify-center gap-6">
             <button
               onClick={handleDiscard}
               className="px-8 py-4 text-xl font-display text-retro-dark bg-white border-4 border-retro-dark rounded-2xl hover:bg-gray-100 shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase"
             >
               Discard
             </button>

                          <button
                            onClick={handleSaveDraft}
                            disabled={isSaving || (!!savedDraft && savedDraft.status !== 'draft')}
                            className={`px-8 py-4 text-xl font-display border-4 border-retro-dark rounded-2xl shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase flex items-center gap-3 justify-center ${
                                (savedDraft && !isSaving)
                                ? 'bg-retro-cream text-retro-dark/50'
                                : 'bg-retro-teal text-retro-dark hover:bg-teal-400'
                            }`}
                          >
                            {isSaving ? (
                                <>
                                 <Loader2 className="animate-spin w-6 h-6" /> Saving...
                                </>
                            ) : savedDraft ? (
                                <>
                                 <CheckCircle2 className="w-6 h-6" /> Saved
                                </>
                            ) : (
                                <>
                                 <Save className="w-6 h-6" /> Save Draft
                                </>
                            )}
                          </button>
                          <button
               onClick={handleTransmit}
               disabled={buildMutation.isPending}
               className="px-8 py-4 text-xl font-display text-retro-dark bg-retro-pink border-4 border-retro-dark rounded-2xl hover:bg-pink-400 shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase flex items-center gap-3 justify-center disabled:opacity-50"
             >
               {buildMutation.isPending ? (
                 <>
                   <Loader2 className="animate-spin w-6 h-6" />
                   TRANSMITTING...
                 </>
               ) : (
                 <>
                   <Zap className="w-6 h-6 fill-retro-dark" /> Transmit to Spotify
                 </>
               )}
             </button>
          </div>
        </section>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Transmission Successful"
      >
        {buildResult && (
          <div className="space-y-8 text-center py-4">
            <div className="flex justify-center">
              <div className="bg-retro-teal/20 p-6 rounded-full border-4 border-retro-dark shadow-retro-sm">
                <CheckCircle2 className="w-16 h-16 text-retro-teal" />
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-3xl font-display text-retro-dark uppercase">Archives Updated</h4>
              <p className="font-body text-xl text-retro-dark/70 italic leading-relaxed">
                Your playlist has been successfully compiled and broadcasted to your Spotify account.
              </p>
            </div>

            {buildResult.failed_tracks.length > 0 && (
              <div className="p-4 bg-retro-pink/10 border-4 border-retro-pink rounded-xl text-left">
                <h5 className="font-display text-retro-dark uppercase mb-2 text-sm">Degraded Signals:</h5>
                <ul className="text-xs font-body space-y-1 text-retro-dark/60">
                  {buildResult.failed_tracks.map((t, i) => (
                    <li key={i}>• {t} (Signal lost during search)</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="pt-4 flex flex-col gap-4">
              <a
                href={buildResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-3 px-10 py-4 bg-retro-teal text-retro-dark font-display text-2xl uppercase rounded-2xl border-4 border-retro-dark shadow-retro hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all"
              >
                Open in Spotify <ExternalLink className="w-6 h-6" />
              </a>
              <button
                onClick={() => {
                    setIsModalOpen(false)
                    handleDiscard()
                    navigate({ to: '/profile/$identity', params: { identity: 'me' } })
                }}
                className="text-retro-dark underline font-display uppercase tracking-widest hover:text-retro-teal"
              >
                Return to Generator
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
