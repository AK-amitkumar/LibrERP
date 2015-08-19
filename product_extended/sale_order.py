# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2011 - 2012 Avanzosc <http://www.avanzosc.com>
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm, fields


class sale_order(orm.Model):
    _inherit = "sale.order"

    def action_wait(self, cr, uid, ids, *args):

        res = super(sale_order, self).action_wait(cr, uid, ids, *args)
        for o in self.browse(cr, uid, ids):
            for line in o.order_line:
                if line.product_id:
                    vals = {
                        'last_sale_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'last_customer_id': line.order_partner_id.id
                    }
                    self.pool['product.product'].write(cr, uid, [line.product_id.id], vals)
        return res

