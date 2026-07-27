# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from io import BytesIO
import zipfile

from trytond.model import fields, dualmethod
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.tools import slugify
from trytond.transaction import Transaction


class PartyAlternativeReport(metaclass=PoolMeta):
    __name__ = 'party.alternative_report'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        option = ('account.invoice', 'Invoice')
        if option not in cls.model_name.selection:
            cls.model_name.selection.append(option)


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    available_reports = fields.Function(fields.Many2Many('ir.action.report',
            None, None, 'Available Reports'),
        'on_change_with_available_reports')
    invoice_action_report = fields.Many2One('ir.action.report',
        'Invoice Report Template', domain=[
            If(Eval('state') == 'draft',
                ('id', 'in', Eval('available_reports', [])),
                ()),
            ],
        states={
            'required': ~Eval('state').in_(['draft', 'cancelled']),
            'readonly': Eval('state').in_(['posted', 'paid', 'cancelled']),
            })

    @staticmethod
    def default_invoice_action_report():
        Config = Pool().get('account.configuration')
        config = Config(1)

        return (config and config.invoice_action_report and
            config.invoice_action_report.id or None)

    @property
    def alternative_reports(self):
        if not self.party:
            return []
        return [ar.report.id for ar in self.party.alternative_reports
            if ar.model_name == 'account.invoice']

    @fields.depends('party')
    def on_change_with_available_reports(self, name=None):
        if not self.party:
            return []

        alternative_reports = self.alternative_reports
        default_report = self.default_invoice_action_report()
        if default_report and default_report not in alternative_reports:
            alternative_reports.append(default_report)
        return alternative_reports

    @fields.depends('invoice_action_report')
    def on_change_party(self):
        super().on_change_party()
        if not self.party:
            self.invoice_action_report = self.default_invoice_action_report()
            return
        alternative_reports = self.alternative_reports
        if alternative_reports and len(alternative_reports) == 1:
            self.invoice_action_report = alternative_reports[0]
        elif alternative_reports and len(alternative_reports) > 1:
            # force the user to choose one
            self.invoice_action_report = None
        elif not self.invoice_action_report:
            self.invoice_action_report = self.default_invoice_action_report()

    @dualmethod
    def print_invoice(cls, invoices):
        '''
        Generate invoice report and store it in invoice_report_cache field.
        '''
        pool = Pool()
        InvoiceReport = pool.get('account.invoice', type='report')
        for invoice in invoices:
            if invoice.invoice_report_cache:
                return
            assert invoice.invoice_action_report, (
                "Missing Invoice Report in invoice %s (%s)"
                % (invoice.rec_name, invoice.id))
            InvoiceReport.execute([invoice.id], {})


class InvoiceReport(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def _build_zip_result(cls, reports):
        content = BytesIO()
        with zipfile.ZipFile(content, 'w') as content_zip:
            for i, (extension, data, _, name) in enumerate(reports, 1):
                filename = slugify(name or '%s-%s' % (cls.__name__, i))
                content_zip.writestr('%s.%s' % (filename, extension), data)
        return ('zip', content.getvalue(), False, reports[0][3])

    @classmethod
    def execute(cls, ids, data):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Config = pool.get('account.configuration')

        if data is None:
            data = {}

        config = Config(1)

        reports = []
        for invoice in Invoice.browse(ids):
            action_report_id = (
                (invoice.invoice_action_report and invoice.invoice_action_report.id)
                or (config.invoice_action_report and config.invoice_action_report.id)
                or data.get('action_id'))

            if not action_report_id:
                raise Exception('Error', 'Report (%s) not find!' % cls.__name__)

            invoice_data = data.copy()
            invoice_data['action_id'] = action_report_id
            action, _ = cls.get_action(invoice_data)
            if invoice.invoice_report_cache:
                result = (
                    invoice.invoice_report_format,
                    bytes(invoice.invoice_report_cache),
                    cls.get_direct_print(action),
                    cls.get_name(action))
            else:
                if action and action.report_name != cls.__name__:
                    Report = pool.get(action.report_name, type='report')
                    result = Report.execute([invoice.id], invoice_data)
                else:
                    result = super().execute([invoice.id], invoice_data)

                if (invoice.state in {'posted', 'paid'}
                        and invoice.type == 'out'):
                    with Transaction().set_context(_check_access=False):
                        format_, report_data = result[0], result[1]
                        invoice.invoice_report_format = format_
                        invoice.invoice_report_cache = \
                            Invoice.invoice_report_cache.cast(report_data)
                        invoice.save()

            reports.append(result)

        if not reports:
            return super().execute(ids, data)
        if len(ids) > 1:
            if all(report[0] == 'pdf' for report in reports):
                return (
                    'pdf',
                    cls.merge_pdfs([bytes(report[1]) for report in reports]),
                    all(report[2] for report in reports),
                    reports[0][3])
            return cls._build_zip_result(reports)
        return reports[0]
