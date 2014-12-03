# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Invoice', 'PartyAlternativeReport', 'PrintInvoice']
__metaclass__ = PoolMeta


class PartyAlternativeReport:
    __name__ = 'party.alternative_report'

    @classmethod
    def __setup__(cls):
        super(PartyAlternativeReport, cls).__setup__()
        option = ('account.invoice', 'Invoice')
        if option not in cls.model_name.selection:
            cls.model_name.selection.append(option)


class Invoice:
    __name__ = 'account.invoice'

    available_reports = fields.Function(fields.Many2Many('ir.action.report',
            None, None, 'Available Reports'),
        'on_change_with_available_reports')
    invoice_action_report = fields.Many2One('ir.action.report',
        'Report Template', domain=[
            ('id', 'in', Eval('available_reports', [])),
            ],
        states={
            'required': ~Eval('state').in_(['draft', 'cancel']),
            'readonly': Eval('state').in_(['posted', 'paid', 'cancel']),
            }, depends=['available_reports'])

    @staticmethod
    def default_invoice_action_report():
        pool = Pool()
        Report = pool.get('ir.action.report')

        invoice_reports = Report.search([
                ('model', '=', 'account.invoice'),
                ('action.active', '=', True),
                ])
        return invoice_reports[0].id if invoice_reports else None

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
        res = super(Invoice, self).on_change_party()
        if not self.party:
            res['invoice_action_report'] = self.default_invoice_action_report()
            return res
        alternative_reports = self.alternative_reports
        if alternative_reports and len(alternative_reports) == 1:
            res['invoice_action_report'] = alternative_reports[0]
        elif alternative_reports and len(alternative_reports) > 1:
            # force the user to choose one
            res['invoice_action_report'] = None
        elif not self.invoice_action_report:
            res['invoice_action_report'] = self.default_invoice_action_report()
        return res

    def print_invoice(self):
        '''
        Generate invoice report and store it in invoice_report_cache field.
        '''
        if self.invoice_report_cache:
            return
        assert (self.invoice_action_report != None), (
            "Missing Invoice Report in invoice %s (%s)"
            % (self.rec_name, self.id))
        InvoiceReport = Pool().get(self.invoice_action_report.report_name,
            type='report')
        InvoiceReport.execute([self.id], {})


class PrintInvoice:
    __name__ = 'account.invoice.print'

    def do_print_(self, action):
        pool = Pool()
        Action = pool.get('ir.action')
        Invoice = pool.get('account.invoice')

        action, data = super(PrintInvoice, self).do_print_(action)
        invoice = Invoice(data['id'])
        if invoice.invoice_action_report:
            action_report = invoice.invoice_action_report
            action = Action.get_action_values(action_report.action.type,
                [action_report.action.id])[0]
        return action, data
