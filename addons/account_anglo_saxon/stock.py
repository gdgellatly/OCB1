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
            cr, uid, ids, journal_id=journal_id, group=group, type=type,
            context=context)

        if type in ['in_refund', 'in_invoice']:
            for inv in self.pool['account.invoice'].browse(
                    cr, uid, res.values(), context=context):
                for inv_line in inv.invoice_line:
                    if inv_line.product_id:
                        fpos = inv_line.invoice_id.fiscal_position or False
                        account = 'property_stock_account_%s' % (
                            (inv.type in ('in_invoice', 'in_refund')) and
                            'input' or 'output')
                        contra_acc = get_account(cr, uid, inv_line.product_id,
                                                 account, fpos)
                        if contra_acc:
                            inv_line.write({'account_id': contra_acc})
        return res


class StockPickingIn(orm.Model):
    _inherit = 'stock.picking.in'

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='in_invoice', context=None):
        picking_obj = self.pool['stock.picking']
        return picking_obj.action_invoice_create(
            cr, uid, ids, journal_id=journal_id, group=group, type=type,
            context=context)

class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice',
                              context=None):
        picking_obj = self.pool['stock.picking']
        return picking_obj.action_invoice_create(cr, uid, ids,
            journal_id=journal_id, group=group, type=type, context=context)


class StockMove(orm.Model):
    _inherit = 'stock.move'

    def _get_reference_accounting_values_for_valuation(self, cr, uid, move,
                                                       context=None):
        """
        Return the reference amount and reference currency representing
        the inventory valuation for this move.
        These reference values should possibly be converted
        before being posted in Journals to adapt to the primary
        and secondary currencies of the relevant accounts.

        THis function then updates the move's price unit to record
        the amount that was used
        so that invoices use the correct value
        """
        reference_amount, reference_currency_id = super(
            StockMove, self)._get_reference_accounting_values_for_valuation(
            cr, uid, move, context=context)
        if reference_amount != move.price_unit:
            product_uom_obj = self.pool.get('product.uom')
            default_uom = move.product_id.uom_id.id
            qty = product_uom_obj._compute_qty(
                cr, uid, move.product_uom.id, move.product_qty, default_uom)

            move.write({'price_unit': reference_amount/qty})
        return reference_amount, reference_currency_id
