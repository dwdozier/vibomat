# Vibomat Product Guide

## Project Summary

Vibomat is a universal music platform to generate and manage playlists using Generative AI and
external metadata verification. It supports multiple streaming services and uses a FastAPI backend
with a TanStack/React frontend.

## Initial Concept

Vibomat is an AI-powered universal music platform for generating and managing playlists with
multi-service synchronization and metadata verification.

## Vision

To create a platform-agnostic music management suite that bridges the gap between different
streaming services (Spotify, Apple Music, Tidal, etc.) while fostering social sharing and
discovery. Vibomat aims to be the definitive tool for users to seamlessly curate, transfer, and
share music across the entire digital music ecosystem.

## Vib-O-Mat Terminology

- **Citizens:** Users
- **Archives:** Playlists
- **Relays:** Service Connections
- **Nodes:** OAuth Identity Links

## Target Audience

- Music enthusiasts who use multiple streaming services.
- Social curators who want to share their musical discoveries with friends, regardless of which
    platform they use.

## Problem Statement

Users currently face significant friction when trying to share playlists with friends who use
different music services. This "walled garden" approach limits musical discovery and social
interaction. Existing tools often lack the creative power of AI and the precision of multi-source
metadata verification.

## Key Differentiators

- **Generative AI Integration:** Unlike simple transfer tools, Vibomat uses Generative AI to create
    new, mood-based playlists from scratch based on user prompts.
- **Precision Verification:** Cross-references results with MusicBrainz and Discogs to eliminate
    hallucinations and ensure accurate track matching across services.
- **Universal Synchronization:** Designed to eventually support all major streaming platforms,
    breaking down the barriers of service-specific ecosystems.
