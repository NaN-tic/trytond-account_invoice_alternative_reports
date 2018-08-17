# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.modules.company.model import CompanyValueMixin

__all_ = ['AccountConfiguration', 'AccountConfigurationCompany']


class AccountConfiguration(metaclass=PoolMeta):
    __name__ = 'account.configuration'

    invoice_action_report = fields.MultiValue(fields.Many2One(
            'ir.action.report', 'Report Template',
            help='Default report used when creat new invoice'))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'invoice_action_report':
            return pool.get('account.configuration.company')
        return super(AccountConfiguration, cls).multivalue_model(field)


class AccountConfigurationCompany(ModelSQL, CompanyValueMixin):
    'Account Configuration per Company'
    __name__ = 'account.configuration.company'

    invoice_action_report = fields.Many2One(
        'ir.action.report', 'Report Template')
