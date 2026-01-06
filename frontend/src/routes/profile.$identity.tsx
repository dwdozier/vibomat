import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { User as UserIcon, Music, Disc, Heart, Globe, Lock } from 'lucide-react'
import { type Album } from '../api/auth'

export const Route = createFileRoute('/profile/$identity')({
  component: Profile,
})

interface PublicPlaylist {
  id: string
  name: string
  description: string
  user_id: string
}

function isUuid(str: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str)
}

function Profile() {
  const { identity } = Route.useParams()

  const { data: profile, isLoading: profileLoading, error: profileError } = useQuery({
    queryKey: ['profile', identity],
    queryFn: async () => {
      const endpoint = isUuid(identity)
        ? `/api/v1/profile/${identity}`
        : `/api/v1/profile/by-handle/${identity}`
      const res = await fetch(endpoint)
      if (!res.ok) throw new Error('Profile not found')
      return res.json()
    }
  })

  const { data: playlists, isLoading: playlistsLoading } = useQuery<PublicPlaylist[]>({
    queryKey: ['profile-playlists', profile?.id],
    queryFn: async () => {
      const res = await fetch(`/api/v1/profile/${profile.id}/playlists`)
      if (!res.ok) return []
      return res.json()
    },
    enabled: !!profile?.is_public && !!profile?.id
  })

  const { data: favorites, isLoading: favoritesLoading } = useQuery<PublicPlaylist[]>({
    queryKey: ['profile-favorites', profile?.id],
    queryFn: async () => {
      const res = await fetch(`/api/v1/profile/${profile.id}/favorites`)
      if (!res.ok) return []
      return res.json()
    },
    enabled: !!profile?.is_public && !!profile?.id
  })

  if (profileLoading) return <div className="flex justify-center p-20"><Disc className="animate-spin w-12 h-12 text-retro-teal" /></div>
  if (profileError) return (
    <div className="max-w-4xl mx-auto p-12 bg-retro-pink/10 border-4 border-retro-pink rounded-2xl text-center">
      <Lock className="w-16 h-16 text-retro-pink mx-auto mb-4" />
      <h2 className="text-3xl font-display text-retro-dark uppercase">Profile Restricted</h2>
      <p className="mt-4 text-xl font-body text-retro-dark/70">This Citizen has opted for a private broadcast frequency or the record does not exist.</p>
    </div>
  )

  return (
    <div className="max-w-5xl mx-auto space-y-12">
      {/* Header Card */}
      <section className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4">
           {profile.is_public ? (
             <div className="flex items-center gap-2 text-retro-teal">
               <Globe className="w-5 h-5" />
               <span className="font-display uppercase text-sm tracking-widest">Public Broadcast</span>
             </div>
           ) : (
             <div className="flex items-center gap-2 text-retro-pink">
               <Lock className="w-5 h-5" />
               <span className="font-display uppercase text-sm tracking-widest">Private Archive</span>
             </div>
           )}
        </div>

        <div className="flex flex-col md:flex-row items-center gap-10">
          <div className="w-32 h-32 bg-retro-teal rounded-full border-4 border-retro-dark flex items-center justify-center shadow-retro-sm">
            <UserIcon className="w-16 h-16 text-retro-dark" />
          </div>
          <div className="text-center md:text-left">
            <h2 className="text-5xl font-display text-retro-dark uppercase italic tracking-tighter">
              Citizen {profile.display_name}
            </h2>
            {profile.handle && (
               <p className="font-display text-retro-dark/40 text-lg uppercase tracking-widest mt-1">
                 @{profile.handle}
               </p>
            )}
            <p className="font-display text-retro-teal text-xl tracking-widest mt-2 uppercase italic">Verified Vib-O-Mat Citizen</p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar: Interests */}
        <div className="space-y-8">
          <section className="bg-retro-cream p-6 rounded-xl border-4 border-retro-dark shadow-retro-sm">
            <h3 className="font-display text-2xl text-retro-dark uppercase border-b-2 border-retro-dark pb-2 mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 fill-retro-pink text-retro-pink" />
              Top Artists
            </h3>
            <ul className="space-y-2">
              {profile.favorite_artists?.length > 0 ? (
                profile.favorite_artists.map((artist: any, i: number) => {
                  const name = typeof artist === 'string' ? artist : artist.name;
                  return (
                    <li key={i} className="font-body text-lg font-bold text-retro-dark bg-white/50 px-3 py-1 rounded border-2 border-retro-dark/10">
                      {name}
                    </li>
                  );
                })
              ) : (
                <li className="text-retro-dark/40 italic">No artists archived.</li>
              )}
            </ul>
          </section>

          <section className="bg-retro-yellow/20 p-6 rounded-xl border-4 border-retro-dark shadow-retro-sm">
            <h3 className="font-display text-2xl text-retro-dark uppercase border-b-2 border-retro-dark pb-2 mb-4 flex items-center gap-2">
              <Music className="w-5 h-5 text-retro-dark" />
              Unskippable
            </h3>
            <div className="space-y-4">
               {profile.unskippable_albums?.length > 0 ? (
                 profile.unskippable_albums.map((album: Album, i: number) => (
                   <div key={i} className="flex gap-3 items-center bg-white p-2 rounded border-2 border-retro-dark">
                     <div className="w-12 h-12 bg-retro-dark/10 rounded flex items-center justify-center">
                       <Disc className="w-6 h-6 text-retro-dark" />
                     </div>
                     <div>
                       <div className="font-body font-bold text-sm leading-tight">{album.name}</div>
                       <div className="text-xs text-retro-dark/60">{album.artist}</div>
                     </div>
                   </div>
                 ))
               ) : (
                 <div className="text-retro-dark/40 italic">Nothing marked as unskippable.</div>
               )}
            </div>
          </section>
        </div>

        {/* Main: Playlists */}
        <div className="md:col-span-2 space-y-12">
          <div className="space-y-6">
            <h3 className="font-display text-4xl text-retro-dark uppercase tracking-tight italic">
              Broadcasted Playlists
            </h3>

            <div className="grid grid-cols-1 gap-6">
              {playlistsLoading ? (
                <Disc className="animate-spin w-8 h-8 mx-auto" />
              ) : (playlists?.length ?? 0) > 0 ? (
                playlists?.map((playlist: PublicPlaylist) => (
                  <div key={playlist.id} className="bg-white p-6 rounded-xl border-4 border-retro-dark shadow-retro-sm hover:shadow-retro transition-all group">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-2xl font-display text-retro-dark uppercase group-hover:text-retro-teal transition-colors">
                          {playlist.name}
                        </h4>
                        <p className="text-retro-dark/60 font-body mt-1 italic">
                          {playlist.description || "No description provided."}
                        </p>
                      </div>
                      <button className="px-4 py-2 bg-retro-pink text-retro-dark font-display rounded-lg border-2 border-retro-dark shadow-retro-sm hover:bg-pink-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase text-sm">
                        Clone to Mine
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white/50 p-8 rounded-xl border-4 border-retro-dark border-dashed text-center">
                  <p className="font-display text-lg text-retro-dark/40 uppercase">No public broadcasts</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <h3 className="font-display text-4xl text-retro-dark uppercase tracking-tight italic">
              Favorited Archive
            </h3>

            <div className="grid grid-cols-1 gap-6">
              {favoritesLoading ? (
                <Disc className="animate-spin w-8 h-8 mx-auto" />
              ) : (favorites?.length ?? 0) > 0 ? (
                favorites?.map((playlist: PublicPlaylist) => (
                  <div key={playlist.id} className="bg-retro-cream p-6 rounded-xl border-4 border-retro-dark shadow-retro-sm hover:shadow-retro transition-all group">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-2xl font-display text-retro-dark uppercase group-hover:text-retro-teal transition-colors">
                          {playlist.name}
                        </h4>
                        <p className="text-retro-dark/60 font-body mt-1 italic">
                          By Citizen {playlist.user_id.split('-')[0]}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button className="px-4 py-2 bg-retro-teal text-retro-dark font-display rounded-lg border-2 border-retro-dark shadow-retro-sm hover:bg-teal-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all uppercase text-sm">
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white/50 p-8 rounded-xl border-4 border-retro-dark border-dashed text-center">
                  <p className="font-display text-lg text-retro-dark/40 uppercase">No favorited archives</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
