====================================
Invoice Scenario Alternative Reports
====================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install account_invoice_alternative_reports::

    >>> config = activate_modules('account_invoice_alternative_reports')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> account_tax = accounts['tax']

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.account_revenue = revenue
    >>> account_category.customer_taxes.append(tax)
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('40')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create two invoice reports::

    >>> ActionReport = Model.get('ir.action.report')
    >>> invoice_report1, = ActionReport.find([('model', '=', 'account.invoice')])
    >>> invoice_report2 = ActionReport()
    >>> invoice_report2.name = 'Invoice 2'
    >>> invoice_report2.report_name = 'account.invoice2'
    >>> invoice_report2.template_extension = invoice_report1.template_extension
    >>> invoice_report2.model = invoice_report1.model
    >>> invoice_report2.save()
    >>> invoice_report3 = ActionReport()
    >>> invoice_report3.name = 'Invoice 3'
    >>> invoice_report3.report_name = 'account.invoice3'
    >>> invoice_report3.template_extension = invoice_report1.template_extension
    >>> invoice_report3.model = invoice_report1.model
    >>> invoice_report3.save()

Set default report::

    >>> Config = Model.get('account.configuration')
    >>> config = Config(1)
    >>> config.invoice_action_report = invoice_report1
    >>> config.save()

Create party without alternative report::

    >>> Party = Model.get('party.party')
    >>> party1 = Party(name='Party')
    >>> party1.save()

Create party with one alternative report::

    >>> party2 = Party(name='Party')
    >>> alternative_report = party2.alternative_reports.new()
    >>> alternative_report.model_name = 'account.invoice'
    >>> alternative_report.report = invoice_report2
    >>> party2.save()

Create party with two alternative report::

    >>> party3 = Party(name='Party')
    >>> alternative_report = party3.alternative_reports.new()
    >>> alternative_report.model_name = 'account.invoice'
    >>> alternative_report.report = invoice_report2
    >>> alternative_report = party3.alternative_reports.new()
    >>> alternative_report.model_name = 'account.invoice'
    >>> alternative_report.report = invoice_report3
    >>> party3.save()

Create invoice for party without alternative report::

    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice()
    >>> invoice.party = party1
    >>> invoice.payment_term = payment_term

Check invoice's report is default invoice report::

    >>> invoice.invoice_action_report == invoice_report1
    True

Change invoice's party to party with one alternative report::

    >>> invoice.party = party2

Check invoice's report is the alternative report::

    >>> invoice.invoice_action_report == invoice_report2
    True

Change invoice's party to party with two alternative report::

    >>> invoice.party = party3

Check invoice's report is empty::

    >>> invoice.invoice_action_report == None
    True

Remove invoice's party and check invoice's report is the default one::

    >> invoice.party = None
    >>> invoice.invoice_action_report == None
    True

Set the party with two alternative reports, set one of them as report, add
lines to invoice and post it::

    >>> invoice.party = party3
    >>> invoice.invoice_action_report = invoice_report3
    >>> line = invoice.lines.new()
    >>> line.product = product
    >>> line.quantity = 5
    >>> line.unit_price = Decimal('80.00')
    >>> line.amount
    Decimal('400.00')
    >>> invoice.save()
    >>> invoice.untaxed_amount
    Decimal('400.00')
    >>> invoice.tax_amount
    Decimal('40.00')
    >>> invoice.total_amount
    Decimal('440.00')
    >>> invoice.click('post')
    >>> invoice.state
    'posted'
