# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Product, ProductImage

@receiver(post_save, sender=Product)
def create_product_image_on_create(sender, instance: Product, created: bool, **kwargs):
    """
    When a Product is first created and it has an `image` set,
    create a ProductImage in the product gallery that points to the same file.
    """
    if not created:
        return

    if not instance.image:
        return

    # ensure DB transaction finished so storage/file is available
    def _create_gallery_image():
        # avoid duplicates if you run the signal twice for some reason
        if not ProductImage.objects.filter(product=instance, image=instance.image).exists():
            ProductImage.objects.create(product=instance, image=instance.image)

    transaction.on_commit(_create_gallery_image)
