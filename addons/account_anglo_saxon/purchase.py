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


class PurchaseOrder(orm.Model):
    _inherit = "purchase.order"

    def _choose_account_from_po_line(self, cr, uid, order_line, context=None):
        account_id = super(PurchaseOrder, self)._choose_account_from_po_line(
            cr, uid, order_line, context=context)
        if order_line.product_id and not order_line.product_id.type == 'service':
            fpos = order_line.order_id.fiscal_position or False
            account_id = get_account(
                cr, uid, order_line.product_id,
                'property_stock_account_input', fpos)
        return account_id

