from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, datetime
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Ad(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='ad_images/', null=True, blank=True)
    favorites = models.ManyToManyField(User, related_name='favorite_ads', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expires_at and datetime.now() > self.expires_at
    
    def __str__(self):
        return self.title

class UserRecommendation(models.Model):
    from_user = models.ForeignKey(User, related_name='given_recommendations', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_recommendations', on_delete=models.CASCADE)
    is_positive = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_reported = models.BooleanField(default=False)

    class Meta:
        unique_together = ('from_user', 'to_user')

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"{self.sender} ➡ {self.receiver} ({self.ad.title}): {self.text[:30]}"

    class Meta:
        ordering = ['created_at']
