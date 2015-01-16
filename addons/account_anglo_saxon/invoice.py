##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 
#    2004-2010 Tiny SPRL (<http://tiny.be>). 
#    2009-2010 Veritos (http://veritos.nl).
#    All Rights Reserved
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

from openerp.osv import osv, orm
from openerp.tools.float_utils import float_round as round

from openerp import pooler


def get_account(cr, uid, product, account, fpos=False):
    """Helper function to return the correct account"""
    db_pool = pooler.get_pool(cr.dbname)
    fiscal_pool = db_pool.get('account.fiscal.position')
    res = eval('product.%s and product.%s.id' % (account, account))
    if not res:
        res = eval('product.categ_id.%s_categ and product.categ_id.%s_categ.id' %
                   (account, account))
    if fpos:
        res = fiscal_pool.map_account(cr, uid, fpos, res)
    return res


class AccountInvoiceLine(osv.osv):
    _inherit = "account.invoice.line"

    def _get_price(self, cr, uid, inv, i_line, context=None):
        if context is None:
            context = {}

        decimal_precision = self.pool['decimal.precision']
        ctx2 = context.copy()
        ctx2.update({'currency_id': inv.currency_id.id})
        prod_obj = self.pool['product.product']
        uom_obj = self.pool['product.uom']
        product = i_line.product_id
        move_ids = False

        if product.cost_method == 'average' and i_line.invoice_id.picking_ids:
            move_obj = self.pool['stock.move']
            picking_ids = [x.id for x in i_line.invoice_id.picking_ids]
            move_ids = move_obj.search(cr, uid,
                                       [('picking_id', 'in', picking_ids),
                                        ('product_id', '=', product.id)])
            if not move_ids:
                #If this is being triggered then we have probably changed/added
                #to the invoice. Nothing good can happen, but best alternative,
                #at least it is the current average cost.
                price = prod_obj.price_get(cr, uid, [product.id],
                                           ptype='standard_price',
                                           context=ctx2)[product.id]
            elif len(move_ids) != 1:
                #most of the time we will only have one, but attempt to narrow the search
                #if more than 1
                move_ids_filtered = move_obj.search(
                    cr, uid, [('id', 'in', move_ids),
                               '|', ('product_uos_qty', '=', i_line.quantity),
                              ('product_qty', '=', i_line.quantity)])
                if move_ids_filtered:
                    move_ids = move_ids_filtered
            if move_ids:
                #for now we take the average, overall entries will be correct but in case of
                #multiple matches will be averaged over multiple lines in journal entry
                #rest of this block is just an average cost calculation.
                total = 0.0
                total_qty = 0.0
                for stock_move in move_obj.browse(cr, uid, move_ids):
                    if stock_move.price_unit:
                        total += stock_move.price_unit * stock_move.product_qty
                    else:
                        total += (stock_move.product_id.standard_price *
                                  stock_move.product_qty) #probably need to convert uoms here
                    total_qty += stock_move.product_qty
                price = total / total_qty

        elif product.cost_method == 'standard':
            #note this doesn't allow for cost changes between dispatch and invoice
            price = prod_obj.price_get(cr, uid, [product.id],
                                       ptype='standard_price',
                                       context=ctx2)[product.id]
        else:
            #TODO: there should be no else, should refactor this out to a new method for future
            #extensibility of new cost methods, for now just get standard cost
            price = prod_obj.price_get(cr, uid, [product.id],
                                       ptype='standard_price',
                                       context=ctx2)[product.id]
        if not move_ids: # only convert if not using the already converted move values
            uom = product.uos_id or product.uom_id
            price = self.pool['product.uom']._compute_price(
                cr, uid, uom.id, price, i_line.uos_id.id)
        return price

    def _prepare_anglosaxon_in_moves(self, cr, uid, res, inv, i_line, context=None):

        diff_res = []
        if context is None:
            context = {}

        if i_line.invoice_id.picking_ids:
            if i_line.product_id.type != 'service':
                fpos = i_line.invoice_id.fiscal_position or False
                pd_acc = get_account(cr, uid, i_line.product_id,
                                     'property_account_creditor_price_difference', fpos)

                account = 'property_stock_account_input'
                contra_acc = get_account(cr, uid, i_line.product_id, account, fpos)
                for index, line in enumerate(res): #better to create a map here - even better with link between move and i_line
                    if (index not in context['seen'] and contra_acc == line['account_id'] and
                            i_line.product_id.id == line['product_id'] and
                            i_line.quantity == line['quantity']):
                        context['seen'].append(index)
                        #this could be optimised to break after matching - simpler, now it just returns
                        pd_line = self._prepare_anglosaxon_price_diff(cr, uid, i_line, line, pd_acc, context=context)
                        if pd_line:
                            diff_res.append(pd_line)
                            return diff_res
        return diff_res

    def _prepare_anglosaxon_price_diff(self, cr, uid, i_line, line, pd_acc, context=None):

        diff_res = False
        price = self._get_price(cr, uid, i_line.invoice_id, i_line, context)
        price_diff = (i_line.price_unit * ((100 - i_line.discount)/100)) - price
        decimal_precision = self.pool.get('decimal.precision')
        account_prec = decimal_precision.precision_get(cr, uid, 'Account')
        if pd_acc and price_diff:
            #price difference entry
            line.update({'price': round(price * line['quantity'], account_prec),
                         'price_unit': price})
            diff_res = {'type': 'src',
                        'name': i_line.name[:64],
                        'price_unit': price_diff,
                        'price': round(price_diff * line['quantity'], account_prec),
                        'quantity': line['quantity'],
                        'account_id': pd_acc,
                        'product_id': line['product_id'],
                        'uos_id': line['uos_id'],
                        'account_analytic_id': line['account_analytic_id'],
                        'taxes': line.get('taxes', []),
                        }
        return diff_res

    def _prepare_anglosaxon_out_moves(self, cr, uid, inv, i_line,
                                      company_currency, context=None):
        res = []
        if inv.picking_ids:
            decimal_precision = self.pool.get('decimal.precision')
            account_prec = decimal_precision.precision_get(cr, uid, 'Account')
            account = 'property_stock_account_output'
            fpos = i_line.invoice_id.fiscal_position
            dr_acc = get_account(cr, uid, i_line.product_id, account, fpos)
            cogs_acc = get_account(
                cr, uid, i_line.product_id, 'property_account_expense', fpos)

            if dr_acc and cogs_acc:
                ctx2 = context.copy()
                if inv.currency_id.id != company_currency:
                    ctx2.update({'currency_id': inv.currency_id.id})
                price = self._get_price(cr, uid, inv, i_line, context=context)
                #This is our stock contra entry.
                line = {'type': 'src',
                        'name': i_line.name[:64],
                        'quantity': i_line.quantity,
                        'product_id': i_line.product_id.id,
                        'uos_id': i_line.uos_id.id,
                        'account_analytic_id': False,
                        'taxes': i_line.invoice_line_tax_id,
                        'price_unit': price,
                        'price': round(price * i_line.quantity, account_prec),
                        'account_id': dr_acc,}

                res.append(line.copy())
                #This is our COGS entry
                line.update({'price_unit': -price,
                             'price': -price * i_line.quantity,
                             'account_id': cogs_acc, })
                res.append(line.copy())
            return res

    def move_line_get(self, cr, uid, invoice_id, context=None):
        """
        Method appends stock contra and cogs entries to invoice journal
        moves out
        and price difference entries to moves in.  See _prepare methods for
        actual
        implementation
        """
        res = super(AccountInvoiceLine, self).move_line_get(
            cr, uid, invoice_id, context=context)
        inv = self.pool['account.invoice'].browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id

        if inv.type in ('out_invoice', 'out_refund'):
            for i_line in inv.invoice_line:
                if i_line.product_id:
                    out_moves = self._prepare_anglosaxon_out_moves(
                        cr, uid, inv, i_line, company_currency, context=context)
                    if out_moves:
                        res.extend(out_moves)

        elif inv.type in ('in_invoice', 'in_refund'):
            if context is None:
                context = {}
            context.update({'seen': []})
            for i_line in inv.invoice_line:
                if i_line.product_id:
                    in_moves = self._prepare_anglosaxon_in_moves(
                        cr, uid, res, inv, i_line, context=context)
                    if in_moves:
                        res.extend(in_moves)
        return res

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='',
                          type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          currency_id=False, context=None, company_id=None):

        res = super(AccountInvoiceLine, self).product_id_change(
            cr, uid, ids, product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, context, company_id)

        if not product:
            return res

        if type in ('in_invoice', 'in_refund'):
            product_obj = self.pool['product.product'].browse(
                cr, uid, product, context=context)
            account = 'property_stock_account_input'
            contra_acc = get_account(cr, uid, product_obj, account)
            if contra_acc:
                res['value'].update({'account_id': contra_acc})
        return res


class AccountInvoice(orm.Model):
    _inherit = "account.invoice"

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None,
                        description=None, journal_id=None, context=None):
        invoice_data = super(AccountInvoice, self)._prepare_refund(
            cr, uid, invoice, date, period_id, description,
            journal_id, context=context)

        if invoice.type == 'in_invoice':
            for _, _, line_dict in invoice_data['invoice_line']:
                if line_dict.get('product_id'):
                    product = self.pool['product.product'].browse(
                        cr, uid, line_dict['product_id'], context=context)
                    fpos = invoice.fiscal_position or False
                    contra_acc = get_account(
                        cr, uid, product, 'property_stock_account_output', fpos)
                    if contra_acc:
                        line_dict['account_id'] = contra_acc
        return invoice_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
