from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import Computer, Reservation, Session


@receiver(post_save, sender=Session)
def session_saved(sender, instance, **kwargs):
    """Session saqlanganda kompyuter holatini yangilash."""
    if instance.computer_id:
        if instance.status == 'active':
            Computer.objects.filter(pk=instance.computer_id).update(status='occupied')
        elif instance.status in ('completed', 'cancelled'):
            # Kompyuter boshqa faol sessiyaga ega emasligini tekshirish
            has_active = Session.objects.filter(
                computer_id=instance.computer_id, status='active'
            ).exclude(pk=instance.pk).exists()
            if not has_active:
                Computer.objects.filter(pk=instance.computer_id).update(
                    status='available'
                )


@receiver(post_delete, sender=Session)
def session_deleted(sender, instance, **kwargs):
    """Session o'chirilganda kompyuterni bo'shatish."""
    if instance.computer_id:
        has_active = Session.objects.filter(
            computer_id=instance.computer_id, status='active'
        ).exists()
        if not has_active:
            Computer.objects.filter(pk=instance.computer_id).update(status='available')


@receiver(post_save, sender=Reservation)
def reservation_saved(sender, instance, **kwargs):
    """Rezervatsiya holatiga qarab kompyuterni belgilash."""
    if instance.computer_id:
        if instance.status in ('pending', 'active'):
            Computer.objects.filter(pk=instance.computer_id).update(status='reserved')
        else:
            # Faol sessiya yoki boshqa faol rezerv yo'q bo'lsa available qilish
            has_active = Session.objects.filter(
                computer_id=instance.computer_id, status='active'
            ).exists()
            has_res = Reservation.objects.filter(
                computer_id=instance.computer_id, status__in=['pending', 'active']
            ).exists()
            if not has_active and not has_res:
                Computer.objects.filter(pk=instance.computer_id).update(
                    status='available'
                )


@receiver(post_delete, sender=Reservation)
def reservation_deleted(sender, instance, **kwargs):
    if instance.computer_id:
        has_active = Session.objects.filter(
            computer_id=instance.computer_id, status='active'
        ).exists()
        has_res = Reservation.objects.filter(
            computer_id=instance.computer_id, status__in=['pending', 'active']
        ).exists()
        if not has_active and not has_res:
            Computer.objects.filter(pk=instance.computer_id).update(status='available')
