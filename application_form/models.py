from django.db import models
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

CURRENT_HOUSING_CHOICES = [
    ("Omistusasunto", "Omistusasunto"),
    ("Vuokra-asunto", "Vuokra-asunto"),
    ("Asumisoikeusasunto", "Asumisoikeusasunto"),
    ("Muu", "Muu"),
]

HASO_PERMISSIONS_LIST = [
    ("haso_create", _("Can create new haso applications.")),
    ("haso_update", _("Can update the existing haso applications.")),
    ("haso_delete", _("Can remove remove the existing haso applications.")),
]

HITAS_PERMISSIONS_LIST = [
    ("hitas_create", _("Can create new hitas applications.")),
    ("hitas_update", _("Can update the existing hitas applications.")),
    ("hitas_delete", _("Can remove remove the existing hitas applications.")),
]


class Apartment(models.Model):
    apartment_uuid = models.UUIDField(
        verbose_name=_("apartment uuid"), primary_key=True
    )
    is_available = models.BooleanField(default=True, verbose_name=_("is available"))
    history = HistoricalRecords()

    @property
    def haso_application_id_queue(self):
        return list(
            HasoApartmentPriority.objects.filter(
                is_active=True,
                apartment=self,
            )
            .order_by("haso_application__right_of_occupancy_id")
            .values_list("haso_application__right_of_occupancy_id", flat=True)
        )

    @property
    def hitas_application_queue(self):
        return HitasApplication.objects.filter(
            apartment=self,
        ).order_by("order")


class ApplicationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_rejected=False, applicant_has_accepted_offer=False)

    def non_approved(self):
        return self.filter(
            is_approved=False, is_rejected=False, applicant_has_accepted_offer=False
        )

    def approved(self):
        return self.filter(is_approved=True, applicant_has_accepted_offer=False)

    def accepted(self):
        return self.filter(applicant_has_accepted_offer=True)

    def rejected(self):
        return self.filter(is_rejected=True)


class ApplicationMixin(models.Model):
    is_approved = models.BooleanField(default=False, verbose_name=_("is accepted"))
    is_rejected = models.BooleanField(default=False, verbose_name=_("is rejected"))
    rejection_description = models.TextField(
        default="",
        verbose_name=_("rejection description"),
        blank=True,
    )
    applicant_has_accepted_offer = models.BooleanField(
        default=False, verbose_name=_("applicant has accepted offer")
    )
    applicant_token = models.CharField(
        max_length=200,
        verbose_name=_("applicant token"),
        help_text=_(
            "a token that can be associated with the applicant's user information."
        ),
    )
    history = HistoricalRecords(inherit=True)

    objects = ApplicationQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.is_approved and self.is_rejected:
            raise ValueError(
                _("application cannot be accepted and rejected at the same time.")
            )
        if self.applicant_has_accepted_offer and not self.is_approved:
            raise ValueError(
                _("the offer cannot be accepted before the application is approved.")
            )
        super(ApplicationMixin, self).save(**kwargs)

    def reject(self, rejection_description: str):
        self.is_approved = False
        self.is_rejected = True
        self.rejection_description = rejection_description
        self._change_reason = _("application rejected.")
        self.save()

    def approve(self) -> None:
        self.is_approved = True
        self._change_reason = _("application approved.")
        self.save()


class HasoApplication(ApplicationMixin):
    right_of_occupancy_id = models.IntegerField(verbose_name=_("right of occupancy ID"))
    current_housing = models.CharField(
        max_length=255,
        choices=CURRENT_HOUSING_CHOICES,
        verbose_name=_("current housing"),
    )
    housing_description = models.TextField(verbose_name=_("housing description"))
    housing_type = models.CharField(max_length=255, verbose_name=_("housing type"))
    housing_area = models.FloatField(verbose_name=_("housing area"))
    is_changing_occupancy_apartment = models.BooleanField(
        default=False, verbose_name=_("is changing occupancy apartment")
    )
    is_over_55 = models.BooleanField(
        default=False, verbose_name=_("is applicant over 55 years old")
    )

    @property
    def apartment_uuids(self):
        return list(
            HasoApartmentPriority.objects.filter(haso_application=self)
            .order_by("priority_number")
            .values_list("apartment__apartment_uuid", flat=True)
        )


class HasoApartmentPriority(models.Model):
    is_active = models.BooleanField(default=True, verbose_name=_("is active"))
    priority_number = models.IntegerField(verbose_name=_("priority number"))
    haso_application = models.ForeignKey(
        HasoApplication,
        on_delete=models.CASCADE,
        related_name="haso_apartment_priorities",
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="haso_apartment_priorities",
    )
    history = HistoricalRecords()

    class Meta:
        permissions = HASO_PERMISSIONS_LIST


class HitasApplication(ApplicationMixin):
    has_previous_hitas_apartment = models.BooleanField(
        default=False, verbose_name=_("has previous hitas apartment")
    )
    previous_hitas_description = models.TextField(
        verbose_name=_("previous hitas descripiton")
    )
    has_children = models.BooleanField(default=False, verbose_name=_("has children"))
    apartment = models.ForeignKey(
        Apartment, on_delete=models.CASCADE, related_name="hitas_applications"
    )
    order = models.PositiveIntegerField(verbose_name=_("order"))

    class Meta:
        permissions = HITAS_PERMISSIONS_LIST

    def save(self, **kwargs):
        if not self.id:
            if self.__class__.objects.filter(apartment=self.apartment).exists():
                self.order = (
                    self.__class__.objects.filter(apartment=self.apartment)
                    .order_by("-order")
                    .first()
                    .order
                    + 1
                )
            else:
                self.order = 1
        super(HitasApplication, self).save(**kwargs)
