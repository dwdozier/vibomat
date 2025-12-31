import { createFileRoute, redirect } from '@tanstack/react-router'
import { Settings as SettingsIcon, Link2, Shield, User, Globe, Lock, Trash2, Plus, Disc } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

export const Route = createFileRoute('/settings')({
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
  component: Settings,
})

function Settings() {
  const queryClient = useQueryClient()
  const { context } = Route.useContext()
  const [newArtist, setNewArtist] = useState('')
  const [newAlbum, setNewAlbum] = useState({ name: '', artist: '' })

  const { data: user, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => context.auth.getCurrentUser()
  })

  const updateMutation = useMutation({
    mutationFn: async (updates: Partial<User>) => {
      const res = await fetch('/api/v1/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
    }
  })

  const handleTogglePublic = () => {
    if (user) {
      updateMutation.mutate({ is_public: !user.is_public })
    }
  }

  const handleAddArtist = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newArtist || !user) return
    const artists = [...(user.favorite_artists || []), newArtist]
    updateMutation.mutate({ favorite_artists: artists })
    setNewArtist('')
  }

  const handleRemoveArtist = (artist: string) => {
    if (!user) return
    const artists = (user.favorite_artists || []).filter((a: string) => a !== artist)
    updateMutation.mutate({ favorite_artists: artists })
  }

  const handleAddAlbum = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newAlbum.name || !newAlbum.artist || !user) return
    const albums = [...(user.unskippable_albums || []), newAlbum]
    updateMutation.mutate({ unskippable_albums: albums })
    setNewAlbum({ name: '', artist: '' })
  }

  const handleRemoveAlbum = (index: number) => {
    if (!user) return
    const albums = (user.unskippable_albums || []).filter((_: unknown, i: number) => i !== index)
    updateMutation.mutate({ unskippable_albums: albums })
  }

  if (isLoading) return <div className="p-20 text-center font-display uppercase">Booting Systems...</div>

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-20">
      <div className="flex items-center gap-6">
        <div className="bg-retro-teal p-4 rounded-2xl border-4 border-retro-dark shadow-retro-sm">
          <SettingsIcon className="h-10 w-10 text-retro-dark" />
        </div>
        <div>
          <h2 className="text-4xl font-display text-retro-dark uppercase italic tracking-tight">
            User Settings
          </h2>
          <p className="font-display text-retro-teal text-xl tracking-widest uppercase">Citizen Control Panel</p>
        </div>
      </div>

      {/* Identity & Privacy */}
      <section className="bg-white p-8 rounded-2xl border-8 border-retro-dark shadow-retro">
        <h3 className="text-3xl font-display text-retro-dark mb-8 flex items-center gap-4 uppercase border-b-4 border-retro-dark pb-4 border-dashed">
          <Shield className="h-8 w-8 text-retro-pink" />
          Privacy Shield
        </h3>

        <div className="flex items-center justify-between p-6 bg-retro-cream rounded-xl border-4 border-retro-dark">
          <div className="space-y-1">
            <h4 className="text-2xl font-display text-retro-dark uppercase">Public Profile Broadcast</h4>
            <p className="font-body text-retro-dark/60 italic">Allow other Citizens to view your favorites and archived playlists.</p>
          </div>
          <button
            onClick={handleTogglePublic}
            disabled={updateMutation.isPending}
            className={`px-8 py-3 rounded-xl font-display text-xl uppercase border-4 border-retro-dark transition-all shadow-retro-sm active:shadow-none active:translate-x-1 active:translate-y-1 flex items-center gap-3 ${
              user.is_public ? 'bg-retro-teal hover:bg-teal-400' : 'bg-retro-pink hover:bg-pink-400'
            }`}
          >
            {user.is_public ? (
              <>
                <Globe className="w-6 h-6" /> Public
              </>
            ) : (
              <>
                <Lock className="w-6 h-6" /> Private
              </>
            )}
          </button>
        </div>
      </section>

      {/* Cultural Preferences */}
      <section className="bg-retro-yellow p-8 rounded-2xl border-8 border-retro-dark shadow-retro">
        <h3 className="text-3xl font-display text-retro-dark mb-8 flex items-center gap-4 uppercase border-b-4 border-retro-dark pb-4 border-dashed">
          <User className="h-8 w-8" />
          Citizen Dossier
        </h3>

        <div className="space-y-8">
          <div className="space-y-4">
            <label className="block text-xl font-display text-retro-dark uppercase">Favorite Artists</label>
            <form onSubmit={handleAddArtist} className="flex gap-4">
              <input
                type="text"
                value={newArtist}
                onChange={(e) => setNewArtist(e.target.value)}
                placeholder="Add Artist..."
                className="flex-grow bg-white rounded-xl border-4 border-retro-dark p-4 font-body font-bold focus:outline-none focus:ring-4 focus:ring-retro-teal/20"
              />
              <button type="submit" className="p-4 bg-retro-teal text-retro-dark rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-teal-400">
                <Plus className="w-6 h-6" />
              </button>
            </form>
            <div className="flex flex-wrap gap-3 mt-4">
              {user.favorite_artists?.map((artist: string) => (
                <div key={artist} className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border-2 border-retro-dark font-body font-bold">
                  {artist}
                  <button onClick={() => handleRemoveArtist(artist)} className="text-retro-pink hover:text-red-600">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4 pt-8 border-t-4 border-retro-dark border-dashed">
            <label className="block text-xl font-display text-retro-dark uppercase">Unskippable Albums</label>
            <form onSubmit={handleAddAlbum} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <input
                type="text"
                value={newAlbum.name}
                onChange={(e) => setNewAlbum({ ...newAlbum, name: e.target.value })}
                placeholder="Album Name..."
                className="bg-white rounded-xl border-4 border-retro-dark p-4 font-body font-bold focus:outline-none focus:ring-4 focus:ring-retro-teal/20"
              />
              <div className="flex gap-4">
                <input
                  type="text"
                  value={newAlbum.artist}
                  onChange={(e) => setNewAlbum({ ...newAlbum, artist: e.target.value })}
                  placeholder="Artist..."
                  className="flex-grow bg-white rounded-xl border-4 border-retro-dark p-4 font-body font-bold focus:outline-none focus:ring-4 focus:ring-retro-teal/20"
                />
                <button type="submit" className="p-4 bg-retro-teal text-retro-dark rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-teal-400">
                  <Plus className="w-6 h-6" />
                </button>
              </div>
            </form>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              {user.unskippable_albums?.map((album: any, i: number) => (
                <div key={i} className="flex items-center justify-between bg-white p-4 rounded-lg border-2 border-retro-dark">
                  <div className="flex items-center gap-3">
                    <Disc className="w-6 h-6 text-retro-dark" />
                    <div>
                      <div className="font-body font-bold text-sm leading-tight">{album.name}</div>
                      <div className="text-xs text-retro-dark/60">{album.artist}</div>
                    </div>
                  </div>
                  <button onClick={() => handleRemoveAlbum(i)} className="text-retro-pink hover:text-red-600 p-2">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Connected Services */}
      <section className="bg-white p-8 rounded-2xl border-8 border-retro-dark shadow-retro">
        <h3 className="text-3xl font-display text-retro-dark mb-8 flex items-center gap-4 uppercase border-b-4 border-retro-dark pb-4 border-dashed">
          <Link2 className="h-8 w-8 text-indigo-600" />
          Relay Stations
        </h3>
        <div className="space-y-6">
          <div className="flex items-center justify-between p-6 rounded-xl border-4 border-retro-dark bg-retro-cream shadow-retro-sm">
            <div className="flex items-center gap-6">
              <div className="h-16 w-16 bg-[#1DB954]/20 rounded-full border-2 border-retro-dark flex items-center justify-center">
                <img src="https://www.spotify.com/favicon.ico" className="h-8 w-8" alt="Spotify" />
              </div>
              <div>
                <h4 className="text-2xl font-display text-retro-dark uppercase">Spotify</h4>
                <p className="font-body text-retro-dark/60 italic">High-fidelity playlist broadcasting.</p>
              </div>
            </div>
            <button className="px-8 py-3 bg-retro-teal text-retro-dark font-display text-xl uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-teal-400 transition-all">
              Connect
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
