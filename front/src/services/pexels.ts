/**
 * Pexels API Integration Service
 * Provides functionality to search and fetch images/videos from Pexels
 */

// API Configuration
const PEXELS_API_URL = 'https://api.pexels.com/v1'
const PEXELS_VIDEO_API_URL = 'https://api.pexels.com/videos'

// Replace this with your actual Pexels API key
// Get one free at https://www.pexels.com/api/
const PEXELS_API_KEY = process.env.NEXT_PUBLIC_PEXELS_API_KEY || 'YOUR_PEXELS_API_KEY'

// Types
export interface PexelsPhoto {
  id: number
  width: number
  height: number
  url: string
  photographer: string
  photographer_url: string
  photographer_id: number
  avg_color: string
  src: {
    original: string
    large2x: string
    large: string
    medium: string
    small: string
    portrait: string
    landscape: string
    tiny: string
  }
  liked: boolean
  alt: string
}

export interface PexelsVideo {
  id: number
  width: number
  height: number
  duration: number
  full_res: string | null
  tags: string[]
  url: string
  image: string
  avg_color: string | null
  user: {
    id: number
    name: string
    url: string
  }
  video_files: Array<{
    id: number
    quality: string
    file_type: string
    width: number
    height: number
    fps: number
    link: string
  }>
  video_pictures: Array<{
    id: number
    nr: number
    picture: string
  }>
}

export interface PexelsSearchResponse {
  page: number
  per_page: number
  photos: PexelsPhoto[]
  total_results: number
  next_page?: string
  prev_page?: string
}

export interface PexelsVideoSearchResponse {
  page: number
  per_page: number
  videos: PexelsVideo[]
  total_results: number
  next_page?: string
  prev_page?: string
}

// Error handling
class PexelsError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'PexelsError'
  }
}

