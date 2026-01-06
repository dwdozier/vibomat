import { createFileRoute, redirect, Link } from '@tanstack/react-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { User as UserIcon, Music, Disc, Plus, Settings, Edit, Zap, CheckCircle2, Loader2, ExternalLink, Globe } from 'lucide-react'
import { playlistService, type BuildResponse } from '../api/playlist'
import { useState } from 'react'
import { Modal } from '../components/Modal'

export const Route = createFileRoute('/profile/me')({
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
  component: MyProfile,
})

function MyProfile() {
  const { auth } = Route.useRouteContext()
  const queryClient = useQueryClient()
  const [buildResult, setBuildResult] = useState<BuildResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [transmittingId, setTransmittingId] = useState<string | null>(null)

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: () => auth.getCurrentUser()
  })

  const { data: playlists, isLoading } = useQuery({
    queryKey: ['my-playlists'],
    queryFn: playlistService.getMyPlaylists
  })

  const buildMutation = useMutation({
    mutationFn: playlistService.build,
    onSuccess: (data) => {
      setBuildResult(data)
      setIsModalOpen(true)
      setTransmittingId(null)
      queryClient.invalidateQueries({ queryKey: ['my-playlists'] })
    },
    onError: () => {
      setTransmittingId(null)
      alert("Transmission failed. Please check your Relay connection in Settings.")
    }
  })

  const handleTransmit = (id: string) => {
    setTransmittingId(id)
    buildMutation.mutate({ playlist_id: id })
  }

  if (!user) return null

  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-20">
      {/* Header Card */}
      <section className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 flex gap-4">
           <Link
             to="/profile/$identity"
             params={{ identity: user.handle || user.id }}
             className="flex items-center gap-2 text-retro-dark hover:text-retro-teal transition-colors"
           >
             <Globe className="w-6 h-6" />
             <span className="font-display uppercase text-sm tracking-widest hidden sm:inline">Public View</span>
           </Link>
           <Link to="/settings" className="flex items-center gap-2 text-retro-dark hover:text-retro-teal transition-colors">
             <Settings className="w-6 h-6" />
             <span className="font-display uppercase text-sm tracking-widest hidden sm:inline">Settings</span>
           </Link>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-10">
          <div className="w-32 h-32 bg-retro-teal rounded-full border-4 border-retro-dark flex items-center justify-center shadow-retro-sm">
            <UserIcon className="w-16 h-16 text-retro-dark" />
          </div>
          <div className="text-center md:text-left">
            <h2 className="text-5xl font-display text-retro-dark uppercase italic tracking-tighter">
              Citizen {user.display_name}
            </h2>
            {user.handle && (
              <p className="font-display text-retro-dark/40 text-lg uppercase tracking-widest mt-1">
                @{user.handle}
              </p>
            )}
            <p className="font-display text-retro-teal text-xl tracking-widest mt-2 italic">ACCESS LEVEL: CREATOR</p>
          </div>
        </div>
      </section>

      <div className="space-y-8">
        <div className="flex items-center justify-between border-b-4 border-retro-dark pb-4 border-dashed">
            <h3 className="font-display text-4xl text-retro-dark uppercase tracking-tight italic">
              My Archives
            </h3>
            <Link to="/playlists" className="px-6 py-3 bg-retro-teal text-retro-dark font-display text-lg uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all flex items-center gap-2">
                <Plus className="w-6 h-6" /> New Archive
            </Link>
        </div>

        {isLoading ? (
            <div className="text-center py-20">
                <Disc className="animate-spin w-12 h-12 text-retro-dark mx-auto" />
                <p className="mt-4 font-display text-retro-dark uppercase">Retrieving Records...</p>
            </div>
        ) : (playlists?.length ?? 0) > 0 ? (
            <div className="grid grid-cols-1 gap-6">
                {playlists?.map((playlist) => (
                    <div key={playlist.id} className="bg-white p-6 rounded-xl border-4 border-retro-dark shadow-retro-sm hover:shadow-retro transition-all group">
                        <div className="flex flex-col md:flex-row justify-between gap-6">
                            <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                    <h4 className="text-2xl font-display text-retro-dark uppercase group-hover:text-retro-teal transition-colors">
                                        {playlist.name}
                                    </h4>
                                    {playlist.status === 'draft' && (
                                        <span className="px-2 py-1 bg-retro-cream border-2 border-retro-dark text-xs font-bold font-display uppercase tracking-wider rounded">
                                            Draft
                                        </span>
                                    )}
                                    {playlist.status === 'transmitted' && (
                                        <span className="px-2 py-1 bg-retro-teal text-retro-dark border-2 border-retro-dark text-xs font-bold font-display uppercase tracking-wider rounded flex items-center gap-1">
                                            <CheckCircle2 className="w-3 h-3" /> Live
                                        </span>
                                    )}
                                </div>
                                <p className="text-retro-dark/60 font-body italic max-w-2xl">
                                    {playlist.description || "No description provided."}
                                </p>
                                <div className="flex gap-4 text-xs font-display uppercase tracking-widest text-retro-dark/40">
                                    <span>{playlist.content_json?.tracks?.length || 0} Tracks</span>
                                    <span>•</span>
                                    <span>{playlist.public ? 'Public' : 'Private'}</span>
                                </div>
                            </div>

                            <div className="flex items-center gap-3">
                                <Link
                                    to="/playlists"
                                    search={{ edit: playlist.id }}
                                    className="px-4 py-2 bg-retro-cream text-retro-dark font-display rounded-lg border-2 border-retro-dark hover:bg-white transition-all uppercase text-sm flex items-center gap-2"
                                >
                                    <Edit className="w-4 h-4" /> Edit
                                </Link>
                                {playlist.status === 'draft' && (
                                    <button
                                      onClick={() => handleTransmit(playlist.id)}
                                      disabled={transmittingId === playlist.id}
                                      className="px-4 py-2 bg-retro-pink text-retro-dark font-display rounded-lg border-2 border-retro-dark hover:bg-pink-400 transition-all uppercase text-sm flex items-center gap-2 disabled:opacity-50"
                                    >
                                        {transmittingId === playlist.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                                        {transmittingId === playlist.id ? 'Sending...' : 'Transmit'}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        ) : (
            <div className="bg-white/50 p-12 rounded-xl border-4 border-retro-dark border-dashed text-center">
                <Music className="w-16 h-16 text-retro-dark/20 mx-auto mb-4" />
                <h4 className="text-2xl font-display text-retro-dark uppercase mb-2">No Archives Found</h4>
                <p className="font-body text-retro-dark/60 mb-6">You haven't generated any playlists yet.</p>
                <Link to="/playlists" className="inline-block px-8 py-3 bg-retro-teal text-retro-dark font-display uppercase rounded-xl border-4 border-retro-dark hover:bg-teal-400 transition-all">
                    Start the Vib-O-Matic
                </Link>
            </div>
        )}
      </div>

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
                Your playlist has been successfully broadcasted.
              </p>
            </div>

            <div className="pt-4">
              <a
                href={buildResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-3 px-10 py-4 bg-retro-teal text-retro-dark font-display text-2xl uppercase rounded-2xl border-4 border-retro-dark shadow-retro hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all"
              >
                Open in Spotify <ExternalLink className="w-6 h-6" />
              </a>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
