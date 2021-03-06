# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2014-2018 Didotech srl (<http://www.didotech.com>).
#
#                       All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    # def _get_sale_order(self, cr, uid, ids, field_name, model_name, context=None):
    #     result = {}
    #     crm_lead_obj = self.pool['crm.lead']
    #     sale_order_obj = self.pool['sale.order']
    #
    #     for crm_lead in crm_lead_obj.browse(cr, uid, ids, context):
    #         partner_id = crm_lead.partner_id.id
    #         contact_id = crm_lead.partner_address_id.id
    #         if contact_id:
    #             result[crm_lead.id] = sale_order_obj.search(cr, uid, [('partner_id', '=', partner_id), ('partner_order_id', '=', contact_id)])
    #         else:
    #             result[crm_lead.id] = sale_order_obj.search(cr, uid, [('partner_id', '=', partner_id)])
    #     return result

    def name_get(self, cr, uid, ids, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(x['id'], unicode(x.type in ['in_invoice', 'in_refund'] and x.supplier_invoice_number or x.number or x.name)) for x in self.browse(cr, uid, ids, context=context)]

    def _get_stock_picking(self, cr, uid, ids, field_name, model_name, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        result = {}
        stock_picking_obj = self.pool['stock.picking']

        for invoice in self.browse(cr, uid, ids, context):
            origins = {}

            for line in invoice.invoice_line:
                line_origin = line.origin or False
                if line_origin not in origins:
                    origins[line_origin] = invoice.id
            if invoice.origin:
                for invoice_origin in invoice.origin.split(', '):
                    if invoice_origin not in origins:
                        origins[invoice_origin] = invoice.id
            picking_ids = []
            for origin in origins:
                if origin:
                    # OUTxxx:SOyy
                    if len(origin.split(':')) == 2:
                        pickings_name = origin.split(':')[0]
                    else:
                        pickings_name = origin
                    picking_ids += stock_picking_obj.search(cr, uid, [('name', '=', pickings_name)], context=context)
                    print picking_ids

            result[invoice.id] = picking_ids

        return result

    _columns = {
        'supplier_invoice_number': fields.char('Supplier invoice nr', size=32),
        # 'sale_order_ids': fields.function(_get_sale_order, 'Sale Order', type='one2many', relation="sale.order", readonly=True, method=True),
        'stock_picking_ids': fields.function(_get_stock_picking, 'Stock Picking', type='one2many', relation="stock.picking", readonly=True, method=True),
    }
    
    def copy(self, cr, uid, order_id, default, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        if not default:
            default = {}
        default['user_id'] = uid
        return super(account_invoice, self).copy(cr, uid, order_id, default, context)

    def invoice_validate_check(self, cr, uid, ids, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.type == 'out_invoice' and invoice.fiscal_position and invoice.fiscal_position.sale_journal_id and invoice.fiscal_position.sale_journal_id != invoice.journal_id:
                raise orm.except_orm(_('Fattura Cliente'),
                    _('Impossibile to valide invoice of {partner} because journal on invoive \'{invoice_journal}\' is different from journal \'{fiscal_position_journal}\' set on fiscal position \'{invoice_fiscal_position}\'').format(
                        partner=invoice.partner_id.name, invoice_journal=invoice.journal_id.name, fiscal_position_journal=invoice.fiscal_position.sale_journal_id.name, invoice_fiscal_position=invoice.fiscal_position.name))
                return False
        return True

    def invoice_cancel_check(self, cr, uid, ids, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        return True

    def invoice_proforma_check(self, cr, uid, ids, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        return True

    def onchange_fiscal_position(self, cr, uid, ids, journal_id, fiscal_position, ttype, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        if not fiscal_position:
            return False

        fpos_obj = self.pool['account.fiscal.position']
        new_fiscal_position = fpos_obj.browse(cr, uid, fiscal_position, context)
        if ttype in ['out_invoice']:
            journal_id = new_fiscal_position.sale_journal_id and new_fiscal_position.sale_journal_id.id or journal_id
        elif ttype in ['in_invoice']:
            journal_id = new_fiscal_position.purchase_journal_id and new_fiscal_position.purchase_journal_id.id or journal_id

        # if is an exiting invoice, also change tax inside line to new fiscal position

        warning = {}
        for inv in self.browse(cr, uid, ids, context):
            if inv.fiscal_position != new_fiscal_position:
                for line in inv.invoice_line:
                    if line.product_id:
                        result = {}
                        if inv.type in ('out_invoice', 'out_refund'):
                            account_id = line.product_id.product_tmpl_id.property_account_income.id
                            if not account_id:
                                account_id = line.product_id.categ_id.property_account_income_categ.id
                        else:
                            account_id = line.product_id.product_tmpl_id.property_account_expense.id
                            if not account_id:
                                account_id = line.product_id.categ_id.property_account_expense_categ.id

                        account_id = fpos_obj.map_account(cr, uid, new_fiscal_position, account_id)

                        if inv.type in ('out_invoice', 'out_refund'):
                            taxes = line.product_id.taxes_id and line.product_id.taxes_id or (
                            account_id and self.pool['account.account'].browse(cr, uid, account_id, context=context).tax_ids or False)
                        else:
                            taxes = line.product_id.supplier_taxes_id and line.product_id.supplier_taxes_id or (
                            account_id and self.pool['account.account'].browse(cr, uid, account_id, context=context).tax_ids or False)

                        new_taxes = fpos_obj.map_tax(cr, uid, new_fiscal_position, taxes)
                        if new_taxes:
                            result['invoice_line_tax_id'] = [(6, 0, new_taxes)]
                        result['account_id'] = fpos_obj.map_account(cr, uid, new_fiscal_position, account_id, context=None)

                        self.pool['account.invoice.line'].write(cr, uid, line.id, result, context=context)
                inv.button_reset_taxes()
                warning = {
                    'title': _('Fiscal Position'),
                    'message': _('Is Change from \n{old_fiscal_position} to \n{new_fiscal_position}: \nPlease Press Button for recalculate tax').format(
                        old_fiscal_position=inv.fiscal_position and inv.fiscal_position.name or _('None'), new_fiscal_position=new_fiscal_position.name)
                }

        return {'value': {'journal_id': journal_id}, 'warning': warning}

    def _invoice_adaptative_function(self, invoice, vals):
        partner_vals = {}
        if set(vals.keys()).intersection(['fiscal_position', 'carriage_condition_id', 'goods_description_id', 'payment_term']):
            if not invoice.partner_id.carriage_condition_id and vals.get('carriage_condition_id', False):
                partner_vals['carriage_condition_id'] = vals.get('carriage_condition_id')
            if not invoice.partner_id.goods_description_id and vals.get('goods_description_id', False):
                partner_vals['goods_description_id'] = vals.get('goods_description_id')
            if not invoice.partner_id.property_payment_term and vals.get('payment_term', False):
                partner_vals['property_payment_term'] = vals.get('payment_term')
            if not invoice.partner_id.property_account_position and vals.get('fiscal_position', False):
                partner_vals['property_account_position'] = vals.get('fiscal_position')

            if partner_vals:
                invoice.partner_id.write(partner_vals)
        return True

    def create(self, cr, uid, vals, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        # adaptative function: the system learn
        invoice_id = super(account_invoice, self).create(cr, uid, vals, context=context)
        # create function return only 1 id
        invoice = self.browse(cr, uid, invoice_id, context)
        self._invoice_adaptative_function(invoice, vals)
        return invoice_id

    def write(self, cr, uid, ids, vals, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)

        for invoice in self.browse(cr, uid, ids, context=context):
            # adaptative function: the system learn
            self._invoice_adaptative_function(invoice, vals)
        return res

    # def button_change_fiscal_position(self, cr, uid, ids, context=None):
    #     if context is None:
    #         context = self.pool['res.users'].context_get(cr, uid)
    #
    #     fpos_obj = self.pool['account.fiscal.position']
    #
    #     for inv in self.browse(cr, uid, ids, context):
    #         for line in inv.invoice_line:
    #             if line.product_id:
    #                 new_taxes = fpos_obj.map_tax(cr, uid, inv.fiscal_position, line.product_id.taxes_id)
    #                 line.write({'invoice_line_tax_id': [(6, 0, new_taxes)]})
    #         inv.button_reset_taxes()
    #
    #     return True

    # override to group product_id too
    def inv_line_characteristic_hashcode(self, invoice, invoice_line):
        """Overridable hashcode generation for invoice lines. Lines having the same hashcode
        will be grouped together if the journal has the 'group line' option. Of course a module
        can add fields to invoice lines that would need to be tested too before merging lines
        or not."""
        return "%s-%s-%s-%s"%(
            invoice_line['account_id'],
            invoice_line.get('tax_code_id', "False"),  # invoice_line.get('product_id',"False"),
            invoice_line.get('analytic_account_id', "False"),
            invoice_line.get('date_maturity', "False"))

    # override to merge description (after will be trunked to x character everyway)
    def group_lines(self, cr, uid, iml, line, inv):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if inv.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(inv, l)

                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['tax_amount'] += l['tax_amount']
                    line2[tmp]['analytic_lines'] += l['analytic_lines']
                    line2[tmp]['amount_currency'] += l['amount_currency']
                    line2[tmp]['quantity'] += l['quantity']
                    line2[tmp]['name'] += l['name']
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0, 0, val))
        return line

    def unlink(self, cr, uid, ids, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        # account_invoice_line_obj = self.pool['account.invoice.line']
        stock_picking_obj = self.pool['stock.picking']
        origins = {}
        for invoice in self.browse(cr, uid, ids, context):
            for line in invoice.invoice_line:
                if line.origin_document and line.origin_document._name == 'sale.order.line':
                    # the invoice line is create directly form sale order.line
                    if self.pool['account.invoice.line'].unlink(cr, uid, line.id, context):
                        continue

                line_origin = line.origin or False
                if line_origin not in origins:
                    origins[line_origin] = invoice.id

            if invoice.origin:
                for invoice_origin in invoice.origin.split(', '):
                    if invoice_origin not in origins:
                        origins[invoice_origin] = invoice.id

        # now on origins i have all the origin and invoice.id
        for origin in origins:
            if origin:
                # OUTxxx:SOyy
                if len(origin.split(':')) == 2:
                    pickings_name = origin.split(':')[0]
                else:
                    pickings_name = origin
                picking_id = stock_picking_obj.search(cr, uid, [('name', '=', pickings_name)], context=context)
                if super(account_invoice, self).unlink(cr, uid, [origins[origin]], context=context):
                    if picking_id:
                        stock_picking_obj.write(cr, uid, [picking_id[0]], {'invoice_state': '2binvoiced'}, context=context)
                # now i need to eliminate other ids
                if origins[origin] in ids:
                    del ids[ids.index(origins[origin])]

        return super(account_invoice, self).unlink(cr, uid, ids, context=context)


