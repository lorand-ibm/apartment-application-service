import dataclasses
from datetime import date
from decimal import Decimal
from io import BytesIO
from num2words import num2words
from typing import ClassVar, Dict, Union

from apartment.elastic.queries import get_apartment
from apartment_application_service.pdf import create_pdf, PDFCurrencyField, PDFData
from apartment_application_service.utils import SafeAttributeObject
from application_form.models import ApartmentReservation
from invoicing.enums import InstallmentType

HASO_CONTRACT_PDF_TEMPLATE_FILE_NAME = "haso_contract_template.pdf"


@dataclasses.dataclass
class HasoContractPDFData(PDFData):
    alterations: Union[str, None]
    apartment_number: Union[str, None]
    apartment_structure: Union[str, None]
    approval_date: Union[str, None]
    floor: Union[int, None]
    index_increment: Union[Decimal, None]
    installment_amount: Union[PDFCurrencyField, None]
    living_area: Union[str, None]
    occupant_1: str
    occupant_1_email: str
    occupant_1_phone_number: str
    occupant_1_ssn: str
    occupant_1_street_address: str
    occupant_2: Union[str, None]
    occupant_2_email: Union[str, None]
    occupant_2_phone_number: Union[str, None]
    occupant_2_ssn: Union[str, None]
    occupant_2_street_address: Union[str, None]
    payment_due_date: Union[date, None]
    project_acc_salesperson: Union[str, None]
    project_contract_apartment_completion: Union[str, None]
    project_contract_other_terms: Union[str, None]
    project_contract_right_of_occupancy_payment_verification: Union[str, None]
    project_contract_usage_fees: Union[str, None]
    project_housing_company: Union[str, None]
    project_street_address: Union[str, None]
    right_of_occupancy_fee: Union[PDFCurrencyField, None]
    right_of_occupancy_fee_m2: Union[PDFCurrencyField, None]
    right_of_occupancy_payment: Union[PDFCurrencyField, None]
    right_of_occupancy_payment_text: Union[str, None]
    right_of_residence_number: Union[str, None]
    signing_place: str
    signing_text: str
    signing_time: Union[str, None]

    FIELD_MAPPING: ClassVar[Dict[str, str]] = {
        "alterations": "Muutostyöt",
        "apartment_number": "Huoneiston numero",
        "apartment_structure": "Huoneistotyyppi",
        "approval_date": "Hyväksymispäivämäärä",
        "floor": "Sijaintikerros",
        "index_increment": "Indeksikorotus",
        "installment_amount": "Maksuerän suuruus",
        "living_area": "Huoneiston pinta-ala",
        "occupant_1": "Asumisoikeuden haltija 1",
        "occupant_1_email": "Haltija 1 sähköposti",
        "occupant_1_phone_number": "Haltija 1 puhelinnumero",
        "occupant_1_ssn": "Haltija 1 henkilötunnus",
        "occupant_1_street_address": "Haltija 1 osoite",
        "occupant_2": "Asumisoikeuden haltija 2",
        "occupant_2_email": "Haltija 2 sähköposti",
        "occupant_2_phone_number": "Haltija 2 puhelinnumero",
        "occupant_2_ssn": "Haltija 2 henkilötunnus",
        "occupant_2_street_address": "Haltija 2 osoite",
        "payment_due_date": "Eräpäivä maksulle",
        "project_acc_salesperson": "rakennuttaja-asimies",
        "project_contract_apartment_completion": "Valmistumisaika",
        "project_contract_other_terms": "Muut ehdot",
        "project_contract_right_of_occupancy_payment_verification": "Lisätietokenttä",
        "project_contract_usage_fees": "Vapaakenttä käyttövastike",
        "project_housing_company": "Kohteen nimi",
        "project_street_address": "Kohteen osoite",
        "right_of_occupancy_fee": "Käyttövastike",
        "right_of_occupancy_fee_m2": "Käyttövastike asuinneliö",
        "right_of_occupancy_payment": "Alkuperäinen asumisoikeusmaksu",
        "right_of_occupancy_payment_text": "Alkuperäinen asumisoikeusmaksu tekstinä",
        "right_of_residence_number": "järjestysnumero",
        "signing_place": "Paikka",
        "signing_text": "Sopimus oikeaksi todistetaan",
        "signing_time": "Aika",
    }


