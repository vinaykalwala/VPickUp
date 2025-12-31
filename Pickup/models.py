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
