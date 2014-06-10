# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Didotech SRL
#    (<http://www.didotech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Italian Localisation - Account Didotech',
    'version': '2.0.1.0',
    'category': 'Localisation/Italy',
    'description': """This module customizes OpenERP in order to add more payment functionalities.
""",
    'author': 'OpenERP Italian Community',
    'website': 'http://www.openerp-italia.org',
    'license': 'AGPL-3',
    "depends": [
        'account',
        'base_vat',
        'account_chart',
        'base_iban',
        'l10n_it_base',
        'account_voucher',
    ],
    "init_xml": [
    ],
    "update_xml": [
    ],
    "demo_xml": [],
    "active": False,
    "installable": True
}
