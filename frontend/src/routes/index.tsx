import { createFileRoute, Link } from '@tanstack/react-router'
import { Sparkles, Zap, ShieldCheck, ArrowRight } from 'lucide-react'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return (
    <div className="space-y-24 py-16">
      {/* Hero Section */}
      <header className="text-center space-y-10 relative">
        <div className="inline-block bg-retro-yellow px-6 py-2 rounded-full border-4 border-retro-dark font-display text-lg tracking-widest uppercase mb-4 shadow-retro-sm transform -rotate-1">
          Precision Engineered • SERIES 2000
        </div>
        <h1 className="text-7xl md:text-9xl font-display text-retro-dark leading-[0.9] tracking-tighter uppercase italic drop-shadow-[4px_4px_0px_rgba(80,200,198,0.3)]">
          THE <br />
          <span className="text-retro-teal drop-shadow-[6px_6px_0px_rgba(0,0,0,1)]">VIB-O-MAT</span> <br />
          EXPERIENCE
        </h1>
        <p className="text-2xl md:text-3xl max-w-3xl mx-auto text-retro-dark font-body font-bold leading-relaxed opacity-90">
          High-fidelity playlist generation powered by the wonders of <br className="hidden md:block" />
          Modern Science™ and Artificial Intelligence.
        </p>
        <div className="pt-12">
          <Link
            to="/playlists"
            className="inline-flex items-center gap-4 px-12 py-6 bg-retro-pink hover:bg-pink-400 text-retro-dark text-4xl font-display rounded-2xl border-8 border-retro-dark shadow-retro hover:scale-105 active:shadow-none active:translate-x-2 active:translate-y-2 transition-all group"
          >
            START GENERATING <ArrowRight className="w-12 h-12 group-hover:translate-x-2 transition-transform" />
          </Link>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-0 left-[10%] -z-10 text-retro-teal/20 animate-pulse hidden md:block">
          <Sparkles className="w-48 h-48 rotate-12" />
        </div>
        <div className="absolute bottom-0 right-[10%] -z-10 text-retro-pink/20 animate-bounce hidden md:block">
          <Zap className="w-40 h-40 -rotate-12" />
        </div>
      </header>

      {/* Features Grid */}
      <section className="grid md:grid-cols-3 gap-12 max-w-7xl mx-auto">
        <div className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro hover:-translate-y-2 transition-transform relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-2 bg-retro-teal"></div>
          <div className="w-20 h-20 bg-retro-teal rounded-xl border-4 border-retro-dark flex items-center justify-center mb-8 shadow-retro-sm group-hover:rotate-12 transition-transform">
            <Zap className="w-12 h-12 text-retro-dark" />
          </div>
          <h3 className="text-3xl font-display mb-6 text-retro-dark uppercase">Instant Vibe</h3>
          <p className="text-xl text-retro-dark/80 font-body font-bold leading-relaxed">
            State-of-the-art AI algorithms curate the perfect selection for any mood or occasion. Just insert a prompt!
          </p>
        </div>

        <div className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro hover:-translate-y-2 transition-transform relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-2 bg-retro-pink"></div>
          <div className="w-20 h-20 bg-retro-pink rounded-xl border-4 border-retro-dark flex items-center justify-center mb-8 shadow-retro-sm group-hover:-rotate-12 transition-transform">
            <ShieldCheck className="w-12 h-12 text-retro-dark" />
          </div>
          <h3 className="text-3xl font-display mb-6 text-retro-dark uppercase">Verified</h3>
          <p className="text-xl text-retro-dark/80 font-body font-bold leading-relaxed">
            Our exclusive cross-referencing technology verifies every track with MusicBrainz to ensure 100% accuracy.
          </p>
        </div>

        <div className="bg-white p-10 rounded-2xl border-8 border-retro-dark shadow-retro hover:-translate-y-2 transition-transform relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-2 bg-retro-yellow"></div>
          <div className="w-20 h-20 bg-retro-yellow rounded-xl border-4 border-retro-dark flex items-center justify-center mb-8 shadow-retro-sm group-hover:rotate-12 transition-transform">
            <Sparkles className="w-12 h-12 text-retro-dark" />
          </div>
          <h3 className="text-3xl font-display mb-6 text-retro-dark uppercase">Sync Sync</h3>
          <p className="text-xl text-retro-dark/80 font-body font-bold leading-relaxed">
            Direct integration with your favorite streaming services. One click and your new playlist is ready to play.
          </p>
        </div>
      </section>

      {/* Footer-ish Info */}
      <footer className="text-center pt-12">
        <div className="inline-block border-t-2 border-retro-dark pt-4 px-12">
          <p className="font-display text-retro-dark opacity-50 tracking-widest uppercase">
            Vib-O-Mat Corporation © 1962-2025
          </p>
        </div>
      </footer>
    </div>
  )
}
