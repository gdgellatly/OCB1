# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm
from .invoice import get_account


class StockPicking(orm.Model):
    _inherit = "stock.picking"

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        """Return ids of created invoices for the pickings"""
        res = super(StockPicking, self).action_invoice_create(
            cr, uid, ids, journal_id, group, type, context=context)

        if type in ['in_refund', 'in_invoice']:
            for inv in self.pool['account.invoice'].browse(
                    cr, uid, res.values(), context=context):
                for ol in inv.invoice_line:
                    if ol.product_id:
                        fpos = ol.invoice_id.fiscal_position or False
                        account = 'property_stock_account_%s' % ((inv.type == 'in_invoice') and 'input' or 'output')
                        contra_acc = get_account(cr, uid, ol.product_id, account, fpos)
                        if contra_acc:
                            ol.write({'account_id': contra_acc})
        return res
