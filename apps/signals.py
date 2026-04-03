from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import F

from apps.models import Announcement, Category


def update_category_count(category, delta):
    """
    Обновляет count_products у выбранной категории
    и у всех её родителей.
    delta = +1 или -1
    """
    if not category:
        return

    # сама категория + все предки
    categories = [category] + list(category.get_ancestors())

    for cat in categories:
        Category.objects.filter(pk=cat.pk).update(
            count_products=F('count_products') + delta
        )


@receiver(pre_save, sender=Announcement)
def announcement_pre_save(sender, instance, **kwargs):
    """
    Сохраняем старую категорию перед изменением,
    чтобы потом понять, поменялась она или нет.
    """
    if not instance.pk:
        instance._old_category = None
        return

    try:
        old_instance = Announcement.objects.get(pk=instance.pk)
        instance._old_category = old_instance.category
    except Announcement.DoesNotExist:
        instance._old_category = None


@receiver(post_save, sender=Announcement)
def announcement_post_save(sender, instance, created, **kwargs):
    """
    После сохранения:
    - если объект создан -> +1
    - если категория изменена -> -1 у старой, +1 у новой
    """
    if created:
        update_category_count(instance.category, +1)
    else:
        old_category = getattr(instance, '_old_category', None)
        new_category = instance.category

        if old_category != new_category:
            update_category_count(old_category, -1)
            update_category_count(new_category, +1)


@receiver(post_delete, sender=Announcement)
def announcement_post_delete(sender, instance, **kwargs):
    """
    После удаления товара -> -1
    """
    update_category_count(instance.category, -1)