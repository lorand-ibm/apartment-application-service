from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apartment.api.views import ApartmentAPIView, ProjectAPIView
from invoicing.api.views import ProjectInstallmentTemplateAPIView

router = DefaultRouter()

urlpatterns = [
    path("sales/apartments/", ApartmentAPIView.as_view(), name="apartment-list"),
    path(
        "sales/projects/",
        ProjectAPIView.as_view(),
        name="project-list",
    ),
    path(
        "sales/projects/<uuid:project_uuid>/",
        ProjectAPIView.as_view(),
        name="project-detail",
    ),
    path(
        "sales/projects/<uuid:project_uuid>/installment_templates/",
        ProjectInstallmentTemplateAPIView.as_view(),
        name="project-installment-template-list",
    ),
    path("", include(router.urls)),
]
