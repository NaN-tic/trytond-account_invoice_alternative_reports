# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.modules.jasper_reports.jasper import JasperReport

__all__ = ['Invoice', 'PartyAlternativeReport', 'InvoiceReport']


class PartyAlternativeReport(metaclass=PoolMeta):
    __name__ = 'party.alternative_report'

    @classmethod
    def __setup__(cls):
        super(PartyAlternativeReport, cls).__setup__()
        option = ('account.invoice', 'Invoice')
        if option not in cls.model_name.selection:
            cls.model_name.selection.append(option)


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    available_reports = fields.Function(fields.Many2Many('ir.action.report',
            None, None, 'Available Reports'),
        'get_available_reports')
    invoice_action_report = fields.Many2One('ir.action.report',
        'Report Template', domain=[
            If(Eval('state') == 'draft',
                ('id', 'in', Eval('available_reports', [])),
                ()),
            ],
        states={
            'required': ~Eval('state').in_(['draft', 'cancel']),
            'readonly': Eval('state').in_(['posted', 'paid', 'cancel']),
            }, depends=['available_reports', 'state'])

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

    def get_available_reports(self, name=None):
        if not self.party:
            return []

        alternative_reports = self.alternative_reports
        default_report = self.default_invoice_action_report()
        if default_report and default_report not in alternative_reports:
            alternative_reports.append(default_report)
        return alternative_reports

    @fields.depends('invoice_action_report')
    def on_change_party(self):
        super(Invoice, self).on_change_party()
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

    def print_invoice(self):
        '''
        Generate invoice report and store it in invoice_report_cache field.
        '''
        pool = Pool()
        if self.invoice_report_cache:
            return
        assert self.invoice_action_report, (
            "Missing Invoice Report in invoice %s (%s)"
            % (self.rec_name, self.id))
        InvoiceReport = pool.get(self.invoice_action_report.report_name,
            type='report')
        InvoiceReport.execute([self.id], {})


class InvoiceReport(metaclass=PoolMeta):
    __name__ = 'account.invoice.jreport'

    @classmethod
    def execute(cls, ids, data):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Report = pool.get('ir.action.report')
        Config = pool.get('account.configuration')
        config = Config(1)

        action_report = (config and config.invoice_action_report and
            config.invoice_action_report.id or None)
        reports = {}
        for id_ in ids:
            invoice = Invoice(id_)
            if invoice.invoice_action_report:
                if invoice.invoice_action_report not in reports:
                    reports[invoice.invoice_action_report] = [invoice.id]
                else:
                    reports[invoice.invoice_action_report].append(invoice.id)
            else:
                if action_report not in reports:
                    reports[action_report] = [invoice.id]
                else:
                    reports[action_report].append(invoice.id)

        if not reports:
            raise Exception('Error', 'Report (%s) not find!' % cls.__name__)
        cls.check_access()
        type, content, pages = cls.multirender(reports, data)
        if not isinstance(content, str):
            content = bytearray(content) if bytes == str else bytes(content)
        report = Report(list(reports.keys())[0])

        if Transaction().context.get('return_pages'):
            return (type, content, report.direct_print, report.name, pages)
        return (type, content, report.direct_print, report.name)

    @classmethod
    def multirender(cls, reports, data):
        pool = Pool()
        Report = pool.get('ir.action.report')
        allpages = 0
        invoice_reports_cache = []
        for report_id, ids in reports.items():
            report = Report(report_id)
            model = report.model or data.get('model')
            cls.update_data(report, data)
            type, data_file, pages = cls.render(report, data, model, ids)
            invoice_reports_cache.append(data_file)

        if len(invoice_reports_cache) > 1:
            alldata = JasperReport.merge_pdfs(invoice_reports_cache)
        else:
            alldata = invoice_reports_cache[0]
        return (type, alldata, allpages)

    @classmethod
    def update_data(cls, report, data):
        pass


