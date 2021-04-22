import logging
from django_oikotie.oikotie import create_apartments, create_housing_companies
from elasticsearch_dsl import Search
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from connections.etuovi.services import create_xml
from connections.etuovi.services import (
    fetch_apartments_for_sale as etuovi_fetch_apartments,
)
from connections.oikotie.oikotie_mapper import (
    map_oikotie_apartment,
    map_oikotie_housing_company,
)
from connections.utils import create_elastic_connection

_logger = logging.getLogger(__name__)


class ConnectionsRPC(ViewSet):  # pragma: no cover
    """
    An RPC class for calling special prosedures via api.
    """

    permission_classes = (IsAuthenticated,)

    create_elastic_connection()

    @action(methods=["get"], detail=False, url_path="create_etuovi_xml")
    def create_etuovi_xml(self, request):
        items = etuovi_fetch_apartments()
        if create_xml(items):
            return Response(
                f"Fetched {len(items)} apartements for XML file",
                status=status.HTTP_200_OK,
            )
        else:
            return Response("Etuovi XML not created", status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="create_oikotie_xml")
    def create_oikotie_xml(self, request):
        s_obj = Search().exclude("match", _language="en")
        s_obj.execute()
        scan = s_obj.scan()
        apartments = []
        housing_companies = []

        for hit in scan:
            try:
                hc = map_oikotie_housing_company(hit)
                housing_companies.append(hc)
            except Exception as e:
                _logger.warn(f"Could not map housing company {hit.uuid}:", str(e))
                pass
            try:
                a = map_oikotie_apartment(hit)
                apartments.append(a)
            except Exception as e:
                _logger.warn(f"Could not map apartment {hit.uuid}:", str(e))
                pass
        try:
            create_housing_companies(housing_companies)
        except Exception as e:
            _logger.warn("Housing company XML not created:", {str(e)})
            return Response(
                f"Housing company XML not created : {str(e)}", status=status.HTTP_200_OK
            )

        try:
            create_apartments(apartments)
        except Exception as e:
            _logger.warn("Apartment XML not created:", {str(e)})
            return Response(
                f"Apartment XML not created : {str(e)}", status=status.HTTP_200_OK
            )

        return Response(
            f"Fetched {s_obj.count()} apartements for XML file",
            status=status.HTTP_200_OK,
        )