// Helper function to make API requests
async function pexelsRequest(url: string, options: RequestInit = {}): Promise<Response> {
  if (PEXELS_API_KEY === 'YOUR_PEXELS_API_KEY') {
    throw new PexelsError('Pexels API key not configured. Please set NEXT_PUBLIC_PEXELS_API_KEY environment variable.')
  }

  const response = await fetch(url, {
    headers: {
      'Authorization': PEXELS_API_KEY,
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new PexelsError(`Pexels API error: ${errorText}`, response.status)
  }

  return response
}

/**
 * Search for photos on Pexels
 */
export async function searchPhotos(
  query: string,
  options: {
    page?: number
    per_page?: number
    orientation?: 'landscape' | 'portrait' | 'square'
    size?: 'large' | 'medium' | 'small'
    color?: 'red' | 'orange' | 'yellow' | 'green' | 'turquoise' | 'blue' | 'violet' | 'pink' | 'brown' | 'black' | 'gray' | 'white'
    locale?: string
  } = {}
): Promise<PexelsSearchResponse> {
  const params = new URLSearchParams({
    query: query.trim(),
    page: (options.page || 1).toString(),
    per_page: Math.min(options.per_page || 15, 80).toString(),
  })

  if (options.orientation) params.append('orientation', options.orientation)
  if (options.size) params.append('size', options.size)
  if (options.color) params.append('color', options.color)
  if (options.locale) params.append('locale', options.locale)

  const response = await pexelsRequest(`${PEXELS_API_URL}/search?${params}`)
  return response.json()
}

/**
 * Search for videos on Pexels
 */
export async function searchVideos(
  query: string,
  options: {
    page?: number
    per_page?: number
    min_width?: number
    min_height?: number
    min_duration?: number
    max_duration?: number
    orientation?: 'landscape' | 'portrait' | 'square'
    size?: 'large' | 'medium' | 'small'
    locale?: string
  } = {}
): Promise<PexelsVideoSearchResponse> {
  const params = new URLSearchParams({
    query: query.trim(),
    page: (options.page || 1).toString(),
    per_page: Math.min(options.per_page || 15, 80).toString(),
  })

  if (options.min_width) params.append('min_width', options.min_width.toString())
  if (options.min_height) params.append('min_height', options.min_height.toString())
  if (options.min_duration) params.append('min_duration', options.min_duration.toString())
  if (options.max_duration) params.append('max_duration', options.max_duration.toString())
  if (options.orientation) params.append('orientation', options.orientation)
  if (options.size) params.append('size', options.size)
  if (options.locale) params.append('locale', options.locale)

  const response = await pexelsRequest(`${PEXELS_VIDEO_API_URL}/search?${params}`)
  return response.json()
}

/**
 * Get curated photos from Pexels
 */
export async function getCuratedPhotos(options: {
  page?: number
  per_page?: number
} = {}): Promise<PexelsSearchResponse> {
  const params = new URLSearchParams({
    page: (options.page || 1).toString(),
    per_page: Math.min(options.per_page || 15, 80).toString(),
  })

  const response = await pexelsRequest(`${PEXELS_API_URL}/curated?${params}`)
  return response.json()
}

/**
 * Get popular videos from Pexels
 */
export async function getPopularVideos(options: {
  page?: number
  per_page?: number
  min_width?: number
  min_height?: number
  min_duration?: number
  max_duration?: number
} = {}): Promise<PexelsVideoSearchResponse> {
  const params = new URLSearchParams({
    page: (options.page || 1).toString(),
    per_page: Math.min(options.per_page || 15, 80).toString(),
  })

  if (options.min_width) params.append('min_width', options.min_width.toString())
  if (options.min_height) params.append('min_height', options.min_height.toString())
  if (options.min_duration) params.append('min_duration', options.min_duration.toString())
  if (options.max_duration) params.append('max_duration', options.max_duration.toString())

  const response = await pexelsRequest(`${PEXELS_VIDEO_API_URL}/popular?${params}`)
  return response.json()
}

/**
 * Get a photo by ID
 */
export async function getPhotoById(id: number): Promise<PexelsPhoto> {
  const response = await pexelsRequest(`${PEXELS_API_URL}/photos/${id}`)
  return response.json()
}

/**
 * Get a video by ID
 */
export async function getVideoById(id: number): Promise<PexelsVideo> {
  const response = await pexelsRequest(`${PEXELS_VIDEO_API_URL}/videos/${id}`)
  return response.json()
}

/**
 * Get business-relevant photos based on industry and business type
 */
export async function getBusinessPhotos(
  industry: string,
  businessType: string,
  options: {
    count?: number
    orientation?: 'landscape' | 'portrait' | 'square'
    style?: 'professional' | 'modern' | 'creative'
  } = {}
): Promise<PexelsPhoto[]> {
  const { count = 6, orientation = 'landscape', style = 'professional' } = options

  // Create search terms based on industry and business type
  const searchTerms = [
    `${industry} business`,
    `${businessType} professional`,
    `${industry} office`,
    `business ${style}`,
    `professional ${industry}`,
    `${businessType} workspace`
  ]

  const photos: PexelsPhoto[] = []
  const maxPerSearch = Math.ceil(count / searchTerms.length)

  for (const term of searchTerms) {
    if (photos.length >= count) break

    try {
      const response = await searchPhotos(term, {
        per_page: maxPerSearch,
        orientation,
        size: 'large'
      })

      // Filter for high-quality, relevant photos
      const relevantPhotos = response.photos
        .filter(photo => 
          photo.width >= 1000 && 
          photo.height >= 600 && 
          !photo.alt.toLowerCase().includes('logo') &&
          !photo.alt.toLowerCase().includes('brand')
        )
        .slice(0, maxPerSearch)

      photos.push(...relevantPhotos)
    } catch (error) {
      console.warn(`Failed to fetch photos for term "${term}":`, error)
    }
  }

  // Remove duplicates and return requested count
  const uniquePhotos = photos.filter((photo, index, self) => 
    self.findIndex(p => p.id === photo.id) === index
  )

  return uniquePhotos.slice(0, count)
}

/**
 * Get hero section images for a specific industry
 */
export async function getHeroImages(industry: string, count: number = 3): Promise<PexelsPhoto[]> {
  const heroTerms = [
    `${industry} hero`,
    `${industry} banner`,
    `professional ${industry}`,
    `${industry} success`,
    `${industry} team`
  ]

  const photos: PexelsPhoto[] = []

  for (const term of heroTerms) {
    if (photos.length >= count) break

    try {
      const response = await searchPhotos(term, {
        per_page: 5,
        orientation: 'landscape',
        size: 'large'
      })

      const heroPhotos = response.photos
        .filter(photo => 
          photo.width >= 1200 && 
          photo.height >= 600 &&
          photo.width / photo.height >= 1.5 // Landscape ratio for hero images
        )

      photos.push(...heroPhotos)
    } catch (error) {
      console.warn(`Failed to fetch hero images for term "${term}":`, error)
    }
  }

  return photos.filter((photo, index, self) => 
    self.findIndex(p => p.id === photo.id) === index
  ).slice(0, count)
}

/**
 * Generate attribution text for Pexels content
 */
export function generateAttribution(photo: PexelsPhoto): string {
  return `Photo by ${photo.photographer} on Pexels`
}

export function generateVideoAttribution(video: PexelsVideo): string {
  return `Video by ${video.user.name} on Pexels`
}

/**
 * Check if Pexels API is properly configured
 */
export function isPexelsConfigured(): boolean {
  return PEXELS_API_KEY !== 'YOUR_PEXELS_API_KEY' && PEXELS_API_KEY.length > 0
}

export { PexelsError }
