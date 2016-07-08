# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .invoice import *
from .configuration import *


def register():
    Pool.register(
        AccountConfiguration,
        AccountConfigurationCompany,
        Invoice,
        PartyAlternativeReport,
        module='account_invoice_alternative_reports', type_='model')
    Pool.register(
        PrintInvoice,
        module='account_invoice_alternative_reports', type_='wizard')
    Pool.register(
        InvoiceReport,
        module='account_invoice_alternative_reports', type_='report')
