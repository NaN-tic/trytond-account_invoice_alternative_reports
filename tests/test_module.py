
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class AccountInvoiceAlternativeReportsTestCase(CompanyTestMixin, ModuleTestCase):
    'Test AccountInvoiceAlternativeReports module'
    module = 'account_invoice_alternative_reports'
    extras = ['account_invoice_jreport_cache', 'html_report']


del ModuleTestCase
