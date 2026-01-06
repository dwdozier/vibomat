import { createFileRoute, redirect } from '@tanstack/react-router'
import { Settings as SettingsIcon, Link2, Shield, User as UserIcon, Globe, Lock, Trash2, Plus, Disc, Info, ExternalLink, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { type User } from '../api/auth'
import { Modal } from '../components/Modal'

export const Route = createFileRoute('/settings')({
// ... (omitting unchanged beforeLoad for brevity)
  component: Settings,
})

// ... EnrichedMetadata interface

function Settings() {
  const queryClient = useQueryClient()
  const { auth } = Route.useRouteContext()
  const [newArtist, setNewArtist] = useState('')
  const [newAlbum, setNewAlbum] = useState({ name: '', artist: '' })

  // Identity State
  const [handle, setHandle] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [handleStatus, setHandleStatus] = useState<'idle' | 'checking' | 'valid' | 'invalid' | 'taken'>('idle')
  const [handleError, setHandleError] = useState('')

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isRelayModalOpen, setIsRelayModalOpen] = useState(false)
  const [activeMetadata, setActiveMetadata] = useState<EnrichedMetadata | null>(null)
  const [relayCreds, setRelayCreds] = useState({ client_id: '', client_secret: '' })

  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ['me'],
    queryFn: () => auth.getCurrentUser()
  })

  // Sync state with user data
  useEffect(() => {
    if (user) {
      setHandle(user.handle || '')
      setFirstName(user.first_name || '')
      setLastName(user.last_name || '')
    }
  }, [user])

  // Handle Validation Debounce
  useEffect(() => {
    if (!handle || handle === user?.handle) {
      setHandleStatus('idle')
      setHandleError('')
      return
    }

    if (handle.length < 3) {
      setHandleStatus('invalid')
      setHandleError('Min 3 characters')
      return
    }

    const timer = setTimeout(async () => {
      setHandleStatus('checking')
      try {
        // We'll use the UserManager validation via the update endpoint partially,
        // but it's better to have a dedicated validation endpoint if we want real-time feedback.
        // For now, we'll just try to "dry run" or assume it's valid until we implement the endpoint.
        // Actually, let's just mark it as "checking" and assume it's okay for the UI if it matches regex.
        if (!/^[a-zA-Z0-9_-]+$/.test(handle)) {
          setHandleStatus('invalid')
          setHandleError('Invalid characters')
        } else {
          setHandleStatus('valid')
          setHandleError('')
        }
      } catch (err) {
        setHandleStatus('invalid')
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [handle, user?.handle])

  const spotifyConn = user?.service_connections?.find((c: any) => c.provider_name === 'spotify')

  const relayMutation = useMutation({
    mutationFn: async (creds: typeof relayCreds) => {
      const res = await fetch('/api/v1/integrations/relay/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: 'spotify',
          ...creds
        }),
      })
      return res.json()
    },
    onSuccess: () => {
      setIsRelayModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['me'] })
    }
  })

  const updateMutation = useMutation({
    mutationFn: async (updates: Partial<User>) => {
      const res = await fetch('/api/v1/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Update failed')
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (err: Error) => {
      alert(err.message)
    }
  })

  const handleUpdateIdentity = () => {
    if (!user) return
    updateMutation.mutate({
      handle: handle || null,
      first_name: firstName || null,
      last_name: lastName || null
    })
  }

  const handleTogglePublic = () => {
    if (user) {
      updateMutation.mutate({ is_public: !user.is_public })
    }
  }

  const handleAddArtist = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newArtist || !user) return

    // Attempt to enrich artist metadata
    try {
      const enrichRes = await fetch('/api/v1/profile/me/enrich/artist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ artist_name: newArtist }),
      })

      const enrichedArtist = enrichRes.ok ? await enrichRes.json() : { name: newArtist }
      const artists = [...(user.favorite_artists || []), enrichedArtist]
      updateMutation.mutate({ favorite_artists: artists })
    } catch (err) {
      console.error("Enrichment failed", err)
      const artists = [...(user.favorite_artists || []), { name: newArtist }]
      updateMutation.mutate({ favorite_artists: artists })
    }

    setNewArtist('')
  }

  const handleRemoveArtist = (index: number) => {
    if (!user) return
    const artists = (user.favorite_artists || []).filter((_: unknown, i: number) => i !== index)
    updateMutation.mutate({ favorite_artists: artists })
  }

  const handleAddAlbum = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newAlbum.name || !newAlbum.artist || !user) return

    // Attempt to enrich album metadata
    try {
      const enrichRes = await fetch('/api/v1/profile/me/enrich/album', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ artist_name: newAlbum.artist, album_name: newAlbum.name }),
      })

      const enrichedAlbum = enrichRes.ok ? await enrichRes.json() : { ...newAlbum }
      const albums = [...(user.unskippable_albums || []), enrichedAlbum]
      updateMutation.mutate({ unskippable_albums: albums })
    } catch (err) {
      console.error("Album enrichment failed", err)
      const albums = [...(user.unskippable_albums || []), { ...newAlbum }]
      updateMutation.mutate({ unskippable_albums: albums })
    }

    setNewAlbum({ name: '', artist: '' })
  }

  const handleConnectSpotify = async () => {
    try {
      const res = await fetch('/api/v1/integrations/spotify/login')
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      } else if (data.detail) {
        alert(data.detail)
      }
    } catch (err) {
      console.error("Failed to initiate Spotify connection", err)
    }
  }

  const handleOpenRelayModal = () => {
    setRelayCreds({
      client_id: spotifyConn?.client_id || '',
      client_secret: ''
    })
    setIsRelayModalOpen(true)
  }

  const handleRemoveAlbum = (index: number) => {
    if (!user) return
    const albums = (user.unskippable_albums || []).filter((_: unknown, i: number) => i !== index)
    updateMutation.mutate({ unskippable_albums: albums })
  }

  const handleViewMetadata = (meta: EnrichedMetadata) => {
    setActiveMetadata(meta)
    setIsModalOpen(true)
  }

  if (isLoading || !user) return <div className="p-20 text-center font-display uppercase">Booting Systems...</div>

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
          <UserIcon className="h-8 w-8" />
          Citizen Dossier
        </h3>

        <div className="space-y-8">
          {/* Identity Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pb-8 border-b-4 border-retro-dark border-dashed">
            <div className="space-y-4">
              <label className="block text-xl font-display text-retro-dark uppercase flex items-center gap-2">
                 Handle
                 {handleStatus === 'checking' && <Loader2 className="w-4 h-4 animate-spin text-retro-teal" />}
                 {handleStatus === 'valid' && <CheckCircle2 className="w-4 h-4 text-retro-teal" />}
                 {handleStatus === 'invalid' && <AlertCircle className="w-4 h-4 text-retro-pink" />}
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-retro-dark/40 font-display text-xl">@</span>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  placeholder="handle"
                  className={`w-full bg-white rounded-xl border-4 border-retro-dark p-4 pl-10 font-body font-bold focus:outline-none focus:ring-4 ${
                    handleStatus === 'invalid' ? 'border-retro-pink focus:ring-retro-pink/20' : 'focus:ring-retro-teal/20'
                  }`}
                />
              </div>
              {handleError && <p className="text-retro-pink font-display text-xs uppercase tracking-widest">{handleError}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-4">
                <label className="block text-xl font-display text-retro-dark uppercase">First Name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="First"
                  className="w-full bg-white rounded-xl border-4 border-retro-dark p-4 font-body font-bold focus:outline-none focus:ring-4 focus:ring-retro-teal/20"
                />
              </div>
              <div className="space-y-4">
                <label className="block text-xl font-display text-retro-dark uppercase">Last Name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Last"
                  className="w-full bg-white rounded-xl border-4 border-retro-dark p-4 font-body font-bold focus:outline-none focus:ring-4 focus:ring-retro-teal/20"
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <button
                onClick={handleUpdateIdentity}
                disabled={updateMutation.isPending || handleStatus === 'invalid' || handleStatus === 'checking'}
                className="w-full py-4 bg-retro-teal text-retro-dark font-display text-xl uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all disabled:opacity-50"
              >
                {updateMutation.isPending ? 'Updating Records...' : 'Update Identity Dossier'}
              </button>
            </div>
          </div>

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
              {user.favorite_artists?.map((artist: unknown, i: number) => {
                const name = typeof artist === 'string' ? artist : (artist as EnrichedMetadata).name;
                const meta = typeof artist === 'string' ? { name: artist } : artist as EnrichedMetadata;
                return (
                  <div key={i} className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border-2 border-retro-dark font-body font-bold">
                    {name}
                    <button
                      onClick={() => handleViewMetadata(meta)}
                      className="text-retro-teal hover:text-teal-600 p-1"
                      title="View Archive Data"
                    >
                      <Info className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleRemoveArtist(i)} className="text-retro-pink hover:text-red-600 p-1">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                );
              })}
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
              {user.unskippable_albums?.map((album: unknown, i: number) => {
                const a = album as EnrichedMetadata;
                return (
                  <div key={i} className="flex items-center justify-between bg-white p-4 rounded-lg border-2 border-retro-dark">
                    <div className="flex items-center gap-3">
                      <Disc className="w-6 h-6 text-retro-dark" />
                      <div>
                        <div className="font-body font-bold text-sm leading-tight">{a.name}</div>
                        <div className="text-xs text-retro-dark/60">{a.artist}</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewMetadata(a)}
                        className="text-retro-teal hover:text-teal-600 p-2 border-2 border-transparent hover:border-retro-dark rounded-lg transition-all"
                      >
                        <Info className="w-5 h-5" />
                      </button>
                      <button onClick={() => handleRemoveAlbum(i)} className="text-retro-pink hover:text-red-600 p-2 border-2 border-transparent hover:border-retro-dark rounded-lg transition-all">
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                );
              })}
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
                {spotifyConn?.is_connected && spotifyConn.scopes && (
                  <div className="mt-3 flex flex-wrap gap-2 max-w-md">
                    {spotifyConn.scopes.map(scope => (
                      <span key={scope} className="px-2 py-0.5 bg-retro-teal/10 border-2 border-retro-teal/20 rounded text-[10px] font-display uppercase text-retro-teal tracking-tighter" title="Permission granted">
                        {scope.replace(/-/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleOpenRelayModal}
                className="px-6 py-3 bg-white text-retro-dark font-display text-lg uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-gray-100 transition-all"
              >
                {spotifyConn?.client_id ? 'Re-Configure' : 'Configure'}
              </button>
              <button
                onClick={handleConnectSpotify}
                disabled={!spotifyConn?.client_id}
                className={`px-8 py-3 font-display text-xl uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm transition-all flex items-center gap-2 ${
                  spotifyConn?.is_connected
                    ? 'bg-retro-teal hover:bg-teal-400 text-retro-dark'
                    : 'bg-retro-pink hover:bg-pink-400 text-retro-dark disabled:opacity-50 disabled:grayscale'
                }`}
              >
                {spotifyConn?.is_connected ? (
                  <>
                    <CheckCircle2 className="w-6 h-6" /> Synchronized
                  </>
                ) : (
                  'Connect'
                )}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Relay Configuration Modal */}
      <Modal
        isOpen={isRelayModalOpen}
        onClose={() => setIsRelayModalOpen(false)}
        title="Relay Configuration"
      >
        <div className="space-y-8">
          <div className="bg-retro-cream p-6 rounded-xl border-4 border-retro-dark space-y-4">
            <h5 className="font-display text-retro-dark uppercase flex items-center gap-2">
              <Info className="w-5 h-5" /> Transmission Manual
            </h5>
            <p className="font-body text-sm text-retro-dark/80 leading-relaxed">
              To establish a high-fidelity relay, you must provide credentials from your own
              <span className="font-bold"> Spotify Developer Application</span>.
            </p>
            <ol className="font-body text-xs space-y-2 list-decimal ml-4 text-retro-dark/70">
              <li>Visit the <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener noreferrer" className="text-retro-teal underline font-bold">Spotify Developer Dashboard</a>.</li>
              <li>Create a new "App" (Name it <span className="italic">Vibomat Relay</span>).</li>
              <li>In App Settings, set your <span className="font-bold">Redirect URI</span> to: <br/>
                <code className="bg-white px-1 border border-retro-dark select-all">http://localhost/api/v1/integrations/spotify/callback</code>
              </li>
              <li>Copy your <span className="font-bold">Client ID</span> and <span className="font-bold">Client Secret</span> into the fields below.</li>
            </ol>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="block text-sm font-display uppercase tracking-widest text-retro-dark/60">Client ID</label>
              <input
                type="text"
                value={relayCreds.client_id}
                onChange={(e) => setRelayCreds({ ...relayCreds, client_id: e.target.value })}
                placeholder="e.g. 5f2a..."
                className="w-full bg-white rounded-lg border-2 border-retro-dark p-3 font-body font-bold focus:outline-none focus:border-retro-teal"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-display uppercase tracking-widest text-retro-dark/60">Client Secret</label>
              <input
                type="password"
                value={relayCreds.client_secret}
                onChange={(e) => setRelayCreds({ ...relayCreds, client_secret: e.target.value })}
                placeholder={spotifyConn?.has_secret ? "SECRET KEY IS SET • TYPE TO OVERWRITE" : "••••••••••••••••"}
                className="w-full bg-white rounded-lg border-2 border-retro-dark p-3 font-body font-bold focus:outline-none focus:border-retro-teal placeholder:text-retro-dark/30 placeholder:italic"
              />
            </div>
          </div>

          <button
            onClick={() => relayMutation.mutate(relayCreds)}
            disabled={relayMutation.isPending}
            className="w-full py-4 bg-retro-teal text-retro-dark font-display text-2xl uppercase rounded-xl border-4 border-retro-dark shadow-retro hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
          >
            {relayMutation.isPending ? <Disc className="animate-spin" /> : 'Synchronize Relay'}
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Archive Highlights"
      >
        {activeMetadata && (
          <div className="space-y-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 bg-retro-teal/20 rounded-full border-4 border-retro-dark flex items-center justify-center shadow-retro-sm">
                {activeMetadata.artist ? <Disc className="w-10 h-10" /> : <UserIcon className="w-10 h-10" />}
              </div>
              <div>
                <h4 className="text-3xl font-display text-retro-dark uppercase">{activeMetadata.name}</h4>
                {activeMetadata.artist && <p className="font-body text-lg italic text-retro-dark/60">By {activeMetadata.artist}</p>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-6 border-y-4 border-retro-dark border-dashed">
              {activeMetadata.type && (
                <div>
                  <span className="block text-xs font-display uppercase text-retro-dark/40 tracking-widest">Type</span>
                  <span className="font-body font-bold text-retro-dark uppercase">{activeMetadata.type}</span>
                </div>
              )}
              {activeMetadata.country && (
                <div>
                  <span className="block text-xs font-display uppercase text-retro-dark/40 tracking-widest">Origin</span>
                  <span className="font-body font-bold text-retro-dark uppercase">{activeMetadata.country}</span>
                </div>
              )}
              {activeMetadata.first_release_date && (
                <div>
                  <span className="block text-xs font-display uppercase text-retro-dark/40 tracking-widest">Release Date</span>
                  <span className="font-body font-bold text-retro-dark">{activeMetadata.first_release_date}</span>
                </div>
              )}
              {activeMetadata.primary_type && (
                <div>
                  <span className="block text-xs font-display uppercase text-retro-dark/40 tracking-widest">Category</span>
                  <span className="font-display text-retro-dark uppercase">{activeMetadata.primary_type}</span>
                </div>
              )}
            </div>

            {activeMetadata.source_url && (
              <div className="pt-4">
                <a
                  href={activeMetadata.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-retro-teal hover:text-teal-600 font-display uppercase tracking-widest underline decoration-2 underline-offset-4 transition-all"
                >
                  View on {activeMetadata.source_name}
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
