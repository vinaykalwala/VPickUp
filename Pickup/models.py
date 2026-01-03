from django.db import models

class HomeSlider(models.Model):
    title = models.CharField(max_length=150,blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='sliders/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"Slider #{self.id}"

from django.db import models

class PromotionalBanner(models.Model):
    title = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promotional Banner'
        verbose_name_plural = 'Promotional Banners'

    def __str__(self):
        return self.title or f"Banner #{self.id}"