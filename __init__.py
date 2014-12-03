# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .invoice import *


def register():
    Pool.register(
        Invoice,
        PartyAlternativeReport,
        module='account_invoice_alternative_reports', type_='model')
    Pool.register(
        PrintInvoice,
        module='account_invoice_alternative_reports', type_='wizard')
