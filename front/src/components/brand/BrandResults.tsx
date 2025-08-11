'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

interface BrandResultsProps {
  brandData: any;
  onEdit: () => void;
}

const BrandResults: React.FC<BrandResultsProps> = ({ brandData, onEdit }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading brand results...</p>
        </div>
      </div>
    );
  }

  // Defensive data access
  const brandName = brandData?.name || 'Untitled Brand';
  const brandPersonalities = brandData?.personality || [];
  const brandColors = brandData?.colors || [];
  const logoUrl = brandData?.logoUrl || null;
  const selectedPalette = brandData?.selectedPalette || null;
  const customDescription = brandData?.customDescription || null;
  const businessSummary = brandData?.businessSummary || '';
  const createdAt = brandData?.createdAt || new Date().toISOString();

  const downloadLogo = (format: 'png' | 'svg' = 'png') => {
    if (!logoUrl) {
      toast.error('No logo to download');
      return;
    }

    try {
      const link = document.createElement('a');
      link.href = logoUrl;
      link.download = `${brandName.toLowerCase().replace(/\s+/g, '_')}_logo.${format}`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success('Logo downloaded successfully!');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download logo');
    }
  };

  const shareBrand = () => {
    if (typeof window !== 'undefined' && navigator.share) {
      navigator.share({
        title: `${brandName} Brand Identity`,
        text: `Check out my new brand identity for ${brandName}!`,
        url: window.location.href,
      });
    } else if (typeof window !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    } else {
      toast.error('Sharing not supported in this browser');
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          {brandName}
        </h1>
        <p className="text-lg text-muted-foreground">{brandPersonalities.join(', ') || 'Modern Brand'}</p>
        <div className="flex justify-center gap-2">
          <Button onClick={onEdit} variant="outline" className="flex items-center gap-2">
            ✏️ Edit Brand
          </Button>
          <Button onClick={shareBrand} variant="outline" className="flex items-center gap-2">
            📤 Share
          </Button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Logo Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Brand Logo
              <Badge variant="default">AI Generated</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="aspect-square bg-gradient-to-br from-muted/50 to-muted/80 rounded-lg flex items-center justify-center p-8">
              {logoUrl ? (
                <img
                  src={logoUrl}
                  alt={`${brandName} Logo`}
                  className="max-w-full max-h-full object-contain"
                />
              ) : (
                <div className="text-muted-foreground">Logo not available</div>
              )}
            </div>
            
            <div className="flex gap-2">
              <Button 
                onClick={() => downloadLogo('png')}
                className="flex-1 flex items-center gap-2"
                disabled={!logoUrl}
              >
                📥 Download PNG
              </Button>
            </div>
            
            <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
              <p><strong>Style:</strong> {customDescription || 'AI Generated Logo'}</p>
            </div>
          </CardContent>
        </Card>

        {/* Color Palette Section */}
        <Card>
          <CardHeader>
            <CardTitle>{selectedPalette?.name || 'Color Palette'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {brandColors.length > 0 ? brandColors.map((color: string, index: number) => (
                <div key={index} className="space-y-2">
                  <div
                    className="aspect-square rounded-lg border-2 border-white dark:border-gray-800 shadow-sm"
                    style={{ backgroundColor: color }}
                  />
                  <div className="text-center">
                    <p className="text-sm font-medium">{color}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (typeof window !== 'undefined' && navigator.clipboard) {
                          navigator.clipboard.writeText(color);
                          toast.success(`Copied ${color}!`);
                        }
                      }}
                      className="text-xs h-6 px-2"
                    >
                      Copy
                    </Button>
                  </div>
                </div>
              )) : (
                <div className="col-span-2 text-center text-muted-foreground">
                  No colors available
                </div>
              )}
            </div>
            
            {selectedPalette?.description && (
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
                <p>{selectedPalette.description}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Brand Information */}
      <Card>
        <CardHeader>
          <CardTitle>Brand Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-2">Brand Personality</h3>
              <p className="text-muted-foreground">{brandPersonalities.join(', ') || 'Not specified'}</p>
            </div>
            
            {customDescription && (
              <div>
                <h3 className="font-medium mb-2">Brand Description</h3>
                <p className="text-muted-foreground">{customDescription}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BrandResults;
