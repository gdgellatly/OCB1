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

from openerp.osv import fields, orm
from .invoice import get_account


class ProductCategory(orm.Model):
    _inherit = "product.category"
    _columns = {
        'property_account_creditor_price_difference_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Price Difference Account",
            view_load=True,
            help="This account will be used to value price difference between purchase price and cost price."),

        #Redefine fields to change help text for anglo saxon methodology.            
        'property_account_income_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            help="This account will be used to value outgoing stock using sale price."),
        'property_account_expense_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Expense Account",
            view_load=True,
            help="This account will be used to value outgoing stock using cost price."),

    }


class ProductTemplate(orm.Model):
    _inherit = "product.template"
    _columns = {
        'property_account_creditor_price_difference': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Price Difference Account",
            view_load=True,
            help="This account will be used to value price difference between purchase price and cost price."),
            
        #Redefine fields to change help text for anglo saxon methodology.
        'property_account_income': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Income Account",
            view_load=True,
            help="This account will be used to value outgoing stock using sale price."),
        'property_account_expense': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Expense Account",
            view_load=True,
            help="This account will be used to value outgoing stock using cost price."),

    }


class ChangeStandardPrice(orm.TransientModel):
    _inherit = "stock.change.standard.price"

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.

         For anglo saxon this must be a P & L account.  That leaves a choice
         between COGS or Price Difference without creating a new field.
         Price Difference is selected as that
         is where invoice variances would have ended up.
        """
        res = super(ChangeStandardPrice, self).default_get(
            cr, uid, fields, context=context)
        if context is None:
            context = {}
        product_pool = self.pool['product.product']
        product = product_pool.browse(cr, uid, context['active_id'])
        account = get_account(cr, uid, product,
                              'property_account_creditor_price_difference')
        if 'stock_account_input' in fields:
            res.update({'stock_account_input': account})
        if 'stock_account_output' in fields:
            res.update({'stock_account_output': account})

        return res
