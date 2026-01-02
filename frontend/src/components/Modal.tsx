import React, { useEffect, useCallback } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const handleEsc = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose()
    }
  }, [onClose])

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEsc, false)
      // Prevent scrolling when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEsc, false)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, handleEsc])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-retro-dark/80 backdrop-blur-sm animate-in fade-in duration-300"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-2xl rounded-2xl border-8 border-retro-dark shadow-retro overflow-hidden animate-in zoom-in-95 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="bg-retro-teal p-6 border-b-4 border-retro-dark flex justify-between items-center">
          <h2 className="text-3xl font-display text-retro-dark uppercase italic tracking-tighter">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-retro-dark/10 rounded-lg transition-colors border-2 border-transparent hover:border-retro-dark"
          >
            <X className="w-8 h-8 text-retro-dark" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-8 bg-retro-cream">
          {children}
        </div>

        {/* Modal Footer */}
        <div className="p-6 bg-white border-t-4 border-retro-dark border-dashed flex justify-end">
          <button
            onClick={onClose}
            className="px-8 py-2 bg-retro-pink text-retro-dark font-display text-xl uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-pink-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all"
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  )
}