def create_haso_contract_pdf(reservation: ApartmentReservation) -> BytesIO:
    customer = SafeAttributeObject(
        reservation.application_apartment.application.customer
    )
    primary_profile = SafeAttributeObject(customer.primary_profile)
    secondary_profile = SafeAttributeObject(customer.secondary_profile)
    apartment = get_apartment(reservation.apartment_uuid, include_project_fields=True)

    first_payment = SafeAttributeObject(
        reservation.apartment_installments.filter(
            type=InstallmentType.PAYMENT_1
        ).first()
    )

    completion_start = apartment.project_contract_apartment_completion_selection_2_start
    completion_start_str = (
        completion_start.strftime("%-d.%-m.%Y") if completion_start else ""
    )
    completion_end = apartment.project_contract_apartment_completion_selection_2_end
    completion_end_str = completion_end.strftime("%-d.%-m.%Y") if completion_end else ""

    right_of_occupancy_fee_m2_euros = (
        Decimal(apartment.right_of_occupancy_fee / 100.0 / apartment.living_area)
        if apartment.right_of_occupancy_fee is not None
        else None
    )

    pdf_data = HasoContractPDFData(
        occupant_1=primary_profile.full_name,
        occupant_1_street_address=primary_profile.street_address,
        occupant_1_phone_number=primary_profile.phone_number,
        occupant_1_email=primary_profile.email,
        occupant_1_ssn=primary_profile.national_identification_number,
        occupant_2=secondary_profile.full_name,
        occupant_2_street_address=secondary_profile.street_address,
        occupant_2_phone_number=secondary_profile.phone_number,
        occupant_2_email=secondary_profile.email,
        occupant_2_ssn=secondary_profile.national_identification_number,
        right_of_residence_number=customer.right_of_residence,
        project_housing_company=apartment.project_housing_company,
        project_street_address=apartment.project_street_address,
        apartment_number=apartment.apartment_number,
        apartment_structure=apartment.apartment_structure,
        living_area=apartment.living_area,
        floor=apartment.floor,
        right_of_occupancy_payment=PDFCurrencyField(
            cents=apartment.right_of_occupancy_payment, suffix=" €"
        ),
        right_of_occupancy_payment_text=num2words(
            Decimal(apartment.right_of_occupancy_payment) / 100, lang="fi"
        )
        if apartment.right_of_occupancy_payment is not None
        else None,
        payment_due_date=first_payment.due_date,
        installment_amount=PDFCurrencyField(euros=first_payment.value),
        right_of_occupancy_fee=PDFCurrencyField(
            cents=apartment.right_of_occupancy_fee, suffix=" € / kk"
        ),
        right_of_occupancy_fee_m2=PDFCurrencyField(
            euros=right_of_occupancy_fee_m2_euros, suffix=" € /m\u00b2/kk"
        ),
        project_contract_apartment_completion=(
            f"{completion_start_str} — {completion_end_str}"
            if completion_start_str or completion_end_str
            else ""
        ),
        signing_place="Helsingin kaupunki",
        project_acc_salesperson=apartment.project_acc_salesperson,
        project_contract_other_terms=apartment.project_contract_other_terms,
        project_contract_usage_fees=apartment.project_contract_usage_fees,
        project_contract_right_of_occupancy_payment_verification=apartment.project_contract_right_of_occupancy_payment_verification,  # noqa E501
        # TODO the following fields are still WIP
        signing_text="Sopimus oikeaksi todistetaan",
        signing_time=None,
        approval_date=None,
        alterations=None,
        index_increment=None,
    )

    return create_pdf(HASO_CONTRACT_PDF_TEMPLATE_FILE_NAME, pdf_data)
