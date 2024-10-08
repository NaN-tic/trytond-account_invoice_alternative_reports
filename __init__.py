# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
from . import configuration


def register():
    Pool.register(
        configuration.AccountConfiguration,
        configuration.AccountConfigurationCompany,
        invoice.Invoice,
        invoice.PartyAlternativeReport,
        module='account_invoice_alternative_reports', type_='model')
    Pool.register(
        invoice.InvoiceReport,
        module='account_invoice_alternative_reports', type_='report',
        depends=['account_invoice_jreport_cache'])
    Pool.register(
        invoice.InvoiceReportHTML,
        module='account_invoice_alternative_reports', type_='report',
        depends=['html_report'])
