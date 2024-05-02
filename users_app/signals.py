from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from .models import User


@receiver(post_save, sender=User)
def crop_user_image(*args, **kwargs):
    instance = kwargs['instance']
    image = instance.image
    if image:
        image = Image.open(image.path)
        if image.height > instance.MAX_IMAGE_HEIGHT or image.width > instance.MAX_IMAGE_WIDTH:
            image.thumbnail((instance.MAX_IMAGE_HEIGHT, instance.MAX_IMAGE_WIDTH))
            image.save(instance.image.path)
