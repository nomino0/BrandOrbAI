'use client'

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { 
  ArrowRight, 
  CheckCircle, 
  Star, 
  Users, 
  Shield, 
  Zap, 
  Mail, 
  Phone, 
  MapPin,
  Globe,
  Award,
  TrendingUp,
  Heart,
  MessageCircle,
  Send,
  Facebook,
  Twitter,
  Linkedin,
  Instagram,
  Play,
  Volume2,
  VolumeX,
  Quote,
  Sparkles,
  Target,
  Lightbulb,
  Clock,
  Rocket
} from "lucide-react"

interface WebsiteAnalysis {
  company_name: string
  industry: string
  business_type: string
  target_audience: string
  unique_value_proposition: string
  key_services: string[]
  competitive_advantages: string[]
  brand_colors: string[]
  brand_personality: string
  website_sections: string[]
  call_to_action: string
  seo_keywords: string[]
  tone_of_voice: string
  business_model: string
  stage: string
  key_metrics: string[]
  social_proof_elements: string[]
}

interface GeneratedLandingPageProps {
  analysis: WebsiteAnalysis
  businessData?: {
    business_summary?: string
    financial_data?: string
    market_data?: string
    legal_data?: string
    brand_identity_data?: string
  }
}

export default function GeneratedLandingPage({ analysis, businessData }: GeneratedLandingPageProps) {
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    message: ''
  })
  const [isVideoMuted, setIsVideoMuted] = useState(true)
  const [heroImages, setHeroImages] = useState<string[]>([])
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  // Extract brand data with enhanced processing
  const brandData = businessData?.brand_identity_data ? 
    (() => {
      try {
        return JSON.parse(businessData.brand_identity_data)
      } catch {
        return null
      }
    })() : null

  const brandName = brandData?.brand_name || analysis.company_name || "Your Business"
  const brandColors = brandData?.colors || analysis.brand_colors || ['#3B82F6', '#1E40AF', '#60A5FA']
  const brandPersonality = brandData?.personality || analysis.brand_personality?.split(',') || ['professional', 'innovative']
  const brandDescription = brandData?.description || analysis.brand_description || businessData?.business_summary?.substring(0, 200) || ''

  // Enhanced dynamic content generation
  const dynamicTestimonials = analysis.dynamic_testimonials || [
    {
      name: "Sarah Johnson",
      role: `CEO, ${analysis.industry} Solutions`,
      content: `Working with ${brandName} transformed our business. Their expertise in ${analysis.key_services?.[0] || 'professional services'} is outstanding.`,
      rating: 5,
      image: "https://images.unsplash.com/photo-1494790108755-2616b612b5c5?w=100&h=100&fit=crop&crop=face"
    },
    {
      name: "Michael Chen", 
      role: `Director, ${analysis.industry} Corp`,
      content: `Professional, reliable, and delivers exceptional results. Their ${analysis.key_services?.[1] || 'service'} capabilities exceeded expectations.`,
      rating: 5,
      image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face"
    },
    {
      name: "Emily Rodriguez",
      role: `Manager, ${analysis.business_type} Enterprise`,
      content: `The team's expertise in ${analysis.key_services?.slice(0, 2).join(' and ') || 'business solutions'} helped us achieve remarkable growth.`,
      rating: 5,
      image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face"
    }
  ]

  const dynamicStats = analysis.dynamic_stats || [
    { value: analysis.stage === 'startup' ? '50+' : analysis.stage === 'established' ? '1000+' : '500+', label: 'Happy Clients' },
    { value: '98%', label: 'Success Rate' },
    { value: '24/7', label: 'Support' },
    { value: analysis.stage === 'startup' ? '2+' : analysis.stage === 'established' ? '10+' : '5+', label: 'Years Experience' }
  ]

  // Dynamic hero content based on user requirements and business data
  const userRequirements = analysis.user_requirements || ''
  const heroTitle = userRequirements.toLowerCase().includes('catchy') || userRequirements.toLowerCase().includes('creative')
    ? `Transform Your ${analysis.industry} Experience with ${brandName}`
    : userRequirements.toLowerCase().includes('professional') || userRequirements.toLowerCase().includes('corporate')
    ? `Professional ${analysis.business_type} Solutions by ${brandName}`
    : `Leading ${analysis.business_type} in ${analysis.industry}`

  const heroSubtitle = analysis.unique_value_proposition || 
    `We specialize in ${analysis.key_services?.slice(0, 3).join(', ') || 'professional services'} to help ${analysis.target_audience || 'businesses like yours'} achieve exceptional results in the ${analysis.industry} industry.`

  // Create CSS custom properties for brand colors
  const brandStyles = {
    '--brand-primary': brandColors[0] || '#3B82F6',
    '--brand-secondary': brandColors[1] || '#1E40AF',
    '--brand-accent': brandColors[2] || '#60A5FA',
    '--brand-gradient': `linear-gradient(135deg, ${brandColors[0] || '#3B82F6'} 0%, ${brandColors[1] || '#1E40AF'} 100%)`
  } as React.CSSProperties

  // Load hero images based on industry
  useEffect(() => {
    const loadHeroImages = async () => {
      try {
        const query = `${analysis.industry} business professional modern`
        const response = await fetch('/api/stock-images', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            perPage: 5,
            orientation: 'landscape'
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          const images = data.photos?.map((photo: any) => photo.src.large2x || photo.src.large) || []
          setHeroImages(images)
        }
      } catch (error) {
        console.log('Using fallback hero images:', error)
        // Fallback to Unsplash images
        setHeroImages([
          `https://images.unsplash.com/photo-1551434678-e076c223a692?w=1920&h=1080&fit=crop&crop=center`,
          `https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1920&h=1080&fit=crop&crop=center`,
          `https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1920&h=1080&fit=crop&crop=center`
        ])
      }
    }

    loadHeroImages()
  }, [analysis.industry])

  // Rotate hero images
  useEffect(() => {
    if (heroImages.length > 1) {
      const interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev + 1) % heroImages.length)
      }, 6000)
      return () => clearInterval(interval)
    }
  }, [heroImages.length])

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Contact form submitted:', contactForm)
    alert('Thank you for your message! We\'ll get back to you soon.')
    setContactForm({ name: '', email: '', message: '' })
  }

  const getServiceIcon = (index: number) => {
    const icons = [Users, TrendingUp, Award, Heart, Shield, Zap, Target, Lightbulb, Rocket, Star]
    const IconComponent = icons[index % icons.length]
    return <IconComponent className="h-8 w-8" style={{ color: brandColors[0] }} />
  }

  const getAdvantageIcon = (index: number) => {
    const icons = [Star, Shield, Zap, Clock, Rocket, Award, Target, Lightbulb, TrendingUp, Users]
    const IconComponent = icons[index % icons.length]
    return <IconComponent className="h-6 w-6 text-white" />
  }

  return (
    <div className="min-h-screen bg-background text-foreground" style={brandStyles}>
      {/* Header */}
      <header className="fixed top-0 z-50 w-full bg-background/95 backdrop-blur-md border-b border-border/40 shadow-sm">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-3">
              <div 
                className="h-10 w-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg"
                style={{ background: 'var(--brand-gradient)' }}
              >
                {brandName.charAt(0)}
              </div>
              <div>
                <span className="text-xl font-bold text-foreground">{brandName}</span>
                <div className="text-xs text-muted-foreground">{analysis.industry}</div>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#about" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group">
                About
                <span className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent scale-x-0 group-hover:scale-x-100 transition-transform"></span>
              </a>
              <a href="#services" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group">
                Services
                <span className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent scale-x-0 group-hover:scale-x-100 transition-transform"></span>
              </a>
              <a href="#contact" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors relative group">
                Contact
                <span className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent scale-x-0 group-hover:scale-x-100 transition-transform"></span>
              </a>
              <Button 
                size="sm" 
                className="text-white shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
                style={{ background: 'var(--brand-gradient)' }}
              >
                Get Started
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section with Video/Image Background */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image/Video */}
        <div className="absolute inset-0 z-0">
          {heroImages.length > 0 && (
            <div className="relative w-full h-full">
              {heroImages.map((image, index) => (
                <div
                  key={index}
                  className={`absolute inset-0 transition-opacity duration-1000 ${
                    index === currentImageIndex ? 'opacity-100' : 'opacity-0'
                  }`}
                >
                  <img
                    src={image}
                    alt={`${analysis.industry} background`}
                    className="w-full h-full object-cover"
                  />
                  <div 
                    className="absolute inset-0 bg-gradient-to-r opacity-80"
                    style={{ 
                      background: `linear-gradient(135deg, ${brandColors[0]}E6 0%, ${brandColors[1]}CC 100%)` 
                    }}
                  ></div>
                </div>
              ))}
            </div>
          )}
          
          {/* Animated Particles */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-1/4 left-1/4 w-4 h-4 bg-white/20 rounded-full animate-float"></div>
            <div className="absolute top-1/3 right-1/3 w-2 h-2 bg-white/30 rounded-full animate-float-delay-1"></div>
            <div className="absolute bottom-1/4 left-1/2 w-3 h-3 bg-white/25 rounded-full animate-float-delay-2"></div>
          </div>
        </div>

        {/* Hero Content */}
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-5xl mx-auto">
            <Badge 
              variant="secondary" 
              className="mb-6 px-4 py-2 text-sm font-medium bg-white/10 text-white border-white/20 backdrop-blur-sm"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {analysis.industry} • {analysis.business_type} • {analysis.stage}
            </Badge>
            
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              <span className="bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
                {heroTitle}
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-white/90 mb-8 max-w-3xl mx-auto leading-relaxed">
              {heroSubtitle}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Button 
                size="lg" 
                className="px-8 py-4 text-lg font-semibold text-white shadow-2xl hover:shadow-3xl transition-all transform hover:scale-105 hover:-translate-y-1"
                style={{ background: 'var(--brand-gradient)' }}
              >
                <Rocket className="mr-2 h-5 w-5" />
                {analysis.call_to_action || 'Start Your Journey'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="px-8 py-4 text-lg font-semibold bg-white/10 text-white border-white/30 hover:bg-white/20 backdrop-blur-sm"
              >
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-8 border-t border-white/20">
              {(analysis.key_metrics || [
                'Happy Clients',
                'Success Rate', 
                'Years Experience',
                'Projects Completed'
              ]).slice(0, 4).map((metric, index) => {
                const values = ['500+', '99%', '10+', '1000+']
                return (
                  <div key={index} className="text-center group">
                    <div className="text-3xl md:text-4xl font-bold text-white mb-2 group-hover:scale-110 transition-transform">
                      {values[index]}
                    </div>
                    <div className="text-sm text-white/80 font-medium">{metric}</div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
          <div className="animate-bounce">
            <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center">
              <div className="w-1 h-3 bg-white/50 rounded-full mt-2 animate-pulse"></div>
            </div>
          </div>
        </div>
      </section>

      {/* About Section - Enhanced with Visual Elements */}
      <section id="about" className="py-20 bg-gradient-to-b from-background to-surface">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {/* Section Header */}
            <div className="text-center mb-16">
              <Badge 
                variant="outline" 
                className="mb-4 px-4 py-2 text-sm font-medium"
                style={{ 
                  borderColor: brandColors[0] + '40',
                  color: brandColors[0]
                }}
              >
                <Target className="h-4 w-4 mr-2" />
                About {brandName}
              </Badge>
              <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
                Why Choose <span style={{ color: brandColors[0] }}>{brandName}</span>?
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                {brandDescription || `We're dedicated to providing exceptional service in the ${analysis.industry} industry, combining innovation with reliability to deliver outstanding results.`}
              </p>
            </div>

            {/* Brand Story & Values */}
            <div className="grid lg:grid-cols-2 gap-16 items-center mb-20">
              <div className="space-y-8">
                <div>
                  <h3 className="text-2xl font-bold text-foreground mb-4 flex items-center">
                    <div 
                      className="w-12 h-12 rounded-xl flex items-center justify-center mr-4 text-white"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      <Lightbulb className="h-6 w-6" />
                    </div>
                    Our Mission
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {analysis.unique_value_proposition || `To revolutionize the ${analysis.industry} industry through innovative solutions that empower businesses to reach their full potential.`}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {brandPersonality.slice(0, 4).map((trait, index) => (
                    <div key={index} className="text-center p-6 rounded-2xl bg-card border border-border/50 hover:border-primary/30 transition-all group hover:shadow-lg">
                      <div 
                        className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform"
                        style={{ backgroundColor: brandColors[0] + '20' }}
                      >
                        {getAdvantageIcon(index)}
                      </div>
                      <h4 className="font-semibold text-foreground capitalize">{trait}</h4>
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative">
                <div className="relative z-10">
                  <img
                    src={`https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&h=600&fit=crop&crop=faces`}
                    alt="Team collaboration"
                    className="w-full h-96 object-cover rounded-3xl shadow-2xl"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent rounded-3xl"></div>
                  
                  {/* Play button overlay */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Button 
                      size="lg"
                      className="rounded-full w-20 h-20 text-white shadow-2xl hover:scale-110 transition-all"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      <Play className="h-8 w-8 ml-1" />
                    </Button>
                  </div>
                </div>
                
                {/* Floating elements */}
                <div 
                  className="absolute -top-6 -right-6 w-24 h-24 rounded-3xl flex items-center justify-center text-white shadow-xl"
                  style={{ background: 'var(--brand-gradient)' }}
                >
                  <Award className="h-12 w-12" />
                </div>
                <div 
                  className="absolute -bottom-6 -left-6 w-20 h-20 rounded-2xl flex items-center justify-center bg-white shadow-xl"
                >
                  <Star className="h-8 w-8" style={{ color: brandColors[0] }} />
                </div>
              </div>
            </div>

            {/* Competitive Advantages */}
            <div className="grid md:grid-cols-3 gap-8">
              {analysis.competitive_advantages?.map((advantage, index) => (
                <Card key={index} className="border-border/50 bg-card shadow-card hover:shadow-xl transition-all hover:border-primary/30 group relative overflow-hidden">
                  <div 
                    className="absolute top-0 left-0 w-full h-1"
                    style={{ background: 'var(--brand-gradient)' }}
                  ></div>
                  <CardContent className="p-8 text-center">
                    <div 
                      className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      {getAdvantageIcon(index)}
                    </div>
                    <h3 className="font-bold text-foreground mb-4 text-xl">{advantage}</h3>
                    <p className="text-muted-foreground leading-relaxed">
                      Experience the benefits of our {advantage.toLowerCase()} approach in everything we deliver for your business success.
                    </p>
                  </CardContent>
                </Card>
              )) || [
                { icon: Star, title: 'Expert Team', description: 'Our experienced professionals deliver exceptional results with deep industry knowledge.' },
                { icon: Shield, title: 'Trusted Service', description: 'Reliable and secure solutions you can count on, backed by proven track record.' },
                { icon: Zap, title: 'Fast Delivery', description: 'Quick turnaround times without compromising on quality or attention to detail.' }
              ].map((item, index) => (
                <Card key={index} className="border-border/50 bg-card shadow-card hover:shadow-xl transition-all hover:border-primary/30 group relative overflow-hidden">
                  <div 
                    className="absolute top-0 left-0 w-full h-1"
                    style={{ background: 'var(--brand-gradient)' }}
                  ></div>
                  <CardContent className="p-8 text-center">
                    <div 
                      className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform shadow-lg"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      <item.icon className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="font-bold text-foreground mb-4 text-xl">{item.title}</h3>
                    <p className="text-muted-foreground leading-relaxed">{item.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Services Section - Premium Design */}
      <section id="services" className="py-20 bg-background relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{ 
            backgroundImage: `radial-gradient(circle at 25% 25%, ${brandColors[0]}40 0%, transparent 70%), radial-gradient(circle at 75% 75%, ${brandColors[1]}40 0%, transparent 70%)` 
          }}></div>
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-7xl mx-auto">
            {/* Section Header */}
            <div className="text-center mb-16">
              <Badge 
                variant="outline" 
                className="mb-4 px-4 py-2 text-sm font-medium"
                style={{ 
                  borderColor: brandColors[0] + '40',
                  color: brandColors[0]
                }}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                Our Services
              </Badge>
              <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
                What We <span style={{ color: brandColors[0] }}>Offer</span>
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                Comprehensive solutions tailored to your unique needs in {analysis.industry}, delivered with expertise and innovation.
              </p>
            </div>

            {/* Services Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
              {analysis.key_services?.map((service, index) => (
                <Card key={index} className="border-border/50 bg-card/50 backdrop-blur-sm shadow-card hover:shadow-2xl transition-all hover:border-primary/30 group relative overflow-hidden h-full">
                  {/* Gradient overlay */}
                  <div 
                    className="absolute top-0 left-0 w-full h-full opacity-0 group-hover:opacity-10 transition-opacity"
                    style={{ background: 'var(--brand-gradient)' }}
                  ></div>
                  
                  <CardContent className="p-8 relative z-10 h-full flex flex-col">
                    <div className="flex-1">
                      <div 
                        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-all shadow-lg"
                        style={{ backgroundColor: brandColors[0] + '20' }}
                      >
                        {getServiceIcon(index)}
                      </div>
                      <h3 className="font-bold text-foreground mb-4 text-xl group-hover:text-primary transition-colors">{service}</h3>
                      <p className="text-muted-foreground mb-6 leading-relaxed">
                        Professional {service.toLowerCase()} solutions designed to exceed your expectations and drive meaningful results for your business.
                      </p>
                    </div>
                    
                    <div className="flex items-center justify-between pt-4 border-t border-border/50">
                      <div className="flex items-center text-sm font-medium group-hover:text-primary transition-colors">
                        Learn More 
                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                      <div className="flex space-x-1">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-3 w-3 text-yellow-400 fill-current" />
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )) || [
                { icon: Users, title: 'Consulting', description: 'Expert consultation services tailored to your business needs.' },
                { icon: TrendingUp, title: 'Strategy', description: 'Strategic planning and execution for sustainable growth.' },
                { icon: Award, title: 'Implementation', description: 'Professional implementation with ongoing support.' }
              ].map((item, index) => (
                <Card key={index} className="border-border/50 bg-card/50 backdrop-blur-sm shadow-card hover:shadow-2xl transition-all hover:border-primary/30 group relative overflow-hidden h-full">
                  <div 
                    className="absolute top-0 left-0 w-full h-full opacity-0 group-hover:opacity-10 transition-opacity"
                    style={{ background: 'var(--brand-gradient)' }}
                  ></div>
                  
                  <CardContent className="p-8 relative z-10 h-full flex flex-col">
                    <div className="flex-1">
                      <div 
                        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-all shadow-lg"
                        style={{ backgroundColor: brandColors[0] + '20' }}
                      >
                        <item.icon className="h-8 w-8" style={{ color: brandColors[0] }} />
                      </div>
                      <h3 className="font-bold text-foreground mb-4 text-xl group-hover:text-primary transition-colors">{item.title}</h3>
                      <p className="text-muted-foreground mb-6 leading-relaxed">{item.description}</p>
                    </div>
                    
                    <div className="flex items-center justify-between pt-4 border-t border-border/50">
                      <div className="flex items-center text-sm font-medium group-hover:text-primary transition-colors">
                        Learn More 
                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                      <div className="flex space-x-1">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-3 w-3 text-yellow-400 fill-current" />
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Process Steps */}
            <div className="bg-gradient-to-r from-card to-card/50 rounded-3xl p-8 md:p-12 border border-border/50">
              <div className="text-center mb-12">
                <h3 className="text-2xl md:text-3xl font-bold text-foreground mb-4">Our Process</h3>
                <p className="text-muted-foreground max-w-2xl mx-auto">
                  We follow a proven methodology to ensure exceptional results for every project.
                </p>
              </div>

              <div className="grid md:grid-cols-4 gap-8">
                {[
                  { title: 'Discovery', description: 'Understanding your needs and goals', icon: Target },
                  { title: 'Planning', description: 'Strategic roadmap development', icon: Lightbulb },
                  { title: 'Execution', description: 'Professional implementation', icon: Rocket },
                  { title: 'Success', description: 'Results and ongoing support', icon: Award }
                ].map((step, index) => (
                  <div key={index} className="text-center relative">
                    <div 
                      className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 text-white shadow-xl"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      <step.icon className="h-8 w-8" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-primary text-white text-sm font-bold flex items-center justify-center">
                      {index + 1}
                    </div>
                    <h4 className="font-semibold text-foreground mb-2">{step.title}</h4>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                    
                    {/* Connection line */}
                    {index < 3 && (
                      <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-primary/50 to-transparent transform -translate-x-4"></div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      {analysis.social_proof_elements?.includes('testimonials') && (
        <section className="py-20 bg-surface">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <Badge variant="outline" className="mb-4 border-primary/20 text-primary">Testimonials</Badge>
                <h2 className="text-3xl font-bold text-foreground mb-4">What Our Clients Say</h2>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {dynamicTestimonials.map((testimonial, index) => (
                  <Card key={index} className="border-border/50 bg-card shadow-card">
                    <CardContent className="p-6">
                      <div className="flex mb-4">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                        ))}
                      </div>
                      <p className="text-muted-foreground mb-4 italic">"{testimonial.content || testimonial.feedback}"</p>
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center mr-3">
                          <span className="text-primary font-semibold">{testimonial.name.charAt(0)}</span>
                        </div>
                        <div>
                          <div className="font-semibold text-foreground">{testimonial.name}</div>
                          <div className="text-sm text-muted-foreground">{testimonial.role || testimonial.company}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* CTA Section - Premium Design */}
      <section className="py-24 bg-gradient-to-br from-background via-surface to-background relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0">
          <div 
            className="absolute top-0 left-0 w-96 h-96 rounded-full opacity-10 blur-3xl"
            style={{ background: 'var(--brand-gradient)' }}
          ></div>
          <div 
            className="absolute bottom-0 right-0 w-80 h-80 rounded-full opacity-10 blur-3xl"
            style={{ background: `linear-gradient(135deg, ${brandColors[1]}, ${brandColors[2] || brandColors[0]})` }}
          ></div>
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-5xl mx-auto">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-2xl overflow-hidden">
              <CardContent className="p-0">
                <div className="grid lg:grid-cols-2 gap-0">
                  {/* Content Side */}
                  <div className="p-12 lg:p-16 flex flex-col justify-center">
                    <Badge 
                      variant="outline" 
                      className="w-fit mb-6 px-4 py-2 text-sm font-medium"
                      style={{ 
                        borderColor: brandColors[0] + '40',
                        color: brandColors[0]
                      }}
                    >
                      <Sparkles className="h-4 w-4 mr-2" />
                      Get Started Today
                    </Badge>
                    
                    <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6 leading-tight">
                      Ready to Transform Your 
                      <span style={{ color: brandColors[0] }}> Business</span>?
                    </h2>
                    
                    <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                      Join hundreds of satisfied clients who have achieved remarkable results with {brandName}. 
                      Let's discuss how we can help you reach your goals in {analysis.industry}.
                    </p>

                    {/* Dynamic Stats */}
                    <div className="grid grid-cols-3 gap-6 mb-8">
                      {dynamicStats.map((stat, index) => (
                        <div key={index} className="text-center">
                          <div className="text-2xl font-bold" style={{ color: brandColors[0] }}>{stat.value}</div>
                          <div className="text-sm text-muted-foreground">{stat.label}</div>
                        </div>
                      ))}
                    </div>

                    <div className="flex flex-col sm:flex-row gap-4 mb-8">
                      <Button 
                        size="lg"
                        className="text-white font-semibold shadow-xl hover:shadow-2xl transition-all hover:scale-105"
                        style={{ background: 'var(--brand-gradient)' }}
                      >
                        Start Your Journey
                        <ArrowRight className="ml-2 h-5 w-5" />
                      </Button>
                      <Button 
                        size="lg"
                        variant="outline"
                        className="border-primary/30 hover:border-primary/50 hover:bg-primary/5 transition-all"
                      >
                        <Phone className="mr-2 h-5 w-5" />
                        Book a Call
                      </Button>
                    </div>

                    {/* Trust Indicators */}
                    <div className="flex items-center pt-6 border-t border-border/50">
                      <div className="flex items-center space-x-1 mr-6">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                        ))}
                        <span className="ml-2 text-sm font-medium text-foreground">4.9/5 Rating</span>
                      </div>
                      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                        <Shield className="h-4 w-4" />
                        <span>Trusted & Secure</span>
                      </div>
                    </div>
                  </div>

                  {/* Visual Side */}
                  <div className="relative bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 p-12 lg:p-16 flex items-center justify-center">
                    <div className="relative w-full max-w-md">
                      {/* Main visual element */}
                      <div 
                        className="w-64 h-64 mx-auto rounded-3xl shadow-2xl relative overflow-hidden"
                        style={{ 
                          background: 'var(--brand-gradient)',
                        }}
                      >
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-center text-white">
                            <Rocket className="h-16 w-16 mx-auto mb-4 animate-pulse" />
                            <div className="text-2xl font-bold">Launch Success</div>
                            <div className="text-sm opacity-90">with {brandName}</div>
                          </div>
                        </div>
                      </div>

                      {/* Floating elements */}
                      <div className="absolute -top-4 -right-4 w-20 h-20 bg-white rounded-2xl shadow-xl flex items-center justify-center animate-bounce">
                        <TrendingUp className="h-8 w-8" style={{ color: brandColors[0] }} />
                      </div>
                      <div className="absolute -bottom-4 -left-4 w-16 h-16 bg-white rounded-xl shadow-xl flex items-center justify-center animate-pulse">
                        <Award className="h-6 w-6" style={{ color: brandColors[0] }} />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer - Enhanced Design */}
      <footer className="bg-gradient-to-b from-background to-card border-t border-border/50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          {/* Main Footer Content */}
          <div className="py-16">
            <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-12">
              {/* Brand Column */}
              <div className="space-y-6">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-xl font-bold shadow-lg"
                    style={{ background: 'var(--brand-gradient)' }}
                  >
                    {brandName.charAt(0)}
                  </div>
                  <div className="text-2xl font-bold text-foreground">{brandName}</div>
                </div>
                <p className="text-muted-foreground leading-relaxed max-w-sm">
                  {brandDescription || `Leading the way in ${analysis.industry} with innovative solutions and exceptional service.`}
                </p>
                <div className="flex space-x-4">
                  {[
                    { icon: Facebook, href: '#' },
                    { icon: Twitter, href: '#' },
                    { icon: Linkedin, href: '#' },
                    { icon: Instagram, href: '#' }
                  ].map((social, index) => (
                    <Button
                      key={index}
                      size="sm"
                      variant="outline"
                      className="w-10 h-10 rounded-xl p-0 border-border/50 hover:border-primary/30 hover:bg-primary/5 transition-all"
                    >
                      <social.icon className="h-4 w-4" />
                    </Button>
                  ))}
                </div>
              </div>

              {/* Services Column */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-6">Services</h3>
                <ul className="space-y-3">
                  {(analysis.key_services?.slice(0, 6) || ['Consulting', 'Strategy', 'Implementation', 'Support', 'Training', 'Maintenance']).map((service, index) => (
                    <li key={index}>
                      <Button 
                        variant="ghost" 
                        className="p-0 h-auto font-normal text-muted-foreground hover:text-foreground hover:bg-transparent transition-colors"
                      >
                        {service}
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Company Column */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-6">Company</h3>
                <ul className="space-y-3">
                  {['About Us', 'Our Team', 'Careers', 'News', 'Partners', 'Contact'].map((item, index) => (
                    <li key={index}>
                      <Button 
                        variant="ghost" 
                        className="p-0 h-auto font-normal text-muted-foreground hover:text-foreground hover:bg-transparent transition-colors"
                      >
                        {item}
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Contact Column */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-6">Get In Touch</h3>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <MapPin className="h-5 w-5 text-primary mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                      123 Business Street<br />
                      City, State 12345
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Phone className="h-5 w-5 text-primary" />
                    <div className="text-sm text-muted-foreground">+1 (555) 123-4567</div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Mail className="h-5 w-5 text-primary" />
                    <div className="text-sm text-muted-foreground">hello@{brandName.toLowerCase().replace(/\s+/g, '')}.com</div>
                  </div>
                </div>

                {/* Newsletter */}
                <div className="mt-8 p-4 bg-card rounded-xl border border-border/50">
                  <h4 className="font-medium text-foreground mb-2">Stay Updated</h4>
                  <p className="text-xs text-muted-foreground mb-3">Get the latest news and updates.</p>
                  <div className="flex space-x-2">
                    <input 
                      type="email" 
                      placeholder="Enter email"
                      className="flex-1 px-3 py-2 text-sm bg-background border border-border/50 rounded-lg focus:outline-none focus:border-primary/50 transition-colors"
                    />
                    <Button 
                      size="sm"
                      className="text-white shadow-md"
                      style={{ background: 'var(--brand-gradient)' }}
                    >
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Footer */}
          <div className="py-8 border-t border-border/50">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <div className="text-sm text-muted-foreground">
                © {new Date().getFullYear()} {brandName}. All rights reserved.
              </div>
              <div className="flex items-center space-x-6">
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="text-sm text-muted-foreground hover:text-foreground p-0 h-auto"
                >
                  Privacy Policy
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="text-sm text-muted-foreground hover:text-foreground p-0 h-auto"
                >
                  Terms of Service
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="text-sm text-muted-foreground hover:text-foreground p-0 h-auto"
                >
                  Cookies
                </Button>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
